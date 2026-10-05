#!/usr/bin/env python3
"""
receipt_intake.py — 영수증 파일 정규화 · 추출 결과 검증 · 원장 대사(reconcile)

이 스크립트는 OCR을 하지 않는다. OCR은 Claude가 이미지를 직접 보고 수행한다.
스크립트가 맡는 일은 결정론적으로 처리해야 정확한 세 가지다.

  1) prepare   — 어떤 형식으로 들어오든 Claude가 읽을 수 있는 이미지로 정규화
  2) validate  — Claude가 뽑아낸 레코드의 형식·범위·중복을 기계적으로 점검
  3) reconcile — 기존 원장과 대사해 예상→실제 전환과 분류별 차이를 계산

사용법
  python3 receipt_intake.py prepare   --inputs a.jpg b.pdf --out /tmp/trip/receipts
  python3 receipt_intake.py validate  --records records.json --brief trip-brief.json [--ledger ledger.json]
  python3 receipt_intake.py reconcile --records records.json --ledger ledger.json [--out report.json]

records.json 형식 (Claude가 채운다)
  [{"source_file": "...", "merchant": "...", "date": "2026-08-14",
    "currency": "USD", "amount": 41.83, "tax": 2.61,
    "category": "식비", "payment_last4": "1234",
    "line_items": ["..."], "confidence": "high", "notes": ""}]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime

# 지출 DB의 표준 분류. travel-expense-db 스킬의 스키마와 일치해야 한다.
CATEGORIES = {
    "항공", "RV", "렌터카", "숙박", "식비",
    "입장료", "장비·용품", "연료", "기타",
}

# ISO 4217 중 여행에서 실제로 마주치는 것들. 그 외는 경고만 내고 통과시킨다.
COMMON_CURRENCIES = {
    "USD", "KRW", "EUR", "JPY", "CAD", "GBP", "AUD",
    "CHF", "CNY", "TWD", "THB", "SGD", "HKD", "MXN", "NZD",
}

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
HEIC_EXT = {".heic", ".heif"}
PDF_EXT = {".pdf"}

# Claude가 이미지를 읽을 때 실용적인 상한. 이보다 크면 축소한다.
MAX_EDGE = 2200
# 이보다 작으면 글자가 뭉개져 OCR 정확도가 급격히 떨어진다.
MIN_EDGE_WARN = 900


# ──────────────────────────────────────────────────────────────
# prepare
# ──────────────────────────────────────────────────────────────

def _have(cmd):
    return shutil.which(cmd) is not None


def _load_pil():
    try:
        from PIL import Image, ImageOps  # noqa: F401
        return True
    except ImportError:
        return False


def _register_heif():
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        return True
    except ImportError:
        return False


def _normalize_image(src, dst_dir, stem):
    """EXIF 회전을 적용하고 긴 변을 MAX_EDGE로 맞춰 JPEG로 저장."""
    from PIL import Image, ImageOps

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)   # 세로로 찍은 영수증이 눕는 사고 방지
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        long_edge = max(w, h)
        scaled = False
        if long_edge > MAX_EDGE:
            ratio = MAX_EDGE / long_edge
            im = im.resize((max(1, int(w * ratio)), max(1, int(h * ratio))),
                           Image.LANCZOS)
            scaled = True
        out = os.path.join(dst_dir, f"{stem}.jpg")
        im.save(out, "JPEG", quality=88, optimize=True)
        return out, im.size, scaled, (w, h)


def _pdf_to_images(src, dst_dir, stem):
    """PDF를 페이지별 PNG로 변환. poppler의 pdftoppm을 쓴다."""
    if not _have("pdftoppm"):
        raise RuntimeError(
            "PDF 변환에 pdftoppm이 필요합니다. "
            "`apt-get install -y poppler-utils` 후 다시 실행하세요."
        )
    prefix = os.path.join(dst_dir, stem)
    subprocess.run(
        ["pdftoppm", "-r", "170", "-png", src, prefix],
        check=True, capture_output=True,
    )
    pages = sorted(
        p for p in os.listdir(dst_dir)
        if p.startswith(os.path.basename(prefix) + "-") and p.endswith(".png")
    )
    return [os.path.join(dst_dir, p) for p in pages]


def cmd_prepare(args):
    os.makedirs(args.out, exist_ok=True)
    have_pil = _load_pil()
    heif_ok = _register_heif() if have_pil else False

    manifest, warnings = [], []

    for idx, src in enumerate(args.inputs, 1):
        if not os.path.exists(src):
            warnings.append(f"파일 없음: {src}")
            continue

        ext = os.path.splitext(src)[1].lower()
        stem = f"r{idx:03d}_" + re.sub(r"[^0-9A-Za-z._-]", "_",
                                       os.path.splitext(os.path.basename(src))[0])[:40]

        try:
            if ext in PDF_EXT:
                pages = _pdf_to_images(src, args.out, stem)
                for pno, page in enumerate(pages, 1):
                    manifest.append({
                        "source_file": src,
                        "prepared": page,
                        "page": pno,
                        "kind": "pdf-page",
                    })
                if not pages:
                    warnings.append(f"PDF에서 페이지를 얻지 못함: {src}")

            elif ext in HEIC_EXT:
                if not heif_ok:
                    warnings.append(
                        f"HEIC를 열 수 없습니다: {src} — "
                        "`pip install pillow-heif --break-system-packages` 후 재실행"
                    )
                    continue
                out, size, scaled, orig = _normalize_image(src, args.out, stem)
                manifest.append({"source_file": src, "prepared": out,
                                 "kind": "image", "size": list(size),
                                 "original_size": list(orig), "downscaled": scaled})

            elif ext in IMAGE_EXT:
                if not have_pil:
                    # PIL이 없으면 그대로 복사한다. 회전·축소는 못 하지만 읽기는 된다.
                    out = os.path.join(args.out, stem + ext)
                    shutil.copy2(src, out)
                    manifest.append({"source_file": src, "prepared": out,
                                     "kind": "image", "note": "PIL 없음 — 원본 그대로"})
                    warnings.append("Pillow가 없어 EXIF 회전·리사이즈를 건너뛰었습니다.")
                    continue
                out, size, scaled, orig = _normalize_image(src, args.out, stem)
                entry = {"source_file": src, "prepared": out, "kind": "image",
                         "size": list(size), "original_size": list(orig),
                         "downscaled": scaled}
                if min(size) < MIN_EDGE_WARN:
                    entry["low_resolution"] = True
                    warnings.append(
                        f"해상도가 낮습니다({size[0]}x{size[1]}): {os.path.basename(src)} "
                        "— 금액을 잘못 읽을 수 있으니 추출 결과를 사용자에게 확인받으세요."
                    )
                manifest.append(entry)

            else:
                warnings.append(f"지원하지 않는 형식({ext}): {src}")

        except Exception as e:  # noqa: BLE001
            warnings.append(f"처리 실패 {src}: {e}")

    path = os.path.join(args.out, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"count": len(manifest), "items": manifest,
                   "warnings": warnings}, f, ensure_ascii=False, indent=2)

    print(f"준비 완료: {len(manifest)}건 → {path}")
    for w in warnings:
        print("  ⚠️  " + w)
    return 0 if manifest else 1


# ──────────────────────────────────────────────────────────────
# validate
# ──────────────────────────────────────────────────────────────

def _parse_date(s):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _norm_merchant(s):
    return re.sub(r"[^a-z0-9가-힣]", "", str(s or "").lower())


def cmd_validate(args):
    with open(args.records, encoding="utf-8") as f:
        records = json.load(f)
    if isinstance(records, dict):
        records = records.get("records", [])

    trip_start = trip_end = None
    if args.brief and os.path.exists(args.brief):
        with open(args.brief, encoding="utf-8") as f:
            brief = json.load(f)
        trip_start = _parse_date(brief.get("start_date") or
                                 (brief.get("dates") or {}).get("start"))
        trip_end = _parse_date(brief.get("end_date") or
                               (brief.get("dates") or {}).get("end"))

    ledger = []
    if args.ledger and os.path.exists(args.ledger):
        with open(args.ledger, encoding="utf-8") as f:
            ledger = json.load(f)
        if isinstance(ledger, dict):
            ledger = ledger.get("results", ledger.get("rows", []))

    errors, warnings, seen = [], [], {}

    for i, r in enumerate(records):
        tag = f"[{i}] {r.get('source_file') or r.get('merchant') or '?'}"

        # 필수 필드
        for field in ("merchant", "date", "currency", "amount", "category"):
            if r.get(field) in (None, "", []):
                errors.append(f"{tag}: 필수 항목 누락 — {field}")

        # 금액
        amt = r.get("amount")
        if amt is not None:
            if not isinstance(amt, (int, float)):
                errors.append(f"{tag}: amount가 숫자가 아닙니다 — {amt!r}")
            elif amt <= 0:
                errors.append(f"{tag}: amount가 0 이하입니다 — {amt}")
            elif amt > 20000:
                warnings.append(f"{tag}: 금액이 비정상적으로 큽니다({amt}). "
                                "소수점이나 통화를 잘못 읽었을 수 있습니다.")

        tax = r.get("tax")
        if isinstance(tax, (int, float)) and isinstance(amt, (int, float)):
            if tax > amt:
                errors.append(f"{tag}: 세액({tax})이 총액({amt})보다 큽니다.")

        # 통화
        cur = str(r.get("currency") or "").upper()
        if cur and not re.fullmatch(r"[A-Z]{3}", cur):
            errors.append(f"{tag}: 통화 코드 형식이 아닙니다 — {cur!r}")
        elif cur and cur not in COMMON_CURRENCIES:
            warnings.append(f"{tag}: 흔치 않은 통화({cur}). 맞는지 확인하세요.")

        # 분류
        cat = r.get("category")
        if cat and cat not in CATEGORIES:
            errors.append(f"{tag}: 알 수 없는 분류 — {cat!r} "
                          f"(허용: {', '.join(sorted(CATEGORIES))})")

        # 날짜
        d = _parse_date(r.get("date"))
        if r.get("date") and not d:
            errors.append(f"{tag}: 날짜를 해석할 수 없습니다 — {r.get('date')!r}")
        elif d:
            in_trip = bool(trip_start and trip_end and trip_start <= d <= trip_end)
            if trip_start and trip_end and not in_trip:
                warnings.append(f"{tag}: 여행 기간({trip_start}–{trip_end}) "
                                f"밖의 날짜입니다 — {d}")
            # 여행 기간 안이면 미래여도 정상이다(출발 전 선결제 영수증).
            # 기간 정보가 없을 때만 미래 날짜를 의심한다.
            elif not (trip_start and trip_end) and d > date.today():
                warnings.append(f"{tag}: 날짜가 미래입니다({d}). "
                                "월/일 순서를 뒤집어 읽었을 수 있습니다.")

        # 확신도
        if str(r.get("confidence", "")).lower() in ("low", "낮음"):
            warnings.append(f"{tag}: 확신도 낮음 — 등록 전 사용자 확인 필요")

        # 입력 파일 내 중복
        key = (_norm_merchant(r.get("merchant")), str(d), amt)
        if key in seen and all(k not in (None, "None", "") for k in key):
            errors.append(f"{tag}: 같은 배치의 [{seen[key]}]와 중복입니다.")
        else:
            seen[key] = i

        # 기존 원장과 중복
        for row in ledger:
            props = row.get("properties", row)
            l_merchant = _norm_merchant(props.get("가맹점"))
            l_amount = props.get("금액(USD)") or props.get("amount")
            l_date = _parse_date(props.get("결제일"))
            if (l_merchant and l_merchant == _norm_merchant(r.get("merchant"))
                    and l_amount == amt and l_date == d):
                errors.append(
                    f"{tag}: 원장에 이미 있습니다 — "
                    f"{props.get('항목') or props.get('title')}"
                )
                break

    print(f"검증 대상 {len(records)}건 · 오류 {len(errors)} · 경고 {len(warnings)}")
    for e in errors:
        print("  ❌ " + e)
    for w in warnings:
        print("  ⚠️  " + w)
    if not errors:
        print("\n오류 없음 — 등록을 진행해도 됩니다.")
        if warnings:
            print("경고 항목은 사용자에게 먼저 확인받으세요.")
    return 1 if errors else 0


# ──────────────────────────────────────────────────────────────
# reconcile
# ──────────────────────────────────────────────────────────────

def cmd_reconcile(args):
    with open(args.records, encoding="utf-8") as f:
        records = json.load(f)
    if isinstance(records, dict):
        records = records.get("records", [])
    with open(args.ledger, encoding="utf-8") as f:
        ledger = json.load(f)
    if isinstance(ledger, dict):
        ledger = ledger.get("results", ledger.get("rows", []))

    actual = defaultdict(float)
    for r in records:
        if isinstance(r.get("amount"), (int, float)):
            actual[r.get("category") or "기타"] += float(r["amount"])

    est, confirmed = defaultdict(float), defaultdict(float)
    est_rows = defaultdict(list)
    for row in ledger:
        p = row.get("properties", row)
        cat = p.get("분류") or "기타"
        amt = p.get("금액(USD)")
        status = p.get("상태") or ""
        if not isinstance(amt, (int, float)):
            continue
        if status == "환불예정":
            continue
        if status == "예상":
            est[cat] += amt
            est_rows[cat].append(p.get("항목") or p.get("title") or "?")
        else:
            confirmed[cat] += amt

    cats = sorted(set(actual) | set(est) | set(confirmed))
    lines, total_actual, total_est = [], 0.0, 0.0

    print(f"{'분류':<12}{'이번 등록':>12}{'기존 예상':>12}{'차이':>12}")
    print("-" * 48)
    for c in cats:
        a, e = actual.get(c, 0.0), est.get(c, 0.0)
        total_actual += a
        total_est += e
        diff = a - e
        if a or e:
            print(f"{c:<12}{a:>12,.2f}{e:>12,.2f}{diff:>+12,.2f}")
        lines.append({"category": c, "receipts_total": round(a, 2),
                      "estimate_total": round(e, 2),
                      "confirmed_total": round(confirmed.get(c, 0.0), 2),
                      "difference": round(diff, 2),
                      "estimate_rows": est_rows.get(c, [])})
    print("-" * 48)
    print(f"{'합계':<12}{total_actual:>12,.2f}{total_est:>12,.2f}"
          f"{total_actual - total_est:>+12,.2f}")

    over = [l for l in lines if l["difference"] > 0 and l["estimate_total"] > 0]
    if over:
        print("\n예산을 넘긴 분류:")
        for l in over:
            pct = l["difference"] / l["estimate_total"] * 100
            print(f"  · {l['category']}: +{l['difference']:,.2f} ({pct:+.0f}%)")
            if l["estimate_rows"]:
                print(f"    ↳ 갱신 후보(예상 상태 행): {', '.join(l['estimate_rows'][:4])}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"by_category": lines,
                       "receipts_total": round(total_actual, 2),
                       "estimate_total": round(total_est, 2)},
                      f, ensure_ascii=False, indent=2)
        print(f"\n리포트 저장: {args.out}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="영수증 파일을 읽기 좋은 이미지로 정규화")
    p.add_argument("--inputs", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_prepare)

    v = sub.add_parser("validate", help="추출 레코드의 형식·범위·중복 점검")
    v.add_argument("--records", required=True)
    v.add_argument("--brief", help="trip-brief.json (여행 기간 대조용)")
    v.add_argument("--ledger", help="기존 DB 행 JSON (중복 판정용)")
    v.set_defaults(func=cmd_validate)

    r = sub.add_parser("reconcile", help="기존 원장과 대사해 분류별 차이 계산")
    r.add_argument("--records", required=True)
    r.add_argument("--ledger", required=True)
    r.add_argument("--out")
    r.set_defaults(func=cmd_reconcile)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

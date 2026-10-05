#!/usr/bin/env python3
"""
build_map_assets.py — 여행 스팟 목록에서 지도 자산 일괄 생성

입력  : spots.json  (travel-maps-integration SKILL.md의 스팟 스키마 배열)
        routes.json (선택 — 날짜별 경로 정의)
출력  : {out}/trip.kml           Google My Maps 임포트용 (Day별 폴더)
        {out}/trip_spots.csv     UTF-8 BOM, Excel 호환
        {out}/trip_routes.md     날짜별 구글맵 경로 URL
        {out}/notion_day_maps.md 날짜별 노션 삽입용 마크다운
        {out}/image_urls.txt     (있으면) 이미지 URL 검증 목록

사용  : python3 build_map_assets.py --spots spots.json --out assets/ \
                 [--routes routes.json] [--box 43.0,46.0,-112.0,-101.0]

의존성 없음 (표준 라이브러리만).
"""

import argparse
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

# ── 카테고리 → (KML 아이콘, ABGR 색상, 노션 이모지) ──────────────────────────
CATEGORY = {
    "공항":     ("airports",        "ffff9900", "✈️"),
    "차량":     ("cabs",            "ff999999", "🚐"),
    "관문":     ("ranger_station",  "ff336699", "🚪"),
    "숙박":     ("campground",      "ff33aa33", "🏕️"),
    "관광":     ("camera",          "ff0000ff", "📸"),
    "야생동물": ("horsebackriding", "ff0099ff", "🦬"),
    "식당":     ("dining",          "ff33ccff", "🍽️"),
    "쇼핑":     ("shopping",        "ffcc33cc", "🛒"),
    "편의":     ("gas_stations",    "ffcccc33", "⛽"),
    "경유":     ("placemark_circle","ffffffff", "📍"),
}
DEFAULT_CAT = ("placemark_circle", "ffffffff", "📍")

MAPS_SEARCH = "https://www.google.com/maps/search/?api=1&query={lat},{lon}"
MAPS_DIR = ("https://www.google.com/maps/dir/?api=1"
            "&origin={o}&destination={d}{wp}&travelmode=driving")
MAPS_EMBED = "https://maps.google.com/maps?saddr={o}&daddr={chain}&output=embed"

MAX_WAYPOINTS = 9


# ── 유틸 ────────────────────────────────────────────────────────────────────
def notion_escape(text):
    """노션 마크다운에서 특수 해석되는 문자를 이스케이프."""
    return str(text).replace("~", "\\~").replace("$", "\\$")


def coord(spot):
    return "{:.4f},{:.4f}".format(spot["lat"], spot["lon"])


def validate(spots, box):
    """좌표 바운딩 박스 검증. 부호 누락·자릿수 오타를 잡는다."""
    problems = []
    seen = {}
    for s in spots:
        lat, lon = s.get("lat"), s.get("lon")
        if lat is None or lon is None:
            problems.append((s.get("id", s.get("name_ko", "?")), "좌표 없음"))
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            problems.append((s["id"], "좌표 범위 초과 {},{}".format(lat, lon)))
            continue
        if box and not (box[0] <= lat <= box[1] and box[2] <= lon <= box[3]):
            problems.append((s["id"],
                             "바운딩 박스 밖 {},{} — 부호 누락 의심".format(lat, lon)))
        key = (round(lat, 4), round(lon, 4))
        if key in seen and seen[key] != s.get("name_ko"):
            problems.append((s["id"], "좌표 중복: {}".format(seen[key])))
        seen[key] = s.get("name_ko")
    return problems


# ── KML ─────────────────────────────────────────────────────────────────────
def build_kml(spots, title):
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = title

    for cat, (icon, color, _) in CATEGORY.items():
        style = ET.SubElement(doc, "Style", id="s_" + icon)
        istyle = ET.SubElement(style, "IconStyle")
        ET.SubElement(istyle, "color").text = color
        ET.SubElement(istyle, "scale").text = "1.1"
        ic = ET.SubElement(istyle, "Icon")
        ET.SubElement(ic, "href").text = (
            "https://maps.google.com/mapfiles/kml/shapes/{}.png".format(icon))

    by_day = {}
    for s in spots:
        by_day.setdefault(s.get("day", 0), []).append(s)

    for day in sorted(by_day):
        folder = ET.SubElement(doc, "Folder")
        ET.SubElement(folder, "name").text = "Day {}".format(day)
        for s in by_day[day]:
            icon, _, _ = CATEGORY.get(s.get("category"), DEFAULT_CAT)
            pm = ET.SubElement(folder, "Placemark")
            ET.SubElement(pm, "name").text = s.get("name_ko", s.get("id", ""))
            desc = "{}\n{}".format(s.get("name_en", ""), s.get("note", "")).strip()
            ET.SubElement(pm, "description").text = desc
            ET.SubElement(pm, "styleUrl").text = "#s_" + icon
            pt = ET.SubElement(pm, "Point")
            ET.SubElement(pt, "coordinates").text = "{:.6f},{:.6f},0".format(
                s["lon"], s["lat"])

    raw = ET.tostring(kml, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + raw


# ── CSV ─────────────────────────────────────────────────────────────────────
def build_csv(spots, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Day", "장소명(한)", "장소명(영)", "위도", "경도",
                    "카테고리", "메모", "구글맵링크"])
        for s in sorted(spots, key=lambda x: (x.get("day", 0),
                                              x.get("arrival_order", 0))):
            w.writerow([
                s.get("day", ""), s.get("name_ko", ""), s.get("name_en", ""),
                s["lat"], s["lon"], s.get("category", ""), s.get("note", ""),
                MAPS_SEARCH.format(lat=s["lat"], lon=s["lon"]),
            ])


# ── 경로 URL ────────────────────────────────────────────────────────────────
def route_urls(route):
    """route = {day, title, origin, waypoints[], destination} (각 'lat,lon' 문자열)"""
    wps = route.get("waypoints", [])
    dropped = []
    if len(wps) > MAX_WAYPOINTS:
        dropped = wps[MAX_WAYPOINTS:]
        wps = wps[:MAX_WAYPOINTS]

    wp_param = ""
    if wps:
        wp_param = "&waypoints=" + "%7C".join(wps)
    deep = MAPS_DIR.format(o=route["origin"], d=route["destination"], wp=wp_param)

    chain = "+to:".join(wps + [route["destination"]]) if wps else route["destination"]
    embed = MAPS_EMBED.format(o=route["origin"], chain=chain)
    return deep, embed, dropped


def build_routes_md(routes):
    out = ["# 날짜별 Google Maps 경로 링크", "",
           "클릭하면 구글맵에서 해당 날짜의 전체 경로가 열립니다.",
           "휴대폰에서 열면 그대로 내비게이션을 시작할 수 있습니다.", ""]
    for r in routes:
        deep, _, dropped = route_urls(r)
        out += ["## Day {}".format(r["day"]), "**{}**".format(r.get("title", "")), "", deep, ""]
        if dropped:
            out += ["> 경유지 {}개가 구글맵 상한(9개)을 초과해 제외되었습니다: {}"
                    .format(len(dropped), ", ".join(dropped)), ""]
    return "\n".join(out)


def build_notion_day_maps(routes, spots):
    """날짜별 노션 삽입용 마크다운."""
    by_day = {}
    for s in spots:
        by_day.setdefault(s.get("day", 0), []).append(s)

    blocks = []
    for r in routes:
        day = r["day"]
        deep, embed, dropped = route_urls(r)
        b = ["---", "",
             "## 🗺️ Day {} 지도".format(day), "",
             '<embed src="{}">Day {} 경로: {}</embed>'.format(
                 embed, day, notion_escape(r.get("title", ""))), "",
             "📱 [**휴대폰에서 내비 시작하기 →**]({})".format(deep), "",
             "### 개별 장소 바로가기", "",
             '<table header-row="true">',
             "<tr><td>장소</td><td>구글맵</td><td>메모</td></tr>"]
        for s in sorted(by_day.get(day, []), key=lambda x: x.get("arrival_order", 0)):
            _, _, emoji = CATEGORY.get(s.get("category"), DEFAULT_CAT)
            b.append("<tr><td>{} {}</td><td>[열기]({})</td><td>{}</td></tr>".format(
                emoji, notion_escape(s.get("name_ko", "")),
                MAPS_SEARCH.format(lat=s["lat"], lon=s["lon"]),
                notion_escape(s.get("note", ""))))
        b += ["</table>", ""]
        if dropped:
            b += ["> ⚠️ 경유지 상한(9개) 초과로 {}개 지점이 경로에서 제외되었습니다. "
                  "위 표에서 개별로 여세요.".format(len(dropped)), ""]
        blocks.append("\n".join(b))
    return "\n\n<!-- ===== DAY SPLIT ===== -->\n\n".join(blocks)


# ── 메인 ────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spots", required=True)
    ap.add_argument("--routes")
    ap.add_argument("--out", default="assets")
    ap.add_argument("--title", default="Trip Map")
    ap.add_argument("--box", help="s,n,w,e 바운딩 박스 (예: 43.0,46.0,-112.0,-101.0)")
    args = ap.parse_args()

    spots = json.load(open(args.spots, encoding="utf-8"))
    if isinstance(spots, dict):
        spots = spots.get("spots", [])

    box = None
    if args.box:
        parts = [float(x) for x in args.box.split(",")]
        box = (parts[0], parts[1], parts[2], parts[3])

    problems = validate(spots, box)
    if problems:
        print("⚠️  좌표 검증 경고 {}건".format(len(problems)), file=sys.stderr)
        for pid, msg in problems:
            print("   - {}: {}".format(pid, msg), file=sys.stderr)

    os.makedirs(args.out, exist_ok=True)

    kml_path = os.path.join(args.out, "trip.kml")
    with open(kml_path, "w", encoding="utf-8") as f:
        f.write(build_kml(spots, args.title))
    ET.parse(kml_path)  # 파싱 검증

    csv_path = os.path.join(args.out, "trip_spots.csv")
    build_csv(spots, csv_path)

    written = [kml_path, csv_path]

    if args.routes:
        routes = json.load(open(args.routes, encoding="utf-8"))
        if isinstance(routes, dict):
            routes = routes.get("routes", [])
        rp = os.path.join(args.out, "trip_routes.md")
        with open(rp, "w", encoding="utf-8") as f:
            f.write(build_routes_md(routes))
        np_ = os.path.join(args.out, "notion_day_maps.md")
        with open(np_, "w", encoding="utf-8") as f:
            f.write(build_notion_day_maps(routes, spots))
        written += [rp, np_]

    print("✅ 스팟 {}개 · 생성 파일 {}개".format(len(spots), len(written)))
    for p in written:
        print("   {}".format(p))
    if problems:
        print("⚠️  좌표 경고 {}건 — 위 stderr 확인".format(len(problems)))


if __name__ == "__main__":
    main()

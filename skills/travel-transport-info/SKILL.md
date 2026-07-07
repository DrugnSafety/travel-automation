---
name: travel-transport-info
description: 항공편, 렌트카, 기차 등 교통 예약 확인 자료를 파싱하여 Notion 여행 페이지에 교통 정보 섹션을 생성합니다. 사용자가 업로드한 예약 확인 이메일, PDF, 스크린샷에서 정보를 추출합니다. 사용자가 항공편 정보 추가, 렌트카 예약, 비행기 일정, 교통편 등록, 예약 확인서 등록, 비행 스케줄, 차량 렌트 정보 등을 요청할 때 이 스킬을 사용하세요.
---

# Travel Transport Info

항공편, 렌트카, 기차 등 교통 관련 예약 자료를 파싱하고, Notion 여행 가이드에 교통 정보 전용 페이지/섹션을 생성하는 스킬입니다.

## 핵심 원칙

- 사용자가 **업로드한 자료**(이메일, PDF, 스크린샷)에서 교통 정보를 자동 추출합니다.
- 추출된 정보를 **구조화된 형태**로 Notion 페이지에 반영합니다.
- 파이프라인 초기 단계에서 교통 자료를 수집하여 이후 단계에 활용합니다.
- 파싱 결과는 사용자 확인(pending → confirm) 후에만 캘린더·Notion에 반영합니다.

## 표준 파싱 스키마: schema.org JSON-LD (v3 — TREK 차용)

모든 예약 파싱 결과는 schema.org Reservation 타입으로 정규화한다. 표준 어휘라 파싱 정확도가 높고, 이후 캘린더/Notion 변환 매퍼를 재사용할 수 있다:

```
파싱 지시문: "Extract every travel reservation from the document as schema.org JSON-LD.
Output only {\"reservations\": [...]}. Use @type: FlightReservation, LodgingReservation,
RentalCarReservation, TrainReservation, BusReservation, FoodEstablishmentReservation,
EventReservation. Nest details under reservationFor. Times in ISO 8601 local time.
Always include reservationNumber. For round trips, extract every segment."
```

- 왕복 항공은 구간별로 각각 1개 Reservation
- 시간은 반드시 **현지 시간 + 타임존 명시** (캘린더 등록 오류의 최다 원인) — 공항 IATA 코드로 타임존을 확정한 뒤 이벤트를 만든다
- 결과 저장: `/tmp/{여행지}_transport.json` (schema.org 구조 그대로)

## 지원 교통 수단

### 1. 항공편 (Flights)

**추출 정보:**

| 필드 | 설명 | 예시 |
|------|------|------|
| 항공사 | Airline name + code | United Airlines (UA) |
| 편명 | Flight number | UA1234 |
| 출발 공항 | Departure airport + code | Boston Logan (BOS) |
| 도착 공항 | Arrival airport + code | Las Vegas (LAS) |
| 출발 시간 | Date + time (현지 시간) | 2026-04-15 06:30 EDT |
| 도착 시간 | Date + time (현지 시간) | 2026-04-15 09:45 PDT |
| 터미널/게이트 | Terminal + Gate | Terminal B, Gate B12 |
| 좌석 | Seat assignment | 23A |
| 예약번호 | Confirmation code | ABC123 |
| 수하물 | Baggage allowance | 기내 1개 + 위탁 1개 |
| 경유지 | Layover info | Denver (DEN), 2시간 |
| 비용 | 총 비용 | $450/인 |

### 2. 렌트카 (Rental Car)

**추출 정보:**

| 필드 | 설명 | 예시 |
|------|------|------|
| 렌트 업체 | Company name | Enterprise, Hertz |
| 예약번호 | Confirmation code | RES-789456 |
| 차종 | Vehicle class/model | Midsize SUV (Toyota RAV4 or similar) |
| 픽업 장소 | Pickup location | LAS Airport |
| 픽업 시간 | Date + time | 2026-04-15 10:30 |
| 반납 장소 | Return location | LAS Airport |
| 반납 시간 | Date + time | 2026-04-26 14:00 |
| 보험 | Insurance type | Full Coverage (CDW + LIS) |
| 추가 옵션 | Extras | GPS, 카시트, 추가 운전자 |
| 비용 | Total cost | $780 (11일) |
| 마일리지 | Mileage policy | Unlimited |

### 3. 기차/버스 (Rail/Bus)

**추출 정보:**

| 필드 | 설명 | 예시 |
|------|------|------|
| 운행사 | Operator | Amtrak, Greyhound |
| 노선/편명 | Route/train number | Northeast Regional 2154 |
| 출발역 | Departure station | Boston South Station |
| 도착역 | Arrival station | New York Penn Station |
| 출발/도착 시간 | Times | 08:00 → 12:30 |
| 좌석 | Seat/class | Coach, Car 4 Seat 12 |
| 예약번호 | Confirmation code | TRN-456789 |

## 자료 입력 방식

### 방식 1: 파일 업로드 (기본)

```
1. PDF 예약 확인서
   - 항공사 e-ticket, 렌트카 예약 확인 (PDF)
   - Read tool로 PDF 내용 추출

2. 이메일 스크린샷
   - 예약 확인 이메일 캡처 (PNG/JPG)
   - Read tool로 이미지 OCR 수행 (Claude 멀티모달)

3. 텍스트 파일
   - 예약 정보를 텍스트로 정리한 파일 (.txt, .md)
   - 직접 파싱

4. Word 문서
   - 여행사 일정표 (.docx)
   - markitdown 또는 python-docx로 추출
```

### 방식 2: 직접 입력

사용자가 대화로 직접 정보 제공 → 자연어에서 구조화 데이터로 변환

### 방식 3: 파이프라인 초기 수집

오케스트레이터의 Phase 0(사전 준비)에서 AskUserQuestion:

```
"항공편, 렌트카, 기차 등 교통 예약 자료가 있으시면
 파일을 업로드해주세요. (없으면 건너뛸 수 있습니다)"

옵션:
  1. 파일 업로드
  2. 직접 입력
  3. 나중에 추가
  4. 교통편 없음 (자가용 등)
```

## 파싱 전략

### PDF 파싱

```python
# Read tool로 PDF 내용 읽기, 주요 패턴 매칭:

# 항공편
flight_patterns = [
    r"Flight\s*#?\s*:?\s*([A-Z]{2}\d{2,4})",
    r"Confirmation\s*:?\s*([A-Z0-9]{5,8})",
    r"Depart(?:ure)?:\s*(.+?\d{1,2}:\d{2})",
    r"Arriv(?:al)?:\s*(.+?\d{1,2}:\d{2})",
    r"Seat:\s*(\d{1,2}[A-F])",
    r"Terminal\s*(\w+)\s*Gate\s*(\w+)",
]

# 렌트카
rental_patterns = [
    r"Confirmation\s*(?:Number|Code|#)?\s*:?\s*([A-Z0-9-]+)",
    r"Pick[- ]?up:\s*(.+)",
    r"(?:Drop[- ]?off|Return):\s*(.+)",
    r"Vehicle\s*(?:Class|Type)?\s*:?\s*(.+)",
]
```

### 이미지/스크린샷 OCR

```
1. Read tool로 이미지 파일 읽기 (Claude 멀티모달)
2. 이미지 내 텍스트를 시각적으로 인식
3. 구조화된 데이터로 변환
4. 불확실한 정보는 사용자에게 확인 요청
```

## Notion 페이지 생성

### 교통 정보 전용 서브 페이지

메인 여행 페이지 아래에 "✈️ 교통 정보" 서브 페이지를 생성합니다.

```markdown
# ✈️ 교통 정보

## 항공편

### 🛫 가는 편 (Outbound)

| 항목 | 정보 |
|------|------|
| 항공사 | United Airlines (UA) |
| 편명 | UA1234 |
| 출발 | Boston Logan (BOS) — 2026-04-15 06:30 EDT |
| 도착 | Las Vegas (LAS) — 2026-04-15 09:45 PDT |
| 터미널/게이트 | Terminal B / Gate B12 |
| 좌석 | 23A (창가) |
| 예약번호 | `ABC123` |
| 수하물 | 기내 1개 + 위탁 1개 |

> 💡 **체크인 알림**: 출발 24시간 전(4/14 06:30) 온라인 체크인 가능
> ⏰ **공항 도착 권장**: 출발 2시간 전 (04:30)

---

### 🛬 돌아오는 편 (Return)

| 항목 | 정보 |
|------|------|
| ... | ... |

---

## 🚗 렌트카

| 항목 | 정보 |
|------|------|
| 업체 | Enterprise Rent-A-Car |
| 예약번호 | `RES-789456` |
| 차종 | Midsize SUV (RAV4 or similar) |
| 픽업 | LAS Airport — 2026-04-15 10:30 |
| 반납 | LAS Airport — 2026-04-26 14:00 |
| 보험 | Full Coverage (CDW + LIS + PAI) |
| 추가 옵션 | GPS, 카시트, 추가 운전자 1명 |
| 총 비용 | $780 (11일, 세금 포함) |
| 마일리지 | 무제한 |

> 💡 **픽업 팁**: 공항 셔틀버스 이용, Rental Car Center까지 약 10분
> ⛽ **반납 시**: 주유 후 반납 (Full-to-Full 정책)
> 📋 **필요 서류**: 운전면허증, 신용카드, 국제운전면허증(해외 렌트 시)
```

### 메인 페이지 연동

메인 여행 페이지 개요 테이블에 교통 정보 요약 추가:

```markdown
| 항목 | 정보 |
|------|------|
| 항공편 | UA1234 (BOS→LAS, 4/15 06:30) / UA5678 (LAS→BOS, 4/26 16:00) |
| 렌트카 | Enterprise, Midsize SUV, 4/15~4/26 |
```

### 캘린더 연동 데이터

추출된 교통 정보를 travel-calendar-sync에 전달할 구조화 데이터:

```json
{
  "flights": [
    {
      "type": "outbound",
      "airline": "UA",
      "flight_number": "UA1234",
      "departure": {"airport": "BOS", "time": "2026-04-15T06:30:00-04:00"},
      "arrival": {"airport": "LAS", "time": "2026-04-15T09:45:00-07:00"},
      "confirmation": "ABC123"
    }
  ],
  "rental_car": {
    "company": "Enterprise",
    "pickup": {"location": "LAS Airport", "time": "2026-04-15T10:30:00-07:00"},
    "return": {"location": "LAS Airport", "time": "2026-04-26T14:00:00-07:00"},
    "confirmation": "RES-789456"
  }
}
```

저장 위치: `/tmp/{여행지}_transport.json`

## 파이프라인 통합

### 오케스트레이터에서의 위치

```
Phase 0: 사전 준비
    ↓
Phase 0.5: travel-transport-info ← 여기 (교통 자료 수집 및 파싱)
    ↓
Phase 1: travel-research
    ↓
Phase 2: notion-travel-page (교통 정보 포함하여 생성)
    ...
Phase 5: travel-calendar-sync (항공편/픽업 이벤트 포함)
```

### 데이터 흐름

```
사용자 업로드 (PDF/이미지/텍스트)
    ↓ 파싱
구조화된 교통 데이터 (/tmp/{여행지}_transport.json)
    ↓
Phase 2: Notion 교통 정보 서브 페이지 생성
Phase 5: Calendar에 항공편/픽업/체크인 이벤트 추가
```

## 체크인 알림 자동 생성

항공편 정보가 있을 경우, 캘린더에 체크인 알림도 생성:

```
- 출발 24시간 전: "✈️ 온라인 체크인 — {항공사} {편명}"
- 출발 2시간 전: "🚗 공항 출발 — {공항명}"
- 렌트카 반납 1시간 전: "⛽ 렌트카 주유 알림"
```

## 자주 사용하는 공항 시간대 매핑

```
US 주요 공항:
BOS, JFK, EWR, PHL, IAD, DCA → America/New_York (ET)
ORD, MDW, MSP, DTW, STL      → America/Chicago (CT)
DEN, PHX, SLC, ABQ            → America/Denver (MT)
LAX, SFO, SEA, PDX, LAS, SAN → America/Los_Angeles (PT)
HNL                            → Pacific/Honolulu (HT)

아시아:
ICN, GMP → Asia/Seoul
NRT, HND → Asia/Tokyo
```

## 오류 처리

| 상황 | 대응 |
|------|------|
| PDF 파싱 실패 | 사용자에게 수동 입력 요청 |
| 이미지 OCR 불확실 | 추출된 정보를 사용자에게 확인 요청 |
| 시간대 모호 | 공항 코드에서 시간대 자동 추론 |
| 정보 불완전 | 있는 정보만 반영, 빈 필드는 "확인 필요" 표시 |
| 파일 없음 | 스킵하고 다음 단계 진행 |

# ☕ Cafe Vision AI — YOLO + ByteTrack + LLM 데모

무인카페 CCTV 영상을 **YOLO11n-seg**로 감지하고 **ByteTrack**으로 추적한 뒤, 추출한 메타데이터를 **Claude LLM**이 운영 행동 지침으로 바꿔주는 실시간 풍 Streamlit 데모입니다.

학습·실습용 프로젝트이며 일반 대중 시연을 염두에 두고 만들었습니다.

## 스크린샷

> 실시간 재생 시 원본 CCTV와 YOLO 세그먼테이션 결과를 나란히 비교, 구역별 인원 분포와 핵심 지표가 동시에 갱신되고 분석 완료 후 LLM이 우선순위 뱃지와 함께 행동 지침을 출력합니다. 추가로 기술 원리 탭에서 격자 분할 / IoU / NMS / ByteTrack 저신뢰 재매칭을 인터랙티브 위젯으로 체험할 수 있습니다.

## 설치

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

CPU만으로 동작합니다 (GPU 있으면 더 빠름).

## 실행 순서

```bash
# 1) 영상 배치 — data/cafe_video.mp4 로 저장 (또는 심볼릭 링크)
ln -sf /path/to/video.mp4 data/cafe_video.mp4

# 2) YOLO 추론 + 원본/렌더링 프레임 + 통계 저장
.venv/bin/python preprocess.py

# 3) LLM 인사이트 생성 (선택 — 없어도 폴백 인사이트 사용)
export ANTHROPIC_API_KEY=sk-ant-...
.venv/bin/python generate_insight.py

# 4) Streamlit 실행
.venv/bin/streamlit run app.py
```

기본 URL: http://localhost:8501

## 프로젝트 구조

```
cafe-demo/
├── app.py                # Streamlit 대시보드 (실시간 분석/시뮬/추적/기술원리 4탭)
├── tech_tab.py           # 🎓 기술 원리 탭 (인터랙티브 HTML/CSS/JS 위젯)
├── preprocess.py         # YOLO + ByteTrack 추론 → 프레임/통계 저장
├── generate_insight.py   # Claude API 단일 호출 → insight.json
├── bytetrack.yaml        # ByteTrack 하이퍼파라미터 (프로젝트 버전 고정)
├── requirements.txt
├── .streamlit/config.toml   # 다크 테마 + Pretendard 폰트
└── data/
    ├── cafe_video.mp4
    ├── frames/           # YOLO 렌더링 프레임 (bbox+mask 표시)
    ├── frames_raw/       # 원본 프레임 (비교 뷰용)
    ├── stats/            # 초별 집계 JSON
    ├── tracking_data.json
    ├── zone_stats.json
    └── insight.json      # LLM 생성 결과
```

## 기술 스택

- **Detection**: Ultralytics YOLO11n-seg (COCO-pretrained, person class만 사용)
- **Tracking**: ByteTrack (저신뢰 탐지 재활용으로 ID 일관성 유지)
- **Runtime**: Python 3.12, OpenCV, PIL
- **UI**: Streamlit 1.56 + `@st.fragment(run_every=...)` 기반 재생 제어
- **Viz**: Plotly + 커스텀 HTML/CSS/JS 위젯 (`st.components.v1.html`)
- **LLM**: Anthropic Claude Sonnet 4.5

## 핵심 UX

| 기능 | 설명 |
|---|---|
| 재생 제어 | ▶/⏸/↺/⏭ · 프레임 슬라이더로 Q&A 시 원하는 장면으로 스크럽 |
| 원본/YOLO 비교 | 상단 2컬럼 동기 재생 |
| 구역 오버레이 | 사이드바 토글로 좌석A/B/주문구역 반투명 영역 표시 |
| 속도 조절 | 0.5x / 1x / 2x / 4x |
| 분석 파이프라인 로그 | INIT → DETECT → TRACK → ZONE → LLM 5단계 순차 체크 |
| 인사이트 뱃지 | 🔴긴급 / 🟡개선 / 🟢최적화 + 정량적 impact |
| 기술 원리 탭 | 격자·IoU·NMS·Kalman·ByteTrack 인터랙티브 위젯 + FAQ |

## 영상 출처 및 라이선스

- **원본**: 유튜브 쏠제이 무인카페 채널 · <https://youtube.com/shorts/0jKwKe5pWvg?si=R30fTAh7lA-ZaVOK>
- **라이선스**: YouTube 크리에이티브 커먼즈(CC BY)
- **사용 목적**: 비상업적 학습·연구·실습 (대한민국 저작권법 제35조의5 공정이용 및 CC BY 조건 준수)
- **개인정보**: 원본 영상의 얼굴은 크리에이터가 사전 블러 처리함. 본 시스템은 분석 후 좌표·시간 등 비식별 메타데이터만 저장하며 원본 영상·생체정보를 보유하지 않음 (PIPA 제58조 요건 충족)

## 로드맵

본 MVP는 **단일 카메라 · 범용 COCO 모델**로 운영됩니다. 향후 확장:

1. Zero-Touch 세팅 + YOLO11-seg/SAM 기반 구역 자동 인식
2. 악조건 극복 + ByteTrack/BoT-SORT 파이프라인 최적화 + 시공간 룰
3. 데이터 플라이휠 → 카페 특화 파인튜닝
4. 대형 리테일 확장: Re-ID + 다중카메라 MTMC + 행동 인식

자세한 기술 설명은 앱 내 **🎓 기술 원리** 탭 참고.

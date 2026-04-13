"""
카페 비전 AI 데모 — 다크 UI · 원본/YOLO 비교 · 재생제어 · 구역 오버레이 · LLM 인사이트 · 기술원리 탭

아키텍처:
  - 단일 fragment(playback_fragment)가 자기-재호출(st.rerun(scope="fragment"))로 루프
  - advance 로직은 반드시 slider 위젯 렌더 이전에 실행 (Streamlit 위젯 state 제약)
  - 사이드바 위젯 key 자체가 state 단일 진실원
"""
from __future__ import annotations
import base64
import glob
import io
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from tech_tab import render_tech_tab
from design_dna import css_for, home_button_html

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# 디자인 팔레트 — orange-400 / yellow-400 (design-dna §0 모드 B · 같은 가족)
ACCENT_HEX    = "#fb923c"
SECONDARY_HEX = "#facc15"


def mode_colors() -> tuple[str, str]:
    """(accent, secondary) hex — Plotly/이미지 등 CSS 변수 닿지 않는 경로용."""
    return (ACCENT_HEX, SECONDARY_HEX)


def _hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


def mode_zone_colors() -> dict[str, str]:
    """주문구역 색을 accent 로. 좌석 A/B 는 파랑 계열 의미색 유지."""
    return {"좌석A": "#4F8BF9", "좌석B": "#85B7EB", "주문구역": ACCENT_HEX}

st.set_page_config(
    page_title="Cafe Vision AI", page_icon="☕",
    layout="wide", initial_sidebar_state="expanded",
)

ZONE_COLORS = {"좌석A": "#4F8BF9", "좌석B": "#85B7EB", "주문구역": "#FF6B35"}
ZONE_RGBA = {
    "좌석A": (79, 139, 249, 55),
    "좌석B": (133, 183, 235, 55),
    "주문구역": (255, 107, 53, 55),
}
SPEED_MAP = {"0.5x": 0.5, "1x": 1.0, "2x": 2.0, "4x": 4.0}
BASE_DELAY = 0.08  # 초당 약 12.5프레임 (1x 기준)


# =============================================================================
# STATE
# =============================================================================
def init_state():
    defaults = {
        "playing": False,
        "frame_scrub": 0,
        "started": False,
        "speed_label": "1x",
        "overlay": False,
        "trails": True,
        "llm_live": False,
        "celebration_played": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def on_scrub():
    """슬라이더 드래그 시 자동 pause."""
    st.session_state.playing = False


# =============================================================================
# CSS · CHROME · THEME REMAP
# =============================================================================
def inject_css():
    """Design DNA CSS (mode B · orange-400/yellow-400) 주입."""
    st.markdown(css_for("b"), unsafe_allow_html=True)


def inject_chrome():
    """Home 버튼 (Apple squircle + rotating conic border)."""
    st.markdown(home_button_html(href="#"), unsafe_allow_html=True)


def inject_emoji_strip():
    """페이지 전체 텍스트 노드에서 이모지 및 재생 컨트롤 기호 제거.
       re-render 대응을 위해 MutationObserver 로 childList 변경 감지."""
    st.components.v1.html(
        """
        <script>
        (function() {
          // Extended_Pictographic + 자주 쓰는 재생/상태 기호(▶⏸⏭⏮↺◀⏯⏹●○↗↘✓✗)
          const EMOJI_RE = /(\\p{Extended_Pictographic}|[\\u25B6\\u23F8\\u23ED\\u23EE\\u23EF\\u21BA\\u21BB\\u25C0\\u23F9\\u25CF\\u25CB\\u2197\\u2198\\u2713\\u2717\\u2709\\u2328\\u2699])\\uFE0F?/gu;
          const doc = (window.parent && window.parent.document) || document;
          let busy = false;

          function stripNode(node) {
            if (node.nodeType === 3) {
              const v = node.nodeValue;
              if (EMOJI_RE.test(v)) {
                const cleaned = v.replace(EMOJI_RE, '')
                                 .replace(/^[\\s·]+/, '')
                                 .replace(/\\s{2,}/g, ' ');
                if (cleaned !== v) node.nodeValue = cleaned;
              }
            } else if (node.nodeType === 1) {
              const tag = node.tagName;
              if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'IFRAME') return;
              for (const c of node.childNodes) stripNode(c);
            }
          }

          function run() {
            if (busy) return;
            busy = true;
            try { stripNode(doc.body); } catch (e) { /* noop */ }
            busy = false;
          }

          run();
          [150, 400, 900, 1800].forEach(ms => setTimeout(run, ms));

          try {
            const obs = new MutationObserver(() => run());
            obs.observe(doc.body, { childList: true, subtree: true });
          } catch (e) { /* same-origin 제약 시 silent */ }
        })();
        </script>
        """,
        height=0,
    )


def inject_slider_recolor():
    """Streamlit 1.56 은 emotion(css-in-js) 으로 config.toml primaryColor 를 <style> 에 주입.
       그 결과 slider filled track · toggle on 등 일부 요소에 원본 오렌지가 남음.
       여기선 3층을 모두 치환해 design DNA orange-400 / yellow-400 로 통일:
         1) <style> 태그 textContent 내 rgb(255,107,53) / #FF6B35 → accent
         2) cssRules.style (emotion insertRule 대비)
         3) [style] inline attribute (BaseWeb 동적 inline · linear-gradient 포함)
       MutationObserver + debounce 로 rerender · drag 에 대응."""
    acc, sec = mode_colors()
    st.components.v1.html(
        f"""
        <script>
        (function() {{
          const ACCENT    = {acc!r};
          const SECONDARY = {sec!r};
          // 원본 오렌지(#FF6B35 / rgb(255,107,53)) → accent
          // 원본 앰버  (#FFC857 / rgb(255,200,87)) → secondary
          const RULES = [
            [/rgb\\(\\s*255\\s*,\\s*107\\s*,\\s*53\\s*\\)/g, ACCENT],
            [/#FF6B35/gi,                                    ACCENT],
            [/rgb\\(\\s*255\\s*,\\s*200\\s*,\\s*87\\s*\\)/g, SECONDARY],
            [/#FFC857/gi,                                    SECONDARY],
          ];
          const HAS = /rgb\\(\\s*255\\s*,\\s*(?:107\\s*,\\s*53|200\\s*,\\s*87)\\s*\\)|#FF6B35|#FFC857/i;
          const doc = (window.parent && window.parent.document) || document;
          let busy = false;
          let timer = null;

          function swap(str) {{
            let out = str;
            for (const [r, c] of RULES) out = out.replace(r, c);
            return out;
          }}

          function recolor() {{
            if (busy) return;
            busy = true;
            try {{
              // (1) <style> 태그 텍스트 직접 치환
              doc.querySelectorAll('style').forEach(s => {{
                const t = s.textContent;
                if (t && HAS.test(t)) s.textContent = swap(t);
              }});

              // (2) cssRules API 로 rule 단위 치환 (emotion insertRule 대비)
              for (const sheet of doc.styleSheets) {{
                let rules;
                try {{ rules = sheet.cssRules; }} catch (e) {{ continue; }}
                if (!rules) continue;
                for (const rule of rules) {{
                  if (!rule.style) continue;
                  for (let i = 0; i < rule.style.length; i++) {{
                    const prop = rule.style[i];
                    const val = rule.style.getPropertyValue(prop);
                    if (val && HAS.test(val)) {{
                      rule.style.setProperty(prop, swap(val),
                        rule.style.getPropertyPriority(prop));
                    }}
                  }}
                }}
              }}

              // (3) inline style 치환 (BaseWeb thumb 등 동적 inline)
              doc.querySelectorAll('[style]').forEach(el => {{
                const s = el.getAttribute('style');
                if (s && HAS.test(s)) el.setAttribute('style', swap(s));
              }});
            }} catch (e) {{ /* silent */ }}
            busy = false;
          }}

          function schedule() {{
            if (timer) clearTimeout(timer);
            timer = setTimeout(recolor, 40);
          }}

          recolor();
          [100, 300, 800, 1600].forEach(ms => setTimeout(recolor, ms));

          try {{
            const obs = new MutationObserver(schedule);
            obs.observe(doc.body, {{
              attributes: true, childList: true, subtree: true,
              characterData: true, attributeFilter: ['style']
            }});
            // head 의 <style> 도 감시 (emotion 이 여기 rule 주입)
            if (doc.head) {{
              const obsHead = new MutationObserver(schedule);
              obsHead.observe(doc.head, {{
                childList: true, subtree: true, characterData: true
              }});
            }}
          }} catch (e) {{ /* same-origin 제약 시 silent */ }}
        }})();
        </script>
        """,
        height=0,
    )


# =============================================================================
# DATA / CACHING
# =============================================================================
@st.cache_data
def load_artifacts():
    frames_yolo = sorted(glob.glob(str(DATA / "frames" / "*.jpg")))
    frames_raw = sorted(glob.glob(str(DATA / "frames_raw" / "*.jpg")))
    stats_files = sorted(glob.glob(str(DATA / "stats" / "*.json")))
    stats = [json.loads(Path(f).read_text(encoding="utf-8")) for f in stats_files]
    tracking = json.loads((DATA / "tracking_data.json").read_text(encoding="utf-8"))
    zone_stats = json.loads((DATA / "zone_stats.json").read_text(encoding="utf-8"))
    insight_path = DATA / "insight.json"
    insight = (
        json.loads(insight_path.read_text(encoding="utf-8"))
        if insight_path.exists()
        else {"headline": "인사이트 생성 전", "actions": [], "summary": "", "source": "none"}
    )
    return frames_yolo, frames_raw, stats, tracking, zone_stats, insight


@st.cache_data
def get_overlay_rgba(w: int, h: int) -> bytes:
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 300, 400, h], fill=ZONE_RGBA["좌석A"])
    d.rectangle([0, 0, 400, 300], fill=ZONE_RGBA["좌석B"])
    d.rectangle([400, 0, w, h], fill=ZONE_RGBA["주문구역"])
    d.line([400, 0, 400, h], fill=(255, 255, 255, 110), width=2)
    d.line([0, 300, 400, 300], fill=(255, 255, 255, 110), width=2)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18
        )
    except Exception:
        font = ImageFont.load_default()
    labels = [
        (12, 310, "A-SEAT", (79, 139, 249, 230)),
        (12, 10, "B-SEAT", (133, 183, 235, 230)),
        (410, 10, "ORDER", (255, 107, 53, 230)),
    ]
    for x, y, txt, color in labels:
        d.rectangle([x - 4, y - 2, x + 78, y + 22], fill=(10, 13, 19, 200))
        d.text((x, y), txt, fill=color, font=font)
    buf = io.BytesIO()
    ov.save(buf, format="PNG")
    return buf.getvalue()


TRAIL_PALETTE = [
    (79, 139, 249), (255, 107, 53), (35, 197, 82), (255, 200, 87),
    (255, 107, 157), (127, 229, 186), (148, 159, 255), (255, 183, 110),
    (138, 226, 255), (244, 162, 97),
]


@st.cache_data
def get_track_series(rows_json: str):
    """트랙 ID별 (frame, cx, cy) 시계열. load_artifacts 결과에서 한 번만 구축."""
    from collections import defaultdict
    rows = json.loads(rows_json)
    series = defaultdict(list)
    for r in rows:
        series[int(r["track_id"])].append((int(r["frame"]), float(r["center"][0]), float(r["center"][1])))
    return {tid: sorted(pts) for tid, pts in series.items()}


def build_trails(series, upto_frame: int) -> dict[int, list[tuple[float, float]]]:
    """frame_idx 이하까지의 track별 (x,y) 포인트 리스트."""
    return {tid: [(x, y) for f, x, y in pts if f <= upto_frame] for tid, pts in series.items()}


def apply_trails(img: Image.Image, trails: dict[int, list[tuple[float, float]]]) -> Image.Image:
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for tid, pts in trails.items():
        if not pts:
            continue
        color = TRAIL_PALETTE[tid % len(TRAIL_PALETTE)]
        if len(pts) >= 2:
            d.line(pts, fill=(*color, 160), width=3, joint="curve")
        x, y = pts[-1]
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(*color, 230),
                  outline=(255, 255, 255, 220), width=1)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


@st.cache_data
def _cached_frame_bytes(path: str, max_width: int, overlay: bool) -> bytes:
    img = Image.open(path).convert("RGB")
    if overlay:
        ov = Image.open(io.BytesIO(get_overlay_rgba(img.width, img.height)))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return buf.getvalue()


def load_frame_b64(path: str, max_width: int = 380, overlay: bool = False,
                   trails: dict | None = None) -> str:
    if not trails:
        return base64.b64encode(_cached_frame_bytes(path, max_width, overlay)).decode("ascii")

    img = Image.open(path).convert("RGB")
    if overlay:
        ov = Image.open(io.BytesIO(get_overlay_rgba(img.width, img.height)))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    img = apply_trails(img, trails)
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def img_html(path: str, max_width: int = 380, overlay: bool = False,
             trails: dict | None = None) -> str:
    b64 = load_frame_b64(path, max_width, overlay, trails)
    return f'<img src="data:image/jpeg;base64,{b64}" alt="frame"/>'


# =============================================================================
# STATIC COMPONENTS
# =============================================================================
def render_setup_guide():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#151A24 0%,#1A2233 100%);
                border:1px solid rgba(255,107,53,0.25);border-radius:16px;
                padding:32px 36px;margin-top:20px">
      <div style="font-size:11px;font-weight:700;color:#FF6B35;letter-spacing:0.12em;
                  text-transform:uppercase;margin-bottom:12px">⚙️ 초기 셋업 필요</div>
      <h2 style="color:#F5F6F8;font-size:22px;font-weight:700;margin:0 0 16px 0">
        분석 데이터가 아직 생성되지 않았습니다
      </h2>
      <p style="color:#A0A7B4;font-size:14px;line-height:1.7;margin:0 0 20px 0">
        Streamlit 데모를 보려면 먼저 영상 전처리(YOLO 추론 + 메타데이터 추출)가 필요합니다.
        아래 순서로 터미널에서 실행하세요.
      </p>
      <div style="background:#0A0D13;border:1px solid rgba(255,255,255,0.06);
                  border-radius:10px;padding:16px 20px;font-family:'JetBrains Mono',monospace;
                  font-size:13px;color:#7FE5BA;line-height:1.9">
        <span style="color:#5B6577"># 1) 영상 배치 (이미 있다면 스킵)</span><br>
        $ ln -sf /path/to/video.mp4 data/cafe_video.mp4<br><br>
        <span style="color:#5B6577"># 2) YOLO 추론 · 200프레임 + 통계 JSON 생성 (~3-5분)</span><br>
        $ .venv/bin/python preprocess.py<br><br>
        <span style="color:#5B6577"># 3) LLM 인사이트 생성 (API 키 없으면 폴백 사용)</span><br>
        $ export ANTHROPIC_API_KEY=sk-ant-...<br>
        $ .venv/bin/python generate_insight.py<br><br>
        <span style="color:#5B6577"># 4) 이 페이지 새로고침</span>
      </div>
      <p style="color:#6B7280;font-size:12px;margin:16px 0 0 0">
        💡 생성되는 파일: <code style="color:#FFC857">data/frames/</code>,
        <code style="color:#FFC857">data/frames_raw/</code>,
        <code style="color:#FFC857">data/tracking_data.json</code>,
        <code style="color:#FFC857">data/insight.json</code>
      </p>
    </div>
    """, unsafe_allow_html=True)


# (tx, ty, size, color, delay) — 12 particles, 3색, stable layout
_CELEBRATION_PARTICLES = [
    (-72, -92, 6, "#FF6B35", 0.00),
    (-34, -116, 5, "#FFC857", 0.04),
    (8, -128, 7, "#4F8BF9", 0.07),
    (44, -104, 6, "#FF6B35", 0.11),
    (76, -82, 5, "#FFC857", 0.15),
    (-82, -64, 4, "#4F8BF9", 0.02),
    (-22, -74, 8, "#FF6B35", 0.09),
    (26, -88, 5, "#FFC857", 0.13),
    (62, -118, 4, "#4F8BF9", 0.17),
    (-50, -134, 6, "#FF6B35", 0.20),
    (88, -102, 5, "#FFC857", 0.06),
    (-12, -58, 7, "#4F8BF9", 0.22),
]


def celebration_html() -> str:
    dots = "".join(
        f'<div class="particle" style="--tx:{tx}px;--ty:{ty}px;--delay:{d}s;'
        f'width:{s}px;height:{s}px;color:{c};background:{c}"></div>'
        for tx, ty, s, c, d in _CELEBRATION_PARTICLES
    )
    return f'<div class="celebration">{dots}</div>'


def render_navbar():
    st.markdown("""
    <div class="navbar">
      <div class="navbar-logo">CV</div>
      <div class="navbar-brand">Cafe Vision AI</div>
      <div class="navbar-spacer"></div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(n_frames: int):
    with st.sidebar:
        with st.expander("⚙️ 재생 설정", expanded=True):
            st.select_slider(
                "재생 속도", options=list(SPEED_MAP.keys()), key="speed_label"
            )
            st.toggle("🎨 구역 오버레이", key="overlay")
            st.toggle("🌀 추적 궤적 표시", key="trails",
                      help="YOLO 프레임 위에 각 track_id의 이동 경로를 반투명 선으로 누적")
        with st.expander("🎯 분석 옵션", expanded=False):
            st.slider("Confidence threshold", 0.1, 0.8, 0.25, 0.05, disabled=True,
                      help="재실행 필요 (preprocess.py)")
            st.toggle("🤖 LLM 실시간 호출", key="llm_live",
                      help="ANTHROPIC_API_KEY 필요 · 활성화 시 generate_insight.py 재호출")
        with st.expander("📈 데이터셋 정보", expanded=False):
            st.caption(f"총 프레임: **{n_frames}**")
            st.caption("영상 길이: **13.3초** @ 15fps")
            st.caption("해상도: **720 × 804** (세로)")
        st.markdown("""
        <div class="sb-footer">
          <b style="color:#8B95A5">📎 영상 출처</b><br>
          유튜브 쏠제이 무인카페<br>
          <a href="https://youtube.com/shorts/0jKwKe5pWvg" target="_blank">원본 링크</a><br>
          CC BY 라이선스 · 비상업적 학습 목적<br>
          얼굴 블러는 크리에이터 측 사전 처리
        </div>
        """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div class="footer">
      <div class="footer-title">📎 영상 출처 · 저작권 · 개인정보</div>
      <b>영상 출처</b>: 유튜브 쏠제이 무인카페 채널 ·
      <a href="https://youtube.com/shorts/0jKwKe5pWvg?si=R30fTAh7lA-ZaVOK" target="_blank">원본 링크</a> ·
      CC BY 라이선스 영상<br>
      <b>사용 목적</b>: 비상업적 학습·연구·실습 · 대한민국 저작권법 제35조의5(공정이용) 및 CC BY 조건 준수<br>
      <b>개인정보</b>: 원본 영상의 얼굴은 크리에이터에 의해 사전 블러 처리됨. 본 시스템은 분석 후 좌표·시간 등 비식별 메타데이터만 저장,
      원본 영상 및 생체정보를 보유하지 않음 · 개인정보보호법(PIPA) 제58조 요건 충족<br>
      <b>기술 스택</b>: YOLO11n-seg (Ultralytics) · ByteTrack · Streamlit · Plotly · Claude Sonnet 4.5 ·
      <b>데이터</b>: 이 데모는 학습용이며 실제 서비스 운영 데이터가 아닙니다.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# LIVE TAB PIECES
# =============================================================================
STAGES = [
    ("00:00", "INIT", "YOLO11n-seg 모델 로드 완료 · 80M params · ByteTrack 초기화"),
    ("00:01", "DETECT", "프레임별 person class 감지 · COCO class 0 · conf ≥ 0.25"),
    ("00:02", "TRACK", "ByteTrack association · Kalman predict · 저신뢰 재매칭"),
    ("00:03", "ZONE", "좌표 기반 구역 분류 (좌석A/B/주문구역) · 체류시간 집계"),
    ("00:04", "LLM", "Claude Sonnet 4.5 호출 · 운영 컨설팅 프롬프트 · JSON 스키마 강제"),
]


def stage_log_html(upto: int) -> str:
    lines = []
    for i, (t, stage, msg) in enumerate(STAGES[: upto + 1]):
        icon = "✓" if i < upto else "▸"
        lines.append(
            f'<div class="log-line">'
            f'<span class="log-time">[{t}]</span>'
            f'<span class="log-stage">{icon} {stage:<7}</span>'
            f'<span>{msg}</span></div>'
        )
    return f'<div class="log-panel">{"".join(lines)}</div>'


def sparkline_svg(values, color: str = "#FF6B35", width: int = 220, height: int = 22) -> str:
    if not values or len(values) < 2:
        return ""
    lo, hi = float(min(values)), float(max(values))
    rng = max(1e-6, hi - lo)
    step = width / (len(values) - 1)
    pts = " ".join(
        f"{i*step:.1f},{height - (v - lo) / rng * (height - 3) - 1.5:.1f}"
        for i, v in enumerate(values)
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'preserveAspectRatio="none" style="display:block;margin-top:8px;opacity:0.85">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def kpi_card_html(label: str, value, unit: str = "",
                  trend: str | None = None, trend_cls: str = "trend-neutral",
                  spark_values=None, spark_color: str = "#FF6B35") -> str:
    t = f'<div class="kpi-trend {trend_cls}">{trend}</div>' if trend else ""
    s = sparkline_svg(spark_values, spark_color) if spark_values else ""
    return f"""<div class="kpi">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
      {t}
      {s}
    </div>"""


def kpis_html(tracking, i: int) -> str:
    pfc = tracking["per_frame_count"][: i + 1]
    cur = tracking["per_frame_count"][i] if i < len(tracking["per_frame_count"]) else 0
    peak = max(pfc) if pfc else 0

    # 스파크라인용 시계열 (최근 30포인트)
    window = 30
    cur_series = pfc[-window:]
    peak_series = []
    running_peak = 0
    for v in pfc:
        running_peak = max(running_peak, v)
        peak_series.append(running_peak)
    peak_series = peak_series[-window:]

    # 누적 고유 방문 시계열
    seen = set()
    unique_series = []
    rows_by_frame = {}
    for r in tracking["rows"]:
        rows_by_frame.setdefault(r["frame"], []).append(int(r["track_id"]))
    for f in range(i + 1):
        for tid in rows_by_frame.get(f, []):
            seen.add(tid)
        unique_series.append(len(seen))
    unique_series = unique_series[-window:]
    unique_seen = len(seen)

    avg = round(sum(pfc) / max(1, len(pfc)), 1)
    congestion = min(100, int(avg * 12))
    congestion_series = [min(100, int((v if isinstance(v, (int, float)) else 0) * 12)) for v in cur_series]

    cong_color = "#23C552" if congestion < 50 else ("#FFC857" if congestion < 75 else "#FF6B6B")

    return '<div class="kpi-row">' + "".join([
        kpi_card_html("현재 인원", cur, " 명", f"구간 평균 {avg}", "trend-up",
                      spark_values=cur_series, spark_color="#4F8BF9"),
        kpi_card_html("피크 인원", peak, " 명", "최대 동시 체류", "trend-neutral",
                      spark_values=peak_series, spark_color="#FFC857"),
        kpi_card_html("누적 고유 방문", unique_seen, " 명",
                      f"전체 {len(tracking['dwell_seconds_by_track'])}명 중", "trend-neutral",
                      spark_values=unique_series, spark_color="#85B7EB"),
        kpi_card_html("혼잡도", congestion, " / 100",
                      "🟢 여유" if congestion < 50 else ("🟡 보통" if congestion < 75 else "🔴 혼잡"),
                      "trend-up" if congestion < 50 else "trend-down",
                      spark_values=congestion_series, spark_color=cong_color),
    ]) + "</div>"


def regenerate_insight() -> dict | None:
    """LLM 실시간 재호출 — generate_insight 모듈 import + 현재 data 사용."""
    try:
        from generate_insight import build_prompt, call_claude, FALLBACK
        tracking = json.loads((DATA / "tracking_data.json").read_text(encoding="utf-8"))
        zone_stats = json.loads((DATA / "zone_stats.json").read_text(encoding="utf-8"))
        prompt = build_prompt(tracking, zone_stats)
        data = call_claude(prompt) or {**FALLBACK, "source": "fallback"}
        out = DATA / "insight.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        load_artifacts.clear()  # 캐시 무효화
        return data
    except Exception as e:
        st.error(f"인사이트 재생성 실패: {e}")
        return None


def render_insight_block(insight: dict):
    """인사이트 카드 + 재생성 버튼."""
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.session_state.llm_live:
            if st.button("🔄 재생성", use_container_width=True, key="btn_regen",
                         help="Claude를 다시 호출해 인사이트 갱신"):
                new_insight = regenerate_insight()
                if new_insight:
                    st.toast(f"✅ 인사이트 갱신됨 · source={new_insight.get('source')}")
                    st.rerun()
    insight_card(insight)


def insight_card(insight: dict):
    actions = insight.get("actions", [])
    priorities_map = {
        "urgent": ("pri-urgent", "🔴 긴급"),
        "improve": ("pri-improve", "🟡 개선"),
        "optimize": ("pri-optimize", "🟢 최적화"),
    }
    defaults = ["urgent", "improve", "optimize"]
    rows_html = ""
    for i, act in enumerate(actions[:3]):
        if isinstance(act, str):
            text, impact, priority = act, "", defaults[i] if i < 3 else "optimize"
        else:
            text = act.get("text", "")
            impact = act.get("impact", "")
            priority = act.get("priority", defaults[i] if i < 3 else "optimize")
        cls, lbl = priorities_map.get(priority, ("pri-optimize", "🟢 최적화"))
        impact_html = f'<div class="action-impact">↗ {impact}</div>' if impact else ""
        rows_html += f"""<div class="action-row">
          <span class="priority-badge {cls}">{lbl}</span>
          <div>
            <div class="action-text">{text}</div>
            {impact_html}
          </div>
        </div>"""
    summary = insight.get("summary", "")
    summary_html = f'<div class="insight-summary">💡 {summary}</div>' if summary else ""
    source = insight.get("source", "unknown")
    src_color = "#23C552" if source == "claude" else "#8B95A5"
    src_label = "Claude Sonnet 4.5" if source == "claude" else "폴백 인사이트"
    st.markdown(f"""<div class="insight">
      <div class="insight-head">
        <span>🤖 AI 행동 지침</span>
        <span style="margin-left:auto;color:{src_color};font-weight:600">● {src_label}</span>
      </div>
      <div class="insight-title">{insight.get('headline', '')}</div>
      {rows_html}
      {summary_html}
    </div>""", unsafe_allow_html=True)


def render_control_row(n: int):
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 6])
    with c1:
        if not st.session_state.started:
            label = "▶ 분석 시작"
        elif st.session_state.playing:
            label = "⏸ 일시정지"
        else:
            label = "▶ 재생"
        if st.button(label, type="primary", use_container_width=True, key="btn_play"):
            if not st.session_state.started:
                st.session_state.started = True
            if st.session_state.frame_scrub >= n - 1:
                st.session_state.frame_scrub = 0
            st.session_state.playing = not st.session_state.playing
    with c2:
        if st.button("↺ 처음으로", use_container_width=True, key="btn_reset",
                     disabled=not st.session_state.started):
            st.session_state.frame_scrub = 0
            st.session_state.playing = False
    with c3:
        if st.button("⏭ 마지막", use_container_width=True, key="btn_end",
                     disabled=not st.session_state.started):
            st.session_state.frame_scrub = n - 1
            st.session_state.playing = False
    with c4:
        i = st.session_state.frame_scrub
        sec = min(i // 15, 13)
        status_color = "#23C552" if st.session_state.playing else "#8B95A5"
        status_text = "● 재생 중" if st.session_state.playing else "○ 정지"
        st.markdown(
            f'<div class="status-bar">'
            f'프레임 <b style="color:#FFC857">{i + 1}</b> / {n} · '
            f'재생 위치 <b style="color:#FFC857">{sec:02d}초</b> / 13초 · '
            f'속도 <b style="color:#FFC857">{st.session_state.speed_label}</b> · '
            f'상태 <b style="color:{status_color}">{status_text}</b>'
            f'</div>', unsafe_allow_html=True
        )


def render_video_pair(frames_raw, frames_yolo, i: int, n: int, trails_map: dict | None):
    ov = st.session_state.overlay
    yolo_caption = "YOLO11n-SEG · ByteTrack · conf≥0.25"
    if trails_map:
        yolo_caption += f" · TRAILS ON ({len(trails_map)} IDs)"
    pct = int((i + 1) / n * 100)
    seekbar = (
        f'<div class="video-seekbar">'
        f'<div class="video-seekbar-fill" style="width:{pct}%"></div>'
        f'</div>'
    )
    st.markdown('<div class="section-label major">📹 영상 비교 — 원본 vs AI 렌더링</div>', unsafe_allow_html=True)
    v1, v2 = st.columns(2, gap="medium")
    with v1:
        st.markdown('<div class="video-caption"><span class="video-tag-raw">●</span> RAW CCTV</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="video-frame"><div class="video-wrap">'
            f'{img_html(frames_raw[i], 380, ov)}'
            f'<div class="src-overlay">SOURCE · YouTube @쏠제이 무인카페 · CC BY</div>'
            f'<div class="fr-overlay">FRAME {i+1:03d}/{n}</div>'
            f'{seekbar}'
            f'</div></div>', unsafe_allow_html=True
        )
    with v2:
        st.markdown('<div class="video-caption"><span class="video-tag-yolo">●</span> YOLO11-SEG + BYTETRACK</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="video-frame"><div class="video-wrap">'
            f'{img_html(frames_yolo[i], 380, ov, trails_map)}'
            f'<div class="src-overlay">{yolo_caption}</div>'
            f'<div class="fr-overlay">FRAME {i+1:03d}/{n}</div>'
            f'{seekbar}'
            f'</div></div>', unsafe_allow_html=True
        )


def render_zone_chart(stats, i: int, fps: float):
    sec = min(i // max(1, int(round(fps))), len(stats) - 1)
    zones_avg = stats[sec].get("zones_avg", {})
    if not zones_avg:
        return
    st.markdown('<div class="section-label">📈 구역별 평균 인원 분포</div>', unsafe_allow_html=True)
    df = pd.DataFrame({"zone": list(zones_avg.keys()), "count": list(zones_avg.values())})
    zone_map = mode_zone_colors()
    fig = go.Figure(go.Bar(
        x=df["zone"], y=df["count"],
        marker_color=[zone_map.get(z, "#888") for z in df["zone"]],
        text=[f"{v:.1f}" for v in df["count"]], textposition="outside",
    ))
    fig.update_layout(
        height=220, margin=dict(l=20, r=20, t=20, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E6E8EB", family="Pretendard"),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, showticklabels=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# LIVE TAB — self-looping fragment
# =============================================================================
def render_live_tab(frames_yolo, frames_raw, stats, tracking, insight):
    if not frames_yolo or not frames_raw:
        render_setup_guide()
        return

    # 디코딩 차이로 인한 프레임 수 불일치 방어
    n = min(len(frames_yolo), len(frames_raw))
    if len(frames_yolo) != len(frames_raw):
        st.warning(
            f"⚠️ 프레임 수 불일치: YOLO {len(frames_yolo)} vs RAW {len(frames_raw)}. "
            f"짧은 쪽({n})에 맞춰 재생합니다."
        )
    fps = tracking.get("fps", 15.0)

    @st.fragment
    def playback_fragment():
        # ── ADVANCE LOGIC (must come BEFORE slider widget) ──
        if st.session_state.playing and st.session_state.frame_scrub < n - 1:
            delay = BASE_DELAY / SPEED_MAP.get(st.session_state.speed_label, 1.0)
            time.sleep(delay)
            st.session_state.frame_scrub = min(st.session_state.frame_scrub + 1, n - 1)
            if st.session_state.frame_scrub >= n - 1:
                st.session_state.playing = False

        # ── UI ──
        render_control_row(n)

        st.slider(
            "프레임 탐색 (Q&A용)", 0, n - 1,
            key="frame_scrub", label_visibility="collapsed",
            on_change=on_scrub,
        )

        i = st.session_state.frame_scrub

        trails_map = None
        if st.session_state.trails:
            series = get_track_series(json.dumps(tracking["rows"]))
            trails_map = build_trails(series, i)

        render_video_pair(frames_raw, frames_yolo, i, n, trails_map)

        st.markdown('<div class="section-label major">📊 핵심 지표 · 실시간 집계</div>', unsafe_allow_html=True)
        st.markdown(kpis_html(tracking, i), unsafe_allow_html=True)

        st.markdown('<div class="section-label">🔬 분석 파이프라인</div>', unsafe_allow_html=True)
        stage_idx = 4 if (st.session_state.started and i >= n - 1 and not st.session_state.playing) \
                      else min(3, 1 + i // max(1, n // 3))
        st.markdown(stage_log_html(stage_idx), unsafe_allow_html=True)

        pct = (i + 1) / n
        if i >= n - 1 and not st.session_state.playing:
            progress_text = "✅ 분석 완료 · LLM 인사이트 생성 완료"
        elif st.session_state.playing:
            progress_text = f"🔄 프레임 분석 중 · {i+1}/{n} · {int(pct*100)}%"
        else:
            progress_text = f"⏸ 일시정지 · {i+1}/{n} · {int(pct*100)}%"
        st.progress(pct, text=progress_text)

        render_zone_chart(stats, i, fps)

        # ── 완료 시 미세 셀레브레이션 (한 번만) ──
        complete = st.session_state.started and i >= n - 1 and not st.session_state.playing
        if complete and not st.session_state.celebration_played:
            st.markdown(celebration_html(), unsafe_allow_html=True)
            st.session_state.celebration_played = True
        elif not complete:
            st.session_state.celebration_played = False

        # ── 인사이트 (재생 완료 시에만 — fragment 내부여야 자동 등장) ──
        if complete:
            st.markdown('<div class="section-label major">🤖 AI 행동 지침</div>', unsafe_allow_html=True)
            render_insight_block(insight)

        # ── SELF-LOOP ──
        if st.session_state.playing:
            st.rerun(scope="fragment")

    playback_fragment()


# =============================================================================
# SIMULATION & TRACKING TABS
# =============================================================================
def simulate_24h(peak_avg: float) -> pd.DataFrame:
    hours = list(range(7, 23))
    shape = np.array([0.2, 0.3, 0.45, 0.6, 0.85, 1.0, 0.95, 0.7,
                      0.55, 0.6, 0.7, 0.8, 0.75, 0.55, 0.35, 0.2])
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 0.05, size=len(shape))
    counts = np.clip((shape + noise) * max(6, peak_avg * 3), 0, None)
    dwell = np.clip(shape * 35 + rng.normal(0, 4, size=len(shape)), 10, 90)
    return pd.DataFrame({
        "hour": [f"{h:02d}:00" for h in hours],
        "avg_visitors": counts.round(1),
        "avg_dwell_min": dwell.round(1),
    })


def styled_fig(fig, height=340):
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E6E8EB", family="Pretendard"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        margin=dict(l=20, r=20, t=40, b=40),
    )
    return fig


def render_sim_tab(tracking):
    st.markdown('<div class="section-label">📈 24시간 운영 패턴 시뮬레이션</div>', unsafe_allow_html=True)
    st.caption("13초 실측 데이터 기반 · numpy 확률분포로 하루치 패턴 생성 (seed=42)")
    peak_avg = sum(tracking["per_frame_count"]) / max(1, len(tracking["per_frame_count"]))
    df = simulate_24h(peak_avg)
    acc, sec = mode_colors()
    acc_rgb = _hex_to_rgb(acc)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(df, x="hour", y="avg_visitors",
                     color="avg_visitors",
                     color_continuous_scale=[[0, "#4F8BF9"], [1, acc]])
        fig.update_layout(title=dict(text="시간대별 평균 방문객", font=dict(size=14)),
                          coloraxis_showscale=False)
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    with c2:
        fig = go.Figure(go.Scatter(
            x=df["hour"], y=df["avg_dwell_min"], mode="lines+markers",
            line=dict(color=acc, width=3),
            marker=dict(size=8, color=sec, line=dict(color=acc, width=2)),
            fill="tozeroy", fillcolor=f"rgba({acc_rgb},0.1)",
        ))
        fig.update_layout(title=dict(text="시간대별 평균 체류시간 (분)", font=dict(size=14)))
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_tracking_tab(tracking):
    st.markdown('<div class="section-label">👤 추적 ID별 구역 체류시간</div>', unsafe_allow_html=True)
    dwell = tracking["dwell_seconds_by_track"]
    if not dwell:
        st.info("추적된 인원이 없습니다.")
        return
    rows = []
    for tid, zmap in dwell.items():
        for zone, sec in zmap.items():
            rows.append({"track_id": f"Person #{tid}", "zone": zone, "seconds": sec})
    df = pd.DataFrame(rows)
    fig = px.bar(df, x="track_id", y="seconds", color="zone", barmode="stack",
                 color_discrete_map=mode_zone_colors())
    fig.update_layout(title=dict(text="누적 체류시간 분포 (초)", font=dict(size=14)))
    st.plotly_chart(styled_fig(fig, 400), use_container_width=True)

    st.markdown('<div class="section-label">🗺 누적 위치 히트맵</div>', unsafe_allow_html=True)
    rows_xy = tracking["rows"]
    if rows_xy:
        df_heat = pd.DataFrame([{"cx": r["center"][0], "cy": r["center"][1]} for r in rows_xy])
        fig = px.density_heatmap(df_heat, x="cx", y="cy", nbinsx=18, nbinsy=20,
                                 color_continuous_scale="Inferno")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(styled_fig(fig, 420), use_container_width=True)


# =============================================================================
# MAIN
# =============================================================================
def main():
    init_state()
    inject_css()
    render_navbar()
    inject_chrome()
    inject_slider_recolor()      # A/B 모드에서 slider 오렌지 잔재를 accent 로 치환
    inject_emoji_strip()         # B 모드에서 이모지/재생 기호 제거

    frames_yolo, frames_raw, stats, tracking, zone_stats, insight = load_artifacts()
    render_sidebar(len(frames_yolo))

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔴 실시간 분석", "📊 24시간 시뮬레이션", "👤 체류시간 추적", "🎓 작동 원리"
    ])
    with tab1:
        render_live_tab(frames_yolo, frames_raw, stats, tracking, insight)
    with tab2:
        render_sim_tab(tracking)
    with tab3:
        render_tracking_tab(tracking)
    with tab4:
        render_tech_tab()

    render_footer()


if __name__ == "__main__":
    main()

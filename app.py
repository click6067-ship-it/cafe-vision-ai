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

ROOT = Path(__file__).parent
DATA = ROOT / "data"

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
# CSS
# =============================================================================
CUSTOM_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css');
html, body, [class*="css"] { font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif; }
.main .block-container { padding-top: 72px !important; padding-bottom: 3rem; max-width: 1400px; }

/* Navbar: fixed at viewport top, ALWAYS full-width. Sidebar lives below us.
   pointer-events:none — navbar is decorative, clicks pass through to tabs above (z 2000). */
.navbar {
    position: fixed; top: 0; left: 0; right: 0;
    z-index: 1000;
    height: 56px; display: flex; align-items: center; gap: 14px;
    padding: 0 22px;
    margin: 0;
    background: rgba(11,14,20,0.85);
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    border: none; border-bottom: 1px solid rgba(255,255,255,0.08);
    border-radius: 0;
    box-shadow: 0 6px 24px rgba(0,0,0,0.3);
    pointer-events: none;
}
.navbar > * { pointer-events: auto; }  /* restore for individual decorative items */
.navbar::after {
    content: ''; position: absolute; left: 0; right: 0; bottom: -14px; height: 14px;
    background: linear-gradient(180deg, rgba(11,14,20,0.35), transparent);
    pointer-events: none;
}

/* Sidebar pushed BELOW navbar — no more horizontal overlap with navbar */
section[data-testid="stSidebar"] {
    top: 56px !important;
    height: calc(100vh - 56px) !important;
    z-index: 900 !important;
}
.navbar-logo {
    width: 30px; height: 30px; border-radius: 8px;
    background: linear-gradient(135deg, #FF6B35 0%, #FFC857 100%);
    display: flex; align-items: center; justify-content: center;
    color: #0B0E14; font-weight: 800; font-size: 12px; letter-spacing: -0.02em;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(255,107,53,0.35);
}
.navbar-brand {
    font-size: 14px; font-weight: 700; color: #F5F6F8;
    letter-spacing: -0.01em; margin-right: 8px; flex-shrink: 0;
}
.navbar-spacer { flex: 1; min-width: 0; }
.live-badge {
    background: #FF3B3B; color: white; font-size: 10px; font-weight: 700;
    padding: 5px 10px; border-radius: 6px; letter-spacing: 0.06em;
    display: inline-flex; align-items: center; gap: 5px; animation: pulse 1.8s infinite;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(255,59,59,0.4);
}
.live-dot { width: 6px; height: 6px; background: white; border-radius: 50%; }
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.55 } }

/* Top-level st.tabs: fixed in navbar band, centered.
   Strategy: tab-list spans full width + pointer-events:none, individual tab buttons re-enable auto.
   No transform → no new stacking context competing with navbar. */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    position: fixed !important;
    top: 10px !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 2147483647 !important;   /* max — nothing ever above */
    background: transparent !important;
    border-bottom: none !important;
    padding: 0 !important;
    gap: 6px !important;
    justify-content: center !important;
    display: flex !important;
    flex-wrap: nowrap;
    pointer-events: none !important;  /* empty space passes clicks through */
}
/* The tab buttons themselves receive clicks */
[data-testid="stTabs"] button[role="tab"] {
    pointer-events: auto !important;
    cursor: pointer !important;
    position: relative;
    z-index: 1;
}
[data-testid="stTabs"] button[role="tab"] * { pointer-events: auto !important; }
[data-testid="stTabs"] button[role="tab"] {
    font-size: 12.5px !important; font-weight: 600 !important;
    padding: 6px 14px !important; min-height: 36px !important;
    border-radius: 8px !important; color: #A0A7B4 !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    background: rgba(255,255,255,0.06) !important;
    color: #F5F6F8 !important;
    border-color: rgba(255,255,255,0.08) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(255,107,53,0.22), rgba(255,200,87,0.12)) !important;
    color: #FFC857 !important;
    border-color: rgba(255,107,53,0.32) !important;
    box-shadow: 0 2px 10px rgba(255,107,53,0.18) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

/* Nested tabs inside any tab-panel: reset to default positioned style */
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
    position: static !important;
    top: auto !important; left: auto !important; right: auto !important;
    transform: none !important;
    max-width: none !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    background: revert !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    justify-content: flex-start !important;
    padding: 0 !important;
    z-index: auto !important;
    pointer-events: auto !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    border: none !important;
    color: #A0A7B4 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    min-height: unset !important;
    padding: 10px 14px !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: transparent !important;
    color: #FFC857 !important;
    border-bottom: 2px solid #FF6B35 !important;
}

@media (max-width: 900px) {
    .navbar { padding: 0 14px; }
    .navbar-brand { display: none; }
}

.section-label {
    font-size: 11px; font-weight: 600; letter-spacing: 0.12em;
    color: #8B95A5; text-transform: uppercase; margin: 14px 0 8px 0;
}
.section-label.major {
    font-size: 13px; font-weight: 700; letter-spacing: 0.14em;
    color: #C0C6D2;
}

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 6px 0 16px 0; }
.kpi {
    background: #151A24; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; padding: 16px 18px; transition: transform 0.2s, border-color 0.2s;
}
.kpi:hover { transform: translateY(-2px); border-color: rgba(255,107,53,0.4); }
.kpi-label { font-size: 11px; font-weight: 600; color: #8B95A5; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #F5F6F8; line-height: 1.1; }
.kpi-unit { font-size: 13px; color: #8B95A5; margin-left: 4px; }
.kpi-trend { font-size: 12px; margin-top: 6px; font-weight: 500; }
.trend-up { color: #23C552; }
.trend-down { color: #FF6B6B; }
.trend-neutral { color: #8B95A5; }

.video-frame {
    background: #0E1118; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 10px; overflow: hidden;
}
.video-caption {
    font-size: 11px; font-weight: 700; color: #A0A7B4;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
}
.video-tag-raw { color: #8B95A5; }
.video-tag-yolo { color: #FF6B35; }
.video-frame img { border-radius: 8px; width: 100%; display: block; }
.video-wrap { position: relative; border-radius: 8px; overflow: hidden; }
.src-overlay {
    position: absolute; left: 8px; bottom: 8px;
    background: rgba(11,14,20,0.82); backdrop-filter: blur(4px);
    color: #E6E8EB; font-size: 10px; font-weight: 600; letter-spacing: 0.06em;
    padding: 4px 8px; border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.1); text-transform: uppercase;
}
.fr-overlay {
    position: absolute; right: 8px; top: 8px;
    background: rgba(255,107,53,0.85); color: #0B0E14;
    font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
    padding: 3px 7px; border-radius: 5px;
    font-family: 'JetBrains Mono', monospace;
}
.video-seekbar {
    position: absolute; left: 0; right: 0; bottom: 0;
    height: 3px; background: rgba(0,0,0,0.3);
}
.video-seekbar-fill {
    height: 100%; background: linear-gradient(90deg, #FF6B35 0%, #FFC857 100%);
    box-shadow: 0 0 6px rgba(255,107,53,0.6);
    transition: width 0.15s linear;
}

.status-bar {
    background: #151A24; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 10px 14px; margin: 4px 0 10px 0;
    color: #8B95A5; font-size: 13px;
}

/* === Apple-style Plotly chart entrance animations (run on tab-switch render) === */
/* Container barely-visible fade so the SVG shows as it animates */
div[data-testid="stPlotlyChart"] { animation: chartFade 0.35s ease-out both; }
@keyframes chartFade { from { opacity: 0 } to { opacity: 1 } }

/* BAR chart: each bar scales from 0 height at the bottom (Apple-style "rise") */
div[data-testid="stPlotlyChart"] svg.main-svg g.trace.bars g.point,
div[data-testid="stPlotlyChart"] svg.main-svg .barlayer g.trace g.point {
    transform-box: fill-box;
    transform-origin: 50% 100%;
    animation: barRise 1.05s cubic-bezier(0.22, 1.08, 0.32, 1) both;
}
@keyframes barRise {
    0%   { transform: scaleY(0); opacity: 0.15; }
    55%  { opacity: 1; }
    100% { transform: scaleY(1); opacity: 1; }
}
/* Stagger bars L→R (covers up to ~30 bars) */
svg.main-svg g.trace.bars g.point:nth-child(1) { animation-delay: 0ms; }
svg.main-svg g.trace.bars g.point:nth-child(2) { animation-delay: 55ms; }
svg.main-svg g.trace.bars g.point:nth-child(3) { animation-delay: 110ms; }
svg.main-svg g.trace.bars g.point:nth-child(4) { animation-delay: 165ms; }
svg.main-svg g.trace.bars g.point:nth-child(5) { animation-delay: 220ms; }
svg.main-svg g.trace.bars g.point:nth-child(6) { animation-delay: 275ms; }
svg.main-svg g.trace.bars g.point:nth-child(7) { animation-delay: 330ms; }
svg.main-svg g.trace.bars g.point:nth-child(8) { animation-delay: 385ms; }
svg.main-svg g.trace.bars g.point:nth-child(9) { animation-delay: 440ms; }
svg.main-svg g.trace.bars g.point:nth-child(10) { animation-delay: 495ms; }
svg.main-svg g.trace.bars g.point:nth-child(11) { animation-delay: 550ms; }
svg.main-svg g.trace.bars g.point:nth-child(12) { animation-delay: 605ms; }
svg.main-svg g.trace.bars g.point:nth-child(13) { animation-delay: 660ms; }
svg.main-svg g.trace.bars g.point:nth-child(14) { animation-delay: 715ms; }
svg.main-svg g.trace.bars g.point:nth-child(15) { animation-delay: 770ms; }
svg.main-svg g.trace.bars g.point:nth-child(16) { animation-delay: 825ms; }
svg.main-svg g.trace.bars g.point:nth-child(17) { animation-delay: 860ms; }
svg.main-svg g.trace.bars g.point:nth-child(18) { animation-delay: 895ms; }
svg.main-svg g.trace.bars g.point:nth-child(19) { animation-delay: 930ms; }
svg.main-svg g.trace.bars g.point:nth-child(20) { animation-delay: 965ms; }
svg.main-svg g.trace.bars g.point:nth-child(n+21) { animation-delay: 1000ms; }

/* LINE chart: draw stroke left→right */
div[data-testid="stPlotlyChart"] svg.main-svg g.trace.scatter path.js-line,
div[data-testid="stPlotlyChart"] svg.main-svg .scatterlayer g.trace > path.js-fill,
div[data-testid="stPlotlyChart"] svg.main-svg .scatterlayer g.trace > path.js-line {
    stroke-dasharray: 3000;
    stroke-dashoffset: 3000;
    animation: lineDraw 1.6s cubic-bezier(0.22, 1, 0.36, 1) 0.25s forwards;
}
@keyframes lineDraw {
    to { stroke-dashoffset: 0; }
}
/* Scatter line markers fade in after line draws */
div[data-testid="stPlotlyChart"] svg.main-svg g.trace.scatter g.points path {
    opacity: 0;
    animation: markerFade 0.4s ease-out 1.5s forwards;
}
@keyframes markerFade {
    to { opacity: 1; }
}

/* HEATMAP / density: fade + subtle scale */
div[data-testid="stPlotlyChart"] svg.main-svg g.trace.heatmap,
div[data-testid="stPlotlyChart"] svg.main-svg .heatmaplayer {
    transform-box: fill-box;
    transform-origin: 50% 50%;
    animation: heatmapFade 0.9s cubic-bezier(0.22, 1, 0.36, 1) 0.15s both;
}
@keyframes heatmapFade {
    from { opacity: 0; transform: scale(0.97); }
    to   { opacity: 1; transform: scale(1); }
}

/* DataFrame: fade after charts */
div[data-testid="stDataFrame"],
div[data-testid="stDataFrameResizable"] {
    animation: dfFade 0.55s ease-out 0.5s both;
}
@keyframes dfFade {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.celebration {
    position: relative; width: 100%; height: 0;
    pointer-events: none; overflow: visible;
}
.particle {
    position: absolute; border-radius: 50%;
    top: -6px; left: 50%;
    opacity: 0; will-change: transform, opacity;
    animation: particleRise 1.9s cubic-bezier(0.2, 0.7, 0.3, 1) forwards;
    animation-delay: var(--delay, 0s);
    box-shadow: 0 0 10px currentColor;
}
@keyframes particleRise {
    0%   { transform: translate(-50%, 8px) scale(0.4); opacity: 0; }
    15%  { opacity: 1; }
    70%  { opacity: 0.85; }
    100% { transform: translate(calc(-50% + var(--tx)), var(--ty)) scale(0.2); opacity: 0; }
}

.insight {
    background: linear-gradient(135deg, #151A24 0%, #1A2233 100%);
    border: 1px solid rgba(255,107,53,0.25);
    border-radius: 16px; padding: 22px 26px; margin-top: 18px;
    animation: fadeInUp 0.6s ease-out;
}
.action-row {
    animation: fadeInUp 0.5s ease-out backwards;
}
.action-row:nth-child(2) { animation-delay: 0.15s; }
.action-row:nth-child(3) { animation-delay: 0.3s; }
.action-row:nth-child(4) { animation-delay: 0.45s; }
.insight-head { display: flex; align-items: center; gap: 8px;
    font-size: 11px; font-weight: 700; color: #FF6B35;
    letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 12px; }
.insight-title { font-size: 20px; font-weight: 700; color: #F5F6F8; margin: 0 0 16px 0; line-height: 1.4; }
.action-row { display: flex; gap: 12px; padding: 14px 16px;
    background: rgba(255,255,255,0.03); border-radius: 10px;
    margin-bottom: 8px; align-items: flex-start; }
.priority-badge { font-size: 10px; font-weight: 700; padding: 4px 9px;
    border-radius: 6px; letter-spacing: 0.06em; flex-shrink: 0; margin-top: 2px; }
.pri-urgent { background: rgba(255,59,59,0.2); color: #FF6B6B; border: 1px solid rgba(255,59,59,0.3); }
.pri-improve { background: rgba(255,185,0,0.15); color: #FFC857; border: 1px solid rgba(255,185,0,0.25); }
.pri-optimize { background: rgba(35,197,82,0.15); color: #4ADE80; border: 1px solid rgba(35,197,82,0.25); }
.action-text { color: #E0E4EA; font-size: 14px; line-height: 1.55; }
.action-impact { color: #8B95A5; font-size: 12px; margin-top: 4px; }
.insight-summary {
    margin-top: 14px; padding: 12px 14px;
    background: rgba(79,139,249,0.08); border-left: 3px solid #4F8BF9;
    border-radius: 6px; color: #C0C6D2; font-size: 13px; line-height: 1.6;
}

.log-panel {
    background: #0A0D13; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 12px 14px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px; color: #7FE5BA; min-height: 110px; max-height: 160px; overflow-y: auto;
}
.log-line { display: block; margin: 2px 0; }
.log-time { color: #5B6577; margin-right: 8px; }
.log-stage { color: #FF6B35; font-weight: 600; margin-right: 6px; }

div[data-testid="stProgress"] > div { background: #1A1F2E; }
div[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, #FF6B35 0%, #FFC857 100%);
}

.footer {
    margin-top: 32px; padding: 18px 22px;
    background: #0E1118; border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px; color: #6B7280; font-size: 11.5px; line-height: 1.7;
}
.footer-title { color: #8B95A5; font-weight: 700; font-size: 11px; letter-spacing: 0.1em; margin-bottom: 6px; }
.footer a { color: #8FB4D8; text-decoration: none; }
.footer a:hover { text-decoration: underline; }

.sb-footer {
    margin-top: 20px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.06);
    color: #6B7280; font-size: 10.5px; line-height: 1.6;
}

#MainMenu { visibility: hidden; }
/* Streamlit header: transparent, keep structure so toolbar buttons render */
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
}
/* Hide only Deploy + hamburger menu — NOT the whole toolbar (stExpandSidebarButton lives there) */
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stMainMenuButton"] { display: none !important; }
footer { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }

/* Sidebar re-open handle — thin vertical tab peeking out of the left edge (below navbar).
   Ref: Linear / Notion / ChatGPT pattern. Subtle idle, expands with icon on hover. */
button[data-testid="stExpandSidebarButton"] {
    position: fixed !important;
    top: 92px !important;
    left: 0 !important;
    z-index: 1001 !important;
    width: 16px !important;
    height: 64px !important;
    min-width: 0 !important;
    padding: 0 !important;
    background: linear-gradient(135deg, #FF6B35 0%, #FFC857 100%) !important;
    border: none !important;
    border-radius: 0 10px 10px 0 !important;
    box-shadow: 3px 0 14px rgba(255,107,53,0.4) !important;
    cursor: pointer !important;
    display: flex !important;
    visibility: visible !important; opacity: 1 !important;
    align-items: center !important; justify-content: center !important;
    overflow: hidden !important;
    animation: edgeHandlePulse 2.6s ease-in-out infinite !important;
    transition: width 0.22s cubic-bezier(0.25, 1, 0.5, 1),
                box-shadow 0.22s ease !important;
}
button[data-testid="stExpandSidebarButton"]:hover {
    width: 34px !important;
    box-shadow: 5px 0 22px rgba(255,107,53,0.7) !important;
    animation: none !important;
}
@keyframes edgeHandlePulse {
    0%, 100% { box-shadow: 2px 0 10px rgba(255,107,53,0.3); }
    50%      { box-shadow: 4px 0 18px rgba(255,107,53,0.7); }
}
/* Icon: hidden when collapsed, appears on hover */
button[data-testid="stExpandSidebarButton"] svg,
button[data-testid="stExpandSidebarButton"] path {
    color: #0B0E14 !important;
    fill: #0B0E14 !important;
    stroke: #0B0E14 !important;
    width: 16px !important; height: 16px !important;
    opacity: 0 !important;
    transition: opacity 0.2s !important;
}
button[data-testid="stExpandSidebarButton"]:hover svg,
button[data-testid="stExpandSidebarButton"]:hover path {
    opacity: 1 !important;
}
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


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
      <span class="live-badge"><span class="live-dot"></span>LIVE DEMO</span>
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
    fig = go.Figure(go.Bar(
        x=df["zone"], y=df["count"],
        marker_color=[ZONE_COLORS.get(z, "#888") for z in df["zone"]],
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
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(df, x="hour", y="avg_visitors",
                     color="avg_visitors",
                     color_continuous_scale=[[0, "#4F8BF9"], [1, "#FF6B35"]])
        fig.update_layout(title=dict(text="시간대별 평균 방문객", font=dict(size=14)),
                          coloraxis_showscale=False)
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    with c2:
        fig = go.Figure(go.Scatter(
            x=df["hour"], y=df["avg_dwell_min"], mode="lines+markers",
            line=dict(color="#FF6B35", width=3),
            marker=dict(size=8, color="#FFC857", line=dict(color="#FF6B35", width=2)),
            fill="tozeroy", fillcolor="rgba(255,107,53,0.1)",
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
                 color_discrete_map=ZONE_COLORS)
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

    frames_yolo, frames_raw, stats, tracking, zone_stats, insight = load_artifacts()
    render_sidebar(len(frames_yolo))

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔴 실시간 분석", "📊 24시간 시뮬레이션", "👤 추적 상세", "🎓 기술 원리"
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

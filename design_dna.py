"""
Design DNA CSS — 원본 design-dna-xai.md 의 규약을 Streamlit에 이식.

두 가지 모드를 지원:
  • Mode A (완전 통일): accent=cyan-400, secondary=amber-400
  • Mode B (같은 가족): accent=orange-400, secondary=yellow-400

CSS 커스텀 프로퍼티로 테마 토큰을 분리해서, 본체 스타일은 한 벌만 유지.
각 모드는 :root 변수만 다르게 주입.

핵심 이식 포인트:
  §1 배경 계층 (bg / card-bg / card-border / surface / divider)
  §1 텍스트 계층 (primary / body / muted / dim)
  §2 폰트 (Inter + JetBrains Mono) · 라벨은 uppercase tracking-widest
  §3 카드 (rounded-2xl + card-bg + border + accent glow)
  §3 섹션 라벨 (uppercase · accent · mb-5) — 디자인의 서명
  §3 버튼 (active: accent/15 + accent/30 border + glow / inactive: gray-800/60)
  §3 입력 (surface + rounded-xl + focus ring)
  §4 호버 (translateY(-2px) or scale + 글로우)
  §5 애니메이션 (fade-in 0.4s · pulse 1.5s · rotate · hover 0.15s)
  §6 글로우 (상시 0.08 / 호버 0.1~0.4)
  §7 레이아웃 (max-w-7xl · px-6 · space-y-8)
  §8 Home 버튼 (fixed · squircle · glass + rotating conic-gradient border)
"""

from __future__ import annotations


# =============================================================================
# MODE VARIABLES
# =============================================================================
_VARS_A = """
:root {
  /* Mode A · Original (cyan / amber) */
  --accent:         #22d3ee;           /* cyan-400  · 제목/활성 라벨 */
  --accent-bright:  #67e8f9;           /* cyan-300  · 활성 버튼 텍스트 */
  --accent-deep:    #06b6d4;           /* cyan-500  · 히트맵/호버 */
  --accent-rgb:     6, 182, 212;
  --accent-light-rgb: 34, 211, 238;

  --secondary:      #fbbf24;           /* amber-400 · 결과값/강조 수치 */
  --secondary-rgb:  251, 191, 36;
  --secondary-deep: #b45309;           /* amber-800 · 보조 카드 액센트 */
}
"""

_VARS_B = """
:root {
  /* Mode B · 같은 가족 (orange / yellow) */
  --accent:         #fb923c;           /* orange-400 */
  --accent-bright:  #fdba74;           /* orange-300 */
  --accent-deep:    #f97316;           /* orange-500 */
  --accent-rgb:     249, 115, 22;
  --accent-light-rgb: 251, 146, 60;

  --secondary:      #facc15;           /* yellow-400 */
  --secondary-rgb:  250, 204, 21;
  --secondary-deep: #a16207;           /* yellow-700 */
}
"""


# =============================================================================
# DNA BODY  (공통 본체 — Mode A/B 가 공유)
# =============================================================================
_BODY = r"""
/* ─────────────────────────────────────────────────────────
   DNA §1 · 공용 토큰 · 배경 / 텍스트 / 시맨틱
   ───────────────────────────────────────────────────────── */
:root {
  /* 배경 계층 */
  --bg:           #030712;
  --card-bg:      rgba(17,24,39,0.40);
  --card-border:  rgba(31,41,55,0.60);
  --surface:      rgba(31,41,55,0.80);
  --surface-solid:#111827;
  --divider:      rgba(31,41,55,0.60);

  /* 텍스트 계층 */
  --text-primary: #e5e7eb;
  --text-body:    #9ca3af;
  --text-muted:   #6b7280;
  --text-dim:     #4b5563;

  /* 시맨틱 (고정) */
  --success: #34d399;
  --warning: #fbbf24;
  --danger:  #f87171;
  --info:    var(--accent);

  /* 라운드 스케일 */
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;   /* rounded-2xl — 메인 카드 */
  --r-xl: 20px;

  /* 글로우 프리셋 */
  --glow-card:    0 0 20px rgba(var(--accent-rgb), 0.08);
  --glow-hover:   0 0 14px rgba(var(--accent-rgb), 0.35);
  --glow-premium: 0 0 30px rgba(var(--accent-rgb), 0.12),
                  0 8px 32px rgba(0,0,0,0.45);
}

/* ─────────────────────────────────────────────────────────
   DNA §2 · 폰트
   ───────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
  background: var(--bg) !important;
  color: var(--text-primary);
}
.stApp { background: var(--bg) !important; }
code, pre, kbd, samp, .mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace !important;
}

/* 전역 base */
.main .block-container {
  padding-top: 82px !important;
  padding-bottom: 3rem;
  max-width: 1280px;   /* §7 max-w-7xl */
}

/* ─────────────────────────────────────────────────────────
   스크롤바 (§1)
   ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #0a0f1a; }
::-webkit-scrollbar-thumb {
  background: #374151;
  border-radius: 5px;
  border: 2px solid #0a0f1a;
}
::-webkit-scrollbar-thumb:hover { background: #4b5563; }
* { scrollbar-color: #374151 #0a0f1a; scrollbar-width: thin; }

/* Streamlit 내장 toolbar / 메뉴 정리 */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stMainMenuButton"] { display: none !important; }
footer { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }

/* ─────────────────────────────────────────────────────────
   NAVBAR (상단 바 — DNA 카드와 같은 유리 표면)
   ───────────────────────────────────────────────────────── */
.navbar {
  position: fixed; top: 0; left: 0; right: 0;
  z-index: 1000;
  height: 62px;
  display: flex; align-items: center; gap: 16px;
  padding: 0 24px;
  background: rgba(3,7,18,0.78);
  backdrop-filter: blur(18px) saturate(1.4);
  -webkit-backdrop-filter: blur(18px) saturate(1.4);
  border-bottom: 1px solid var(--divider);
  box-shadow: 0 1px 0 rgba(255,255,255,0.02), 0 6px 24px rgba(0,0,0,0.35);
  pointer-events: none;
}
.navbar > * { pointer-events: auto; }

.navbar-logo {
  width: 32px; height: 32px;
  border-radius: var(--r-sm);
  background: linear-gradient(135deg, var(--accent) 0%, var(--secondary) 100%);
  display: flex; align-items: center; justify-content: center;
  color: #030712; font-weight: 800; font-size: 12px; letter-spacing: -0.02em;
  flex-shrink: 0;
  box-shadow: 0 0 16px rgba(var(--accent-rgb), 0.35);
}
.navbar-brand {
  font-family: 'Inter', sans-serif;
  font-size: 14px; font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  margin-right: 10px; flex-shrink: 0;
}
.navbar-spacer { flex: 1; min-width: 0; }

/* LIVE 뱃지 — pulse 1.5s (§5) */
.live-badge {
  background: rgba(var(--accent-rgb), 0.15);
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 700;
  padding: 5px 10px;
  border-radius: var(--r-sm);
  letter-spacing: 0.12em; text-transform: uppercase;
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid rgba(var(--accent-rgb), 0.30);
  box-shadow: 0 0 10px rgba(var(--accent-rgb), 0.20);
  flex-shrink: 0;
}
.live-dot {
  width: 6px; height: 6px; background: var(--accent); border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
  box-shadow: 0 0 6px currentColor;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50%      { opacity: 1;   }
}

@media (max-width: 900px) {
  .navbar { padding: 0 14px; }
  .navbar-brand { display: none; }
}

/* Sidebar 를 navbar 아래로 */
section[data-testid="stSidebar"] {
  top: 62px !important;
  height: calc(100vh - 62px) !important;
  background: var(--bg) !important;
  border-right: 1px solid var(--divider);
  z-index: 900 !important;
}

/* ─────────────────────────────────────────────────────────
   탭 (상단, navbar 영역에 고정)
   ───────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  position: fixed !important;
  top: 14px !important;
  left: 0 !important;
  right: 0 !important;
  z-index: 2147483647 !important;     /* 최상위 — 어떤 요소도 탭 위에 올라오지 않음 */
  background: transparent !important;
  border-bottom: none !important;
  padding: 0 !important;
  gap: 6px !important;
  justify-content: center !important;
  display: flex !important;
  flex-wrap: nowrap;
  pointer-events: none !important;     /* 빈 공간은 클릭 통과 → Home/스위처/navbar 클릭 가능 */
}
[data-testid="stTabs"] button[role="tab"] {
  pointer-events: auto !important;
  cursor: pointer !important;
  position: relative; z-index: 1;
  font-family: 'Inter', sans-serif !important;
  font-size: 12.5px !important; font-weight: 600 !important;
  padding: 7px 16px !important;
  min-height: 34px !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  background: rgba(31,41,55,0.40) !important;
  border: 1px solid rgba(31,41,55,0.50) !important;
  transition: all 0.18s ease !important;
  letter-spacing: -0.005em;
}
[data-testid="stTabs"] button[role="tab"] * { pointer-events: auto !important; }
[data-testid="stTabs"] button[role="tab"]:hover {
  background: rgba(55,65,81,0.50) !important;
  color: var(--text-primary) !important;
  border-color: rgba(75,85,99,0.60) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: rgba(var(--accent-rgb), 0.15) !important;
  color: var(--accent-bright) !important;
  border-color: rgba(var(--accent-rgb), 0.30) !important;
  box-shadow: 0 0 12px rgba(var(--accent-rgb), 0.20) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

/* 중첩 탭 (탭 패널 내부) — 하단 언더라인 스타일 */
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
  position: static !important;
  top: auto !important; left: auto !important; right: auto !important;
  transform: none !important;
  max-width: none !important;
  margin-top: 0 !important; margin-bottom: 10px !important;
  background: revert !important;
  border-bottom: 1px solid var(--divider) !important;
  justify-content: flex-start !important;
  padding: 0 !important;
  z-index: auto !important;
  pointer-events: auto !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] button[role="tab"] {
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  color: var(--text-muted) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  min-height: unset !important;
  padding: 10px 14px !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: transparent !important;
  color: var(--accent-bright) !important;
  border-bottom: 2px solid var(--accent) !important;
  box-shadow: none !important;
}

/* ─────────────────────────────────────────────────────────
   §3 · 섹션 라벨 — 디자인의 서명
   ───────────────────────────────────────────────────────── */
.section-label {
  font-family: 'Inter', sans-serif;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.16em !important;      /* tracking-widest */
  text-transform: uppercase !important;
  color: var(--accent) !important;
  margin: 18px 0 20px 0 !important;        /* mb-5 */
  filter: drop-shadow(0 0 8px rgba(var(--accent-rgb), 0.25));
}
.section-label.major {
  font-size: 13px !important;
  letter-spacing: 0.18em !important;
  font-weight: 700 !important;
  color: var(--accent-bright) !important;
}

/* ─────────────────────────────────────────────────────────
   §3 · KPI 카드
   ───────────────────────────────────────────────────────── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 6px 0 18px 0;
}
.kpi {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-lg);
  padding: 20px 22px;
  box-shadow: var(--glow-card);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  animation: fadeIn 0.4s ease-out both;
  position: relative;
  overflow: hidden;
}
.kpi::before {
  /* 미세 상단 하이라이트 */
  content: '';
  position: absolute; left: 0; right: 0; top: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(var(--accent-rgb), 0.35), transparent);
  opacity: 0.7;
}
.kpi:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--accent-rgb), 0.40);
  box-shadow: 0 0 24px rgba(var(--accent-rgb), 0.18),
              0 8px 24px rgba(0,0,0,0.35);
}
.kpi-label {
  font-family: 'Inter', sans-serif;
  font-size: 11px; font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 10px;
}
.kpi-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 30px; font-weight: 700;
  color: var(--secondary);
  line-height: 1.05;
  letter-spacing: -0.01em;
}
.kpi-unit {
  font-family: 'Inter', sans-serif;
  font-size: 13px; font-weight: 500;
  color: var(--text-muted);
  margin-left: 5px;
}
.kpi-trend {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; margin-top: 8px; font-weight: 500;
}
.trend-up      { color: var(--success); }
.trend-down    { color: var(--danger); }
.trend-neutral { color: var(--text-muted); }

/* 스파크라인은 각 KPI 의 의미색(파랑/노랑/연파랑/혼잡도) 을 그대로 사용.
   모드 통일보다 정보 가독성이 우선 — stroke 는 Python 에서 주입한 색 유지 */
.kpi svg polyline {
  filter: drop-shadow(0 0 4px rgba(var(--accent-rgb), 0.12));
}

/* ─────────────────────────────────────────────────────────
   §3 · 영상 프레임 카드
   ───────────────────────────────────────────────────────── */
.video-frame {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-lg);
  padding: 12px;
  overflow: hidden;
  box-shadow: var(--glow-card);
  animation: fadeIn 0.4s ease-out both;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.video-frame:hover {
  border-color: rgba(var(--accent-rgb), 0.35);
  box-shadow: 0 0 22px rgba(var(--accent-rgb), 0.15),
              0 6px 20px rgba(0,0,0,0.35);
}
.video-caption {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 600;
  color: var(--text-body);
  letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 10px;
  display: flex; align-items: center; gap: 8px;
}
.video-tag-raw  { color: var(--text-muted); }
.video-tag-yolo { color: var(--accent); filter: drop-shadow(0 0 4px rgba(var(--accent-rgb), 0.5)); }
.video-frame img {
  border-radius: var(--r-md);
  width: 100%; display: block;
}
.video-wrap {
  position: relative;
  border-radius: var(--r-md);
  overflow: hidden;
}
.src-overlay {
  position: absolute; left: 10px; bottom: 10px;
  background: rgba(3,7,18,0.85);
  backdrop-filter: blur(6px);
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
  padding: 5px 10px;
  border-radius: var(--r-sm);
  border: 1px solid var(--card-border);
  text-transform: uppercase;
}
.fr-overlay {
  position: absolute; right: 10px; top: 10px;
  background: rgba(var(--accent-rgb), 0.90);
  color: #030712;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
  padding: 4px 8px;
  border-radius: var(--r-sm);
  box-shadow: 0 0 10px rgba(var(--accent-rgb), 0.4);
}
.video-seekbar {
  position: absolute; left: 0; right: 0; bottom: 0;
  height: 3px; background: rgba(0,0,0,0.35);
}
.video-seekbar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent) 0%, var(--secondary) 100%);
  box-shadow: 0 0 8px rgba(var(--accent-rgb), 0.7);
  transition: width 0.15s linear;
}

/* ─────────────────────────────────────────────────────────
   Status bar / log panel
   ───────────────────────────────────────────────────────── */
.status-bar {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-md);
  padding: 11px 16px;
  margin: 4px 0 10px 0;
  color: var(--text-body);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12.5px;
  box-shadow: var(--glow-card);
  animation: fadeIn 0.35s ease-out both;
}
.status-bar b { color: var(--secondary); font-weight: 600; }

.log-panel {
  background: rgba(3,7,18,0.65);
  border: 1px solid var(--card-border);
  border-radius: var(--r-md);
  padding: 14px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--success);
  min-height: 110px; max-height: 170px; overflow-y: auto;
  box-shadow: inset 0 0 16px rgba(var(--accent-rgb), 0.04);
}
.log-line { display: block; margin: 3px 0; }
.log-time { color: var(--text-dim); margin-right: 10px; }
.log-stage {
  color: var(--accent);
  font-weight: 600;
  margin-right: 8px;
  filter: drop-shadow(0 0 4px rgba(var(--accent-rgb), 0.3));
}

/* ─────────────────────────────────────────────────────────
   인사이트 카드 — 프리미엄 글로우
   ───────────────────────────────────────────────────────── */
.insight {
  background: linear-gradient(135deg,
    rgba(17,24,39,0.50) 0%,
    rgba(var(--accent-rgb), 0.04) 100%);
  border: 1px solid rgba(var(--accent-rgb), 0.25);
  border-radius: var(--r-lg);
  padding: 24px 28px; margin-top: 20px;
  box-shadow: var(--glow-premium);
  animation: fadeInUp 0.6s ease-out;
}
.insight-head {
  display: flex; align-items: center; gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 14px;
}
.insight-title {
  font-family: 'Inter', sans-serif;
  font-size: 20px; font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 18px 0; line-height: 1.4;
  letter-spacing: -0.01em;
}
.action-row {
  display: flex; gap: 12px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--r-md);
  margin-bottom: 8px;
  align-items: flex-start;
  transition: border-color 0.2s ease, background 0.2s ease;
  animation: fadeInUp 0.5s ease-out backwards;
}
.action-row:hover {
  border-color: rgba(var(--accent-rgb), 0.20);
  background: rgba(255,255,255,0.04);
}
.action-row:nth-child(2) { animation-delay: 0.15s; }
.action-row:nth-child(3) { animation-delay: 0.30s; }
.action-row:nth-child(4) { animation-delay: 0.45s; }
.priority-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 700;
  padding: 4px 9px;
  border-radius: var(--r-sm);
  letter-spacing: 0.08em;
  flex-shrink: 0; margin-top: 2px;
}
.pri-urgent   { background: rgba(248,113,113,0.15); color: var(--danger);  border: 1px solid rgba(248,113,113,0.30); }
.pri-improve  { background: rgba(var(--secondary-rgb),0.15); color: var(--secondary); border: 1px solid rgba(var(--secondary-rgb),0.30); }
.pri-optimize { background: rgba(52,211,153,0.15); color: var(--success); border: 1px solid rgba(52,211,153,0.30); }

.action-text   { color: var(--text-primary); font-size: 14px; line-height: 1.55; }
.action-impact { color: var(--text-muted); font-size: 12px; margin-top: 4px; font-family: 'JetBrains Mono', monospace; }
.insight-summary {
  margin-top: 14px; padding: 14px 16px;
  background: rgba(var(--accent-rgb), 0.06);
  border-left: 3px solid var(--accent);
  border-radius: var(--r-sm);
  color: var(--text-body);
  font-size: 13px; line-height: 1.65;
}

/* ─────────────────────────────────────────────────────────
   Celebration particles (카드 등장 완료시)
   ───────────────────────────────────────────────────────── */
.celebration { position: relative; width: 100%; height: 0; pointer-events: none; overflow: visible; }
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

/* ─────────────────────────────────────────────────────────
   §3 · Streamlit 위젯 — 버튼 / 입력 / 토글 / 슬라이더
   ───────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important; font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  padding: 10px 14px !important;
  border-radius: var(--r-md) !important;
  background: rgba(31,41,55,0.60) !important;
  color: var(--text-body) !important;
  border: 1px solid rgba(55,65,81,0.60) !important;
  box-shadow: none !important;
  transition: all 0.18s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  color: var(--text-primary) !important;
  border-color: rgba(75,85,99,0.80) !important;
  background: rgba(55,65,81,0.60) !important;
  transform: translateY(-1px);
}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background: rgba(var(--accent-rgb), 0.15) !important;
  color: var(--accent-bright) !important;
  border: 1px solid rgba(var(--accent-rgb), 0.35) !important;
  box-shadow: 0 0 10px rgba(var(--accent-rgb), 0.15) !important;
}
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
  background: rgba(var(--accent-rgb), 0.22) !important;
  border-color: rgba(var(--accent-rgb), 0.50) !important;
  box-shadow: 0 0 16px rgba(var(--accent-rgb), 0.30) !important;
  transform: translateY(-1px);
}
.stButton > button:disabled {
  opacity: 0.45 !important;
  cursor: not-allowed !important;
}

/* 텍스트 입력 */
input[type="text"], input[type="number"], input[type="search"], textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
  background: var(--surface) !important;
  border: 1px solid #374151 !important;
  border-radius: var(--r-md) !important;
  color: var(--text-primary) !important;
  font-family: 'JetBrains Mono', monospace !important;
  transition: all 0.18s ease !important;
}
input:focus, textarea:focus,
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.20) !important;
  outline: none !important;
}

/* Streamlit select / selectbox */
[data-baseweb="select"] > div {
  background: var(--surface) !important;
  border: 1px solid #374151 !important;
  border-radius: var(--r-md) !important;
}
[data-baseweb="select"]:focus-within > div {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.20) !important;
}
[data-baseweb="popover"] ul { background: var(--surface-solid) !important; }

/* ─────────────────────────────────────────────────────────
   Slider · Select_slider — Streamlit primaryColor(orange) 전면 오버라이드
   [data-baseweb="slider"] 단독으로 양쪽 위젯 커버
   ───────────────────────────────────────────────────────── */

/* Thumb (원형 핸들) */
[data-baseweb="slider"] [role="slider"] {
  background-color: var(--accent) !important;
  background: var(--accent) !important;
  border: 2px solid #030712 !important;
  box-shadow: 0 0 10px rgba(var(--accent-rgb), 0.5) !important;
  outline: none !important;
}
[data-baseweb="slider"] [role="slider"]:focus,
[data-baseweb="slider"] [role="slider"]:hover {
  box-shadow: 0 0 14px rgba(var(--accent-rgb), 0.7) !important;
}
/* Thumb inner dot (BaseWeb 가 있는 버전) */
[data-baseweb="slider"] [role="slider"] > div {
  background-color: #ffffff !important;
}
/* Thumb 위로 뜨는 값 라벨 */
[data-baseweb="slider"] [data-testid="stThumbValue"] {
  color: var(--accent-bright) !important;
  background: rgba(var(--accent-rgb), 0.15) !important;
  border: 1px solid rgba(var(--accent-rgb), 0.30) !important;
  border-radius: 4px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  padding: 2px 6px !important;
  box-shadow: 0 0 8px rgba(var(--accent-rgb), 0.2) !important;
}

/* 트랙 — BaseWeb 은 linear-gradient 를 inline style 로 그려서 percentage 가 박혀있음.
   CSS 로 background 를 덮으면 그 position 정보를 잃으므로, 여기선 unfilled 힌트만 주고
   실제 오렌지 → accent 치환은 app.py 의 MutationObserver JS 가 담당. */

/* Tick labels (select_slider 의 0.5x/1x/2x/4x 라벨) */
[data-testid="stTickBarMin"],
[data-testid="stTickBarMax"],
[data-baseweb="slider"] [data-testid^="stTickBar"] {
  color: var(--text-muted) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
}

/* ─────────────────────────────────────────────────────────
   Toggle / Checkbox — aria-checked="true" 일 때 accent 로 채움
   양쪽 모드에서 on/off 명확히 구분되도록
   ───────────────────────────────────────────────────────── */

/* OFF 상태 (기본) — surface 배경 */
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child,
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > div:first-child,
label[data-baseweb="checkbox"] > span:first-child,
label[data-baseweb="checkbox"] > div:first-child {
  background-color: rgba(31,41,55,0.8) !important;
  border-color: rgba(75,85,99,0.6) !important;
  transition: background-color 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

/* ON 상태 — 여러 aria/attr/:has variation 모두 커버 */
label[data-baseweb="checkbox"][aria-checked="true"] > span:first-child,
label[data-baseweb="checkbox"][aria-checked="true"] > div:first-child,
[data-testid="stCheckbox"] label[data-baseweb="checkbox"][aria-checked="true"] > span:first-child,
[data-testid="stCheckbox"] label[data-baseweb="checkbox"][aria-checked="true"] > div:first-child,
label[data-baseweb="checkbox"]:has(input:checked) > span:first-child,
label[data-baseweb="checkbox"]:has(input:checked) > div:first-child,
[data-testid="stCheckbox"] label:has(input:checked) > span:first-child,
[data-testid="stCheckbox"] label:has(input:checked) > div:first-child,
[role="checkbox"][aria-checked="true"],
[role="switch"][aria-checked="true"] {
  background-color: var(--accent) !important;
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  box-shadow: 0 0 10px rgba(var(--accent-rgb), 0.45) !important;
}

/* 체크마크 / thumb 핸들 — 흰색 유지 */
label[data-baseweb="checkbox"] > span:first-child > div,
label[data-baseweb="checkbox"] svg {
  color: #ffffff !important;
  fill: #ffffff !important;
}

/* ─────────────────────────────────────────────────────────
   Progress bar — filled portion 을 accent→secondary gradient 로
   ───────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div {
  background: rgba(31,41,55,0.55) !important;
  border-radius: var(--r-sm);
  overflow: hidden;
}
/* Streamlit 버전별 DOM 차이를 모두 커버 */
[data-testid="stProgress"] [role="progressbar"],
[data-testid="stProgress"] div[style*="width:"],
[data-testid="stProgress"] > div > div > div > div,
[data-testid="stProgress"] > div > div > div {
  background: linear-gradient(90deg, var(--accent) 0%, var(--secondary) 100%) !important;
  background-color: var(--accent) !important;
  box-shadow: 0 0 8px rgba(var(--accent-rgb), 0.45) !important;
}
/* 프로그레스 하단 텍스트 */
[data-testid="stProgress"] + div,
[data-testid="stProgress"] ~ div {
  color: var(--text-body) !important;
  font-family: 'Inter', sans-serif !important;
}

/* ─────────────────────────────────────────────────────────
   Inline color 오버라이드 — status-bar 내부 <b style="color:#FFC857">
   !important 는 inline style 을 이김
   ───────────────────────────────────────────────────────── */
.status-bar b[style],
.status-bar b {
  color: var(--secondary) !important;
}
/* 인사이트 헤드의 source dot 은 의미색(초록/회색) 이므로 건드리지 않음 */

/* ─────────────────────────────────────────────────────────
   Expander (사이드바)
   ───────────────────────────────────────────────────────── */
[data-testid="stExpander"] details {
  background: var(--card-bg);
  border: 1px solid var(--card-border) !important;
  border-radius: var(--r-md) !important;
  box-shadow: var(--glow-card);
  margin-bottom: 10px;
  transition: border-color 0.2s ease;
}
[data-testid="stExpander"] details[open] {
  border-color: rgba(var(--accent-rgb), 0.25) !important;
}
[data-testid="stExpander"] summary {
  font-family: 'Inter', sans-serif !important;
  font-size: 12.5px !important; font-weight: 600 !important;
  color: var(--text-primary) !important;
  letter-spacing: 0.02em;
  padding: 10px 14px !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent-bright) !important; }

/* 사이드바 슬라이드 핸들 (펼침 버튼) — 액센트 그라디언트 */
button[data-testid="stExpandSidebarButton"] {
  position: fixed !important;
  top: 100px !important;
  left: 0 !important;
  z-index: 1001 !important;
  width: 16px !important;
  height: 68px !important;
  min-width: 0 !important;
  padding: 0 !important;
  background: linear-gradient(135deg, var(--accent) 0%, var(--secondary) 100%) !important;
  border: none !important;
  border-radius: 0 12px 12px 0 !important;
  box-shadow: 3px 0 14px rgba(var(--accent-rgb), 0.4) !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important; justify-content: center !important;
  overflow: hidden !important;
  animation: handlePulse 2.6s ease-in-out infinite !important;
  transition: width 0.22s cubic-bezier(0.25, 1, 0.5, 1), box-shadow 0.22s ease !important;
}
button[data-testid="stExpandSidebarButton"]:hover {
  width: 36px !important;
  box-shadow: 5px 0 22px rgba(var(--accent-rgb), 0.7) !important;
  animation: none !important;
}
@keyframes handlePulse {
  0%, 100% { box-shadow: 2px 0 10px rgba(var(--accent-rgb), 0.3); }
  50%      { box-shadow: 4px 0 18px rgba(var(--accent-rgb), 0.7); }
}
button[data-testid="stExpandSidebarButton"] svg,
button[data-testid="stExpandSidebarButton"] path {
  color: #030712 !important; fill: #030712 !important; stroke: #030712 !important;
  width: 16px !important; height: 16px !important;
  opacity: 0 !important;
  transition: opacity 0.2s !important;
}
button[data-testid="stExpandSidebarButton"]:hover svg,
button[data-testid="stExpandSidebarButton"]:hover path { opacity: 1 !important; }

/* ─────────────────────────────────────────────────────────
   사이드바 캡션 / 카피
   ───────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  color: var(--text-body) !important;
  font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] b, section[data-testid="stSidebar"] strong {
  color: var(--text-primary);
}
.sb-footer {
  margin-top: 22px; padding-top: 16px;
  border-top: 1px solid var(--divider);
  color: var(--text-muted);
  font-family: 'Inter', sans-serif;
  font-size: 11px; line-height: 1.7;
}
.sb-footer a { color: var(--accent); text-decoration: none; }
.sb-footer a:hover { text-decoration: underline; }

/* ─────────────────────────────────────────────────────────
   Footer
   ───────────────────────────────────────────────────────── */
.footer {
  margin-top: 36px; padding: 20px 24px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-lg);
  color: var(--text-muted);
  font-family: 'Inter', sans-serif;
  font-size: 11.5px; line-height: 1.75;
  box-shadow: var(--glow-card);
}
.footer-title {
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700; font-size: 11px;
  letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 8px;
  filter: drop-shadow(0 0 6px rgba(var(--accent-rgb), 0.2));
}
.footer a { color: var(--accent); text-decoration: none; transition: color 0.15s; }
.footer a:hover { color: var(--accent-bright); text-decoration: underline; }
.footer b { color: var(--text-body); }

/* ─────────────────────────────────────────────────────────
   Plotly / dataframe
   ───────────────────────────────────────────────────────── */
div[data-testid="stPlotlyChart"] {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-lg);
  padding: 10px;
  box-shadow: var(--glow-card);
  animation: fadeIn 0.4s ease-out both;
}

div[data-testid="stDataFrame"],
div[data-testid="stDataFrameResizable"] {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-md);
  animation: dfFade 0.55s ease-out 0.4s both;
  overflow: hidden;
}
div[data-testid="stDataFrame"] table { font-family: 'JetBrains Mono', monospace !important; font-size: 12.5px; }

/* ─────────────────────────────────────────────────────────
   §5 · 애니메이션 · 등장(fade-in 0.4s), 스크롤 등장, 차트 등장
   ───────────────────────────────────────────────────────── */
@keyframes fadeIn   { from { opacity: 0; transform: translateY(8px); }  to { opacity: 1; transform: translateY(0); } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

/* Plotly BAR: apple-style rise */
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
svg.main-svg g.trace.bars g.point:nth-child(1)  { animation-delay: 0ms; }
svg.main-svg g.trace.bars g.point:nth-child(2)  { animation-delay: 55ms; }
svg.main-svg g.trace.bars g.point:nth-child(3)  { animation-delay: 110ms; }
svg.main-svg g.trace.bars g.point:nth-child(4)  { animation-delay: 165ms; }
svg.main-svg g.trace.bars g.point:nth-child(5)  { animation-delay: 220ms; }
svg.main-svg g.trace.bars g.point:nth-child(6)  { animation-delay: 275ms; }
svg.main-svg g.trace.bars g.point:nth-child(7)  { animation-delay: 330ms; }
svg.main-svg g.trace.bars g.point:nth-child(8)  { animation-delay: 385ms; }
svg.main-svg g.trace.bars g.point:nth-child(9)  { animation-delay: 440ms; }
svg.main-svg g.trace.bars g.point:nth-child(10) { animation-delay: 495ms; }
svg.main-svg g.trace.bars g.point:nth-child(11) { animation-delay: 550ms; }
svg.main-svg g.trace.bars g.point:nth-child(12) { animation-delay: 605ms; }
svg.main-svg g.trace.bars g.point:nth-child(13) { animation-delay: 660ms; }
svg.main-svg g.trace.bars g.point:nth-child(14) { animation-delay: 715ms; }
svg.main-svg g.trace.bars g.point:nth-child(15) { animation-delay: 770ms; }
svg.main-svg g.trace.bars g.point:nth-child(16) { animation-delay: 825ms; }
svg.main-svg g.trace.bars g.point:nth-child(n+17) { animation-delay: 880ms; }

/* LINE */
div[data-testid="stPlotlyChart"] svg.main-svg g.trace.scatter path.js-line,
div[data-testid="stPlotlyChart"] svg.main-svg .scatterlayer g.trace > path.js-line {
  stroke-dasharray: 3000;
  stroke-dashoffset: 3000;
  animation: lineDraw 1.6s cubic-bezier(0.22, 1, 0.36, 1) 0.25s forwards;
}
@keyframes lineDraw { to { stroke-dashoffset: 0; } }
div[data-testid="stPlotlyChart"] svg.main-svg g.trace.scatter g.points path {
  opacity: 0;
  animation: markerFade 0.4s ease-out 1.5s forwards;
}
@keyframes markerFade { to { opacity: 1; } }

/* HEATMAP */
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

/* 데이터프레임 딜레이 등장 */
@keyframes dfFade {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ─────────────────────────────────────────────────────────
   Tech tab 위젯 스킨 (tech_tab.py 클래스)
   ───────────────────────────────────────────────────────── */
.tech-hero {
  background: linear-gradient(135deg,
    rgba(var(--accent-rgb), 0.12) 0%,
    rgba(var(--secondary-rgb), 0.08) 100%);
  border: 1px solid rgba(var(--accent-rgb), 0.25);
  border-radius: var(--r-lg);
  padding: 24px 28px; margin-bottom: 20px;
  box-shadow: var(--glow-premium);
  animation: fadeInUp 0.55s ease-out;
}
.tech-hero h2 {
  margin: 0 0 8px 0; font-size: 24px;
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
  font-weight: 700; letter-spacing: -0.01em;
}
.tech-hero p {
  margin: 0; color: var(--text-body);
  font-size: 14px; line-height: 1.65;
}

.concept-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-md);
  padding: 20px 22px; margin-bottom: 14px;
  box-shadow: var(--glow-card);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  animation: fadeIn 0.4s ease-out both;
}
.concept-card:hover {
  border-color: rgba(var(--accent-rgb), 0.35);
  box-shadow: 0 0 22px rgba(var(--accent-rgb), 0.18);
  transform: translateY(-2px);
}
.concept-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 10px;
  filter: drop-shadow(0 0 6px rgba(var(--accent-rgb), 0.25));
}
.concept-body {
  color: var(--text-body);
  font-family: 'Inter', sans-serif;
  font-size: 13.5px; line-height: 1.75;
}

.metaphor {
  background: rgba(var(--accent-rgb), 0.06);
  border-left: 3px solid var(--accent);
  border-radius: var(--r-sm);
  padding: 12px 16px; margin-top: 12px;
  font-size: 13px; color: var(--text-body);
}
.metaphor b { color: var(--accent-bright); }

.key-formula {
  background: rgba(3,7,18,0.7);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px; color: var(--success);
  padding: 12px 16px; border-radius: var(--r-sm);
  margin-top: 12px;
  border: 1px solid rgba(52,211,153,0.15);
}

/* ─────────────────────────────────────────────────────────
   컨테이너 여백 · 기본 색
   ───────────────────────────────────────────────────────── */
.element-container, .block-container { color: var(--text-primary); }
h1, h2, h3, h4 {
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
a { color: var(--accent); transition: color 0.15s; }
a:hover { color: var(--accent-bright); }

/* 알림 박스 */
[data-baseweb="notification"] {
  border-radius: var(--r-md) !important;
  background: var(--card-bg) !important;
  border: 1px solid var(--card-border) !important;
  box-shadow: var(--glow-card);
}
"""


# =============================================================================
# CHROME · Home 버튼 + 모드 스위처 (모든 모드에 공통 주입)
# =============================================================================
_CHROME_BODY = r"""
/* DNA §8 · HOME 버튼 — 고정 우상단 · Apple squircle + rotating conic */
.home-btn {
  position: fixed; top: 12px; right: 24px;
  width: 44px; height: 44px;
  z-index: 1100;
  text-decoration: none;
  display: flex; align-items: center; justify-content: center;
  border-radius: 22%;                             /* Apple squircle 근사 */
  background: rgba(17,24,39,0.72);
  backdrop-filter: blur(14px) saturate(1.3);
  -webkit-backdrop-filter: blur(14px) saturate(1.3);
  border: 1px solid var(--card-border);
  box-shadow: var(--glow-premium);
  transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.25s ease;
  overflow: hidden;
  isolation: isolate;
}
.home-btn::before {
  content: '';
  position: absolute; inset: -60%;
  width: 220%; height: 220%;
  background: conic-gradient(
    from 0deg,
    transparent 0deg, transparent 230deg,
    var(--accent) 300deg,
    var(--secondary) 330deg,
    transparent 360deg
  );
  animation: rotateBorder 2.8s linear infinite;
  opacity: 0; transition: opacity 0.3s ease;
  z-index: -2;
}
.home-btn::after {
  content: '';
  position: absolute; inset: 1.5px;
  border-radius: inherit;
  background: rgba(3,7,18,0.82);
  backdrop-filter: blur(14px);
  z-index: -1;
}
.home-btn:hover {
  transform: scale(1.12);
  box-shadow: 0 0 24px rgba(var(--accent-rgb), 0.45),
              0 8px 32px rgba(0,0,0,0.5);
}
.home-btn:hover::before { opacity: 1; }
.home-btn svg {
  width: 18px; height: 18px;
  stroke: var(--accent); fill: none;
  filter: drop-shadow(0 0 6px rgba(var(--accent-rgb), 0.45));
  transition: transform 0.25s ease;
}
.home-btn:hover svg { transform: scale(1.08); }
@keyframes rotateBorder { to { transform: rotate(360deg); } }

/* 모드 스위처 — Home 버튼 왼쪽 */
.mode-switcher {
  position: fixed; top: 16px; right: 82px;
  z-index: 1100;
  display: inline-flex; gap: 6px;
  padding: 4px;
  background: rgba(17,24,39,0.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: var(--glow-card);
}
.mode-switcher a {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 11px; font-weight: 600;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 8px;
  color: var(--text-muted);
  border: 1px solid transparent;
  transition: all 0.18s ease;
  letter-spacing: 0.04em;
}
.mode-switcher a:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.03);
}
.mode-switcher a.active {
  background: rgba(var(--accent-rgb), 0.15);
  color: var(--accent-bright);
  border-color: rgba(var(--accent-rgb), 0.30);
  box-shadow: 0 0 10px rgba(var(--accent-rgb), 0.15);
}
"""

# 변경 전 모드에서 chrome(+tech tab SECTION_CSS) 를 렌더하기 위한 최소 토큰
# 원본 오렌지/앰버 팔레트 그대로
_CHROME_BEFORE_VARS = """
:root {
  --accent:         #FF6B35;
  --accent-bright:  #FFC857;
  --accent-rgb:     255, 107, 53;
  --secondary:      #FFC857;
  --secondary-rgb:  255, 200, 87;
  --card-bg:        #151A24;
  --card-border:    rgba(255,255,255,0.08);
  --text-primary:   #F5F6F8;
  --text-body:      #A0A7B4;
  --text-muted:     #8B95A5;
  --glow-card:      0 0 18px rgba(255,107,53,0.12);
  --glow-premium:   0 0 28px rgba(255,107,53,0.18),
                    0 8px 28px rgba(0,0,0,0.45);
}
"""


# =============================================================================
# 어셈블
# =============================================================================
_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2"
    "?family=Inter:wght@300;400;500;600;700;800"
    "&family=JetBrains+Mono:wght@400;500;600;700"
    "&display=swap');"
)


def css_for(mode: str) -> str:
    """mode: 'a' | 'b' → DNA 본체 + chrome 포함 완성된 <style> 블록.
       @import 는 스타일 블록 최상단에 와야 유효."""
    vars_block = _VARS_B if mode == "b" else _VARS_A
    return f"<style>{_FONT_IMPORT}\n{vars_block}\n{_BODY}\n{_CHROME_BODY}</style>"


def chrome_for_before() -> str:
    """변경 전 모드: Home 버튼 + 모드 스위처만 추가 주입 (기존 오렌지 토큰 사용)."""
    return f"<style>{_CHROME_BEFORE_VARS}\n{_CHROME_BODY}</style>"


def home_button_html(href: str = "/") -> str:
    """DNA §8 Home 버튼 (fixed top-right · squircle · glass · rotating border)."""
    return f'''
<a class="home-btn" href="{href}" title="Back to Portfolio" aria-label="Home">
  <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M3 12 L12 3 L21 12" />
    <path d="M5 10 L5 21 L19 21 L19 10" />
    <path d="M10 21 L10 14 L14 14 L14 21" />
  </svg>
</a>
'''


def mode_switcher_html(current: str) -> str:
    """3가지 모드 전환 스위처 (Home 버튼 왼쪽)."""
    def cls(key: str) -> str:
        return "active" if key == current else ""
    return f'''
<div class="mode-switcher" role="tablist" aria-label="Design mode">
  <a href="?mode=before" class="{cls('before')}" role="tab">변경 전</a>
  <a href="?mode=a"      class="{cls('a')}"      role="tab">A · 원본</a>
  <a href="?mode=b"      class="{cls('b')}"      role="tab">B · 오렌지</a>
</div>
'''

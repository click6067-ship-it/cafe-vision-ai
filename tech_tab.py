"""
🎓 기술 원리 탭 — 일반 대중 대상 YOLO/ByteTrack 직관 설명
인터랙티브 HTML/CSS/JS 위젯 포함.
"""
from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components


SECTION_CSS = """
<style>
.tech-hero {
  background: linear-gradient(135deg, rgba(79,139,249,0.15) 0%, rgba(255,107,53,0.12) 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 22px 26px; margin-bottom: 18px;
}
.tech-hero h2 { margin: 0 0 6px 0; font-size: 24px; color: #F5F6F8; font-weight: 700; }
.tech-hero p { margin: 0; color: #A0A7B4; font-size: 14px; line-height: 1.6; }

.concept-card {
  background: #151A24; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 18px 20px; margin-bottom: 14px;
}
.concept-title { font-size: 15px; font-weight: 700; color: #FFC857; margin-bottom: 8px; }
.concept-body { color: #C7CDD8; font-size: 13.5px; line-height: 1.7; }

.metaphor {
  background: rgba(79,139,249,0.08); border-left: 3px solid #4F8BF9;
  border-radius: 6px; padding: 10px 14px; margin-top: 10px;
  font-size: 13px; color: #C0C6D2;
}
.metaphor b { color: #4F8BF9; }

.key-formula {
  background: #0A0D13; font-family: 'JetBrains Mono', monospace;
  font-size: 13px; color: #7FE5BA; padding: 10px 14px; border-radius: 8px;
  margin-top: 10px; border: 1px solid rgba(127,229,186,0.15);
}
</style>
"""


# --- 1. 격자 애니메이션 위젯 ---------------------------------------------------
GRID_WIDGET = """
<style>
  body { background: transparent; color: #E6E8EB; font-family: 'Pretendard Variable', sans-serif; margin: 0; }
  .wrap { display:flex; flex-direction:column; align-items:center; padding: 14px; }
  .stage-buttons { display:flex; gap:8px; margin-bottom: 14px; flex-wrap:wrap; justify-content:center; }
  .stage-btn {
    background:#151A24; color:#C0C6D2; border:1px solid rgba(255,255,255,0.1);
    padding:8px 14px; border-radius:8px; cursor:pointer; font-size:12px; font-weight:600;
    transition: all 0.2s;
  }
  .stage-btn:hover { border-color:#FF6B35; color:#FF6B35; }
  .stage-btn.active { background:linear-gradient(135deg,#FF6B35,#FFC857); color:#0B0E14; border-color:transparent; }
  .canvas {
    position:relative; width:480px; height:360px; background:#0A0D13;
    border-radius:10px; border:1px solid rgba(255,255,255,0.08); overflow:hidden;
  }
  .grid { position:absolute; top:0; left:0; right:0; bottom:0; display:grid;
    grid-template-columns: repeat(8, 1fr); grid-template-rows: repeat(6, 1fr); }
  .cell {
    border: 1px solid rgba(255,255,255,0.05); transition: background 0.4s, border-color 0.4s;
  }
  .cell.active { background: rgba(79,139,249,0.12); border-color: rgba(79,139,249,0.5); }
  .cell.hit { background: rgba(255,107,53,0.2); border-color: rgba(255,107,53,0.7); }
  .person {
    position:absolute; border:2px solid rgba(255,255,255,0.2); border-radius:50%;
    background: radial-gradient(circle, rgba(79,139,249,0.45), rgba(79,139,249,0.15));
    transition: all 0.4s;
  }
  .person .silhouette {
    width: 22px; height: 40px; background: rgba(255,255,255,0.55);
    border-radius: 11px 11px 6px 6px; margin: auto; position:relative; top: 8px;
  }
  .bbox { position:absolute; border:2px solid #FF6B35; border-radius:3px; opacity:0; transition: opacity 0.4s; }
  .bbox.show { opacity: 1; }
  .bbox-label {
    position:absolute; top:-18px; left:-2px; font-size:10px; font-weight:700;
    background:#FF6B35; color:#0B0E14; padding:2px 6px; border-radius:3px;
  }
  .hint { margin-top:12px; color:#8B95A5; font-size:12px; text-align:center; max-width:480px; line-height:1.5; }
</style>
<div class="wrap">
  <div class="stage-buttons">
    <button class="stage-btn active" onclick="setStage(0)">① 입력 이미지</button>
    <button class="stage-btn" onclick="setStage(1)">② 격자 분할</button>
    <button class="stage-btn" onclick="setStage(2)">③ 칸별 탐지</button>
    <button class="stage-btn" onclick="setStage(3)">④ 최종 결과</button>
  </div>
  <div class="canvas">
    <div class="grid" id="grid"></div>
    <div class="person" style="left:80px; top:80px; width:60px; height:80px"><div class="silhouette"></div></div>
    <div class="person" style="left:260px; top:140px; width:55px; height:75px"><div class="silhouette"></div></div>
    <div class="person" style="left:360px; top:60px; width:52px; height:72px"><div class="silhouette"></div></div>
    <div class="bbox" id="b1" style="left:70px; top:70px; width:80px; height:100px">
      <div class="bbox-label">person 0.92</div>
    </div>
    <div class="bbox" id="b2" style="left:250px; top:130px; width:75px; height:95px">
      <div class="bbox-label">person 0.88</div>
    </div>
    <div class="bbox" id="b3" style="left:352px; top:50px; width:70px; height:92px">
      <div class="bbox-label">person 0.85</div>
    </div>
  </div>
  <div class="hint" id="hint">클릭해서 YOLO가 한 장의 이미지를 어떻게 처리하는지 단계별로 살펴보세요.</div>
</div>
<script>
  const grid = document.getElementById('grid');
  const hint = document.getElementById('hint');
  const cells = [];
  for (let i=0;i<48;i++) { const c=document.createElement('div'); c.className='cell'; grid.appendChild(c); cells.push(c); }
  const HITS = [9,10,11,17,18,19,  21,22,29,30,  14,15,22,23];
  const HINTS = [
    "원본 CCTV 프레임. YOLO는 이 이미지 한 번만 보고 모든 객체를 찾아냅니다.",
    "이미지를 8×6 = 48개 격자로 분할. 각 칸이 자기 구역을 책임집니다. (물결처럼 활성화되는 애니메이션)",
    "모든 칸이 동시에 '여기 뭐 있나?'를 평가. 오렌지 칸은 사람이 포착된 위치. (순차적으로 탐지됨)",
    "신뢰도 0.5 이상만 남기고 NMS로 중복 제거 → 최종 바운딩박스와 신뢰도 점수 출력.",
  ];
  let timeouts = [];
  function cancelTimers(){ timeouts.forEach(clearTimeout); timeouts = []; }
  function schedule(fn, ms){ timeouts.push(setTimeout(fn, ms)); }

  function setStage(s) {
    cancelTimers();
    document.querySelectorAll('.stage-btn').forEach((b,i)=>b.classList.toggle('active', i===s));
    hint.textContent = HINTS[s];
    cells.forEach(c=>c.classList.remove('active','hit'));
    ['b1','b2','b3'].forEach(id=>document.getElementById(id).classList.remove('show'));

    const cellStep = 14;        // 셀당 지연 (ms) · 48셀 × 14 ≈ 670ms 총 웨이브
    const hitStep  = 70;        // HIT당 지연
    const bboxStep = 180;       // bbox당 지연

    if (s >= 1) {
      // 대각선 웨이브 — row+col 합을 기준으로 오프셋 (0~12 단계)
      for (let i=0; i<cells.length; i++) {
        const row = Math.floor(i/8), col = i%8;
        const wave = row + col;  // 0..12
        schedule(() => cells[i].classList.add('active'), wave * 30 + (i % 3) * 5);
      }
    }

    const stage1End = s >= 1 ? 13 * 30 + 100 : 0;

    if (s >= 2) {
      HITS.forEach((idx, k) => {
        schedule(() => {
          cells[idx].classList.remove('active');
          cells[idx].classList.add('hit');
        }, stage1End + k * hitStep);
      });
    }

    const stage2End = s >= 2 ? stage1End + HITS.length * hitStep + 150 : stage1End;

    if (s >= 3) {
      ['b1','b2','b3'].forEach((id, k) => {
        schedule(() => document.getElementById(id).classList.add('show'),
                 stage2End + k * bboxStep);
      });
    }
  }
  setStage(0);
</script>
"""


# --- 2. IoU 계산기 위젯 -------------------------------------------------------
IOU_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:14px; display:flex; gap:20px; align-items:center; justify-content:center; flex-wrap:wrap; }
  .canvas { position:relative; width:340px; height:260px; background:#0A0D13; border:1px solid rgba(255,255,255,0.08); border-radius:10px; overflow:hidden; }
  .box { position:absolute; border:2px solid; border-radius:4px; opacity:0.85; }
  .box.a { border-color:#4F8BF9; background:rgba(79,139,249,0.15); }
  .box.b { border-color:#FF6B35; background:rgba(255,107,53,0.15); }
  .controls { display:flex; flex-direction:column; gap:10px; min-width:260px; }
  .slider-row { display:flex; align-items:center; gap:10px; font-size:12px; color:#A0A7B4; }
  .slider-row input[type=range] { flex:1; accent-color:#FF6B35; }
  .readout { background:#151A24; border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px; }
  .iou-val { font-size:38px; font-weight:700; background:linear-gradient(135deg,#FF6B35,#FFC857); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .iou-sub { color:#8B95A5; font-size:12px; margin-top:4px; }
  .iou-formula { color:#7FE5BA; font-family:monospace; font-size:12px; margin-top:10px; line-height:1.8; }
</style>
<div class="wrap">
  <div class="canvas" id="canvas">
    <div class="box a" id="boxA" style="left:40px; top:50px; width:150px; height:140px"></div>
    <div class="box b" id="boxB" style="left:120px; top:90px; width:150px; height:140px"></div>
  </div>
  <div class="controls">
    <div class="readout">
      <div class="iou-val" id="iouVal">0.00</div>
      <div class="iou-sub">IoU · Intersection over Union</div>
      <div class="iou-formula">
        교집합: <span id="inter">0</span><br>
        합집합: <span id="union">0</span><br>
        IoU = 교집합 / 합집합
      </div>
    </div>
    <div class="slider-row"><span>B 가로위치</span><input type="range" min="0" max="200" value="80" id="sx"></div>
    <div class="slider-row"><span>B 세로위치</span><input type="range" min="0" max="100" value="40" id="sy"></div>
    <div class="slider-row"><span>B 크기</span><input type="range" min="60" max="180" value="150" id="ss"></div>
  </div>
</div>
<script>
  const A = {x:40, y:50, w:150, h:140};
  const sx=document.getElementById('sx'), sy=document.getElementById('sy'), ss=document.getElementById('ss');
  const boxB=document.getElementById('boxB'), iouVal=document.getElementById('iouVal');
  const interEl=document.getElementById('inter'), unionEl=document.getElementById('union');
  function compute() {
    const bx=40+parseInt(sx.value), by=50+parseInt(sy.value), bs=parseInt(ss.value);
    boxB.style.left=bx+'px'; boxB.style.top=by+'px'; boxB.style.width=bs+'px'; boxB.style.height=bs*0.93+'px';
    const ax1=A.x, ay1=A.y, ax2=A.x+A.w, ay2=A.y+A.h;
    const bx1=bx, by1=by, bx2=bx+bs, by2=by+bs*0.93;
    const ix1=Math.max(ax1,bx1), iy1=Math.max(ay1,by1), ix2=Math.min(ax2,bx2), iy2=Math.min(ay2,by2);
    const iw=Math.max(0,ix2-ix1), ih=Math.max(0,iy2-iy1);
    const inter=iw*ih;
    const areaA=A.w*A.h, areaB=bs*bs*0.93;
    const union=areaA+areaB-inter;
    const iou=union>0?inter/union:0;
    iouVal.textContent=iou.toFixed(2);
    interEl.textContent=Math.round(inter).toLocaleString();
    unionEl.textContent=Math.round(union).toLocaleString();
  }
  [sx,sy,ss].forEach(el=>el.addEventListener('input', compute));
  compute();
</script>
"""


# --- 3. NMS 시뮬레이터 위젯 ---------------------------------------------------
NMS_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:14px; display:flex; flex-direction:column; align-items:center; }
  .btn-row { display:flex; gap:10px; margin-bottom: 14px; }
  .go-btn { background:linear-gradient(135deg,#FF6B35,#FFC857); color:#0B0E14; font-weight:700; font-size:12px;
    border:none; padding:10px 18px; border-radius:8px; cursor:pointer; letter-spacing:0.08em; }
  .reset-btn { background:#151A24; color:#C0C6D2; border:1px solid rgba(255,255,255,0.1); padding:10px 14px; border-radius:8px; cursor:pointer; font-size:12px; }
  .canvas { position:relative; width:460px; height:300px; background:#0A0D13; border:1px solid rgba(255,255,255,0.08); border-radius:10px; overflow:hidden; }
  .nmsbox { position:absolute; border:2px solid; border-radius:4px;
    transform: scale(0.95); opacity: 0;
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.4s, box-shadow 0.5s; }
  .nmsbox.shown { transform: scale(1); opacity: 1; }
  .nmsbox.eliminated { opacity: 0.1; border-style: dashed; transform: scale(0.92); }
  .nmsbox.winner { box-shadow: 0 0 0 3px rgba(255,107,53,0.4); animation: winnerRing 1.1s ease-out; }
  @keyframes winnerRing {
    0%   { box-shadow: 0 0 0 0 rgba(255,107,53,0.8); }
    70%  { box-shadow: 0 0 0 14px rgba(255,107,53,0); }
    100% { box-shadow: 0 0 0 3px rgba(255,107,53,0.4); }
  }
  .nmsbox .lbl {
    position:absolute; top:-20px; left:-2px; font-size:10px; font-weight:700;
    padding:2px 7px; border-radius:3px; color:#0B0E14;
  }
  .step { margin-top:14px; color:#8B95A5; font-size:12px; text-align:center; max-width:460px; line-height:1.6; }
  .step b { color:#FFC857; }
</style>
<div class="wrap">
  <div class="btn-row">
    <button class="go-btn" onclick="runNms()">▶ NMS 실행</button>
    <button class="reset-btn" onclick="reset()">↺ 리셋</button>
  </div>
  <div class="canvas" id="canv">
    <div class="nmsbox" id="n1" style="left:80px; top:60px; width:160px; height:190px; border-color:#4F8BF9; background:rgba(79,139,249,0.1)"><span class="lbl" style="background:#4F8BF9">#1 · 0.92</span></div>
    <div class="nmsbox" id="n2" style="left:110px; top:80px; width:155px; height:185px; border-color:#23C552; background:rgba(35,197,82,0.1)"><span class="lbl" style="background:#23C552">#2 · 0.78</span></div>
    <div class="nmsbox" id="n3" style="left:95px; top:95px; width:150px; height:175px; border-color:#FFC857; background:rgba(255,200,87,0.1)"><span class="lbl" style="background:#FFC857">#3 · 0.65</span></div>
    <div class="nmsbox" id="n4" style="left:280px; top:70px; width:140px; height:175px; border-color:#FF6B9D; background:rgba(255,107,157,0.1)"><span class="lbl" style="background:#FF6B9D">#4 · 0.89</span></div>
  </div>
  <div class="step" id="step">3개의 상자가 같은 사람(좌측)에 겹쳐 있고, 오른쪽에 또 하나의 탐지(#4)가 있습니다. 같은 사람에 대한 중복을 어떻게 제거할까요?</div>
</div>
<script>
  const steps = [
    "3개의 상자가 같은 사람(좌측)에 겹쳐 있고, 오른쪽에 또 하나의 탐지(#4)가 있습니다. 같은 사람에 대한 중복을 어떻게 제거할까요?",
    "<b>Step 1.</b> 신뢰도 내림차순 정렬: #1(0.92) > #4(0.89) > #2(0.78) > #3(0.65)",
    "<b>Step 2.</b> 1위(#1) 채택. #1과 IoU > 0.5인 상자(#2, #3) 제거.",
    "<b>Step 3.</b> 남은 상자 중 #4 채택. #4는 #1과 겹치지 않으므로 유지.",
    "<b>결과.</b> 최종 2개 상자(#1, #4)만 남음. '반장 선거'처럼 같은 반의 경쟁자는 떨어집니다.",
  ];
  const stepEl = document.getElementById('step');
  // 초기 등장 스태거
  ['n1','n2','n3','n4'].forEach((id, k) => {
    setTimeout(() => document.getElementById(id).classList.add('shown'), 120 + k * 90);
  });
  function reset() {
    ['n1','n2','n3','n4'].forEach(id=>{const e=document.getElementById(id); e.classList.remove('eliminated','winner'); e.classList.add('shown');});
    stepEl.innerHTML = steps[0];
  }
  async function runNms() {
    reset();
    await sleep(400); stepEl.innerHTML = steps[1];
    await sleep(1100); document.getElementById('n1').classList.add('winner'); stepEl.innerHTML = steps[2];
    await sleep(1100); document.getElementById('n2').classList.add('eliminated'); document.getElementById('n3').classList.add('eliminated');
    await sleep(800); stepEl.innerHTML = steps[3];
    await sleep(1100); document.getElementById('n4').classList.add('winner');
    await sleep(600); stepEl.innerHTML = steps[4];
  }
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
</script>
"""


# --- 4. ByteTrack 저신뢰 vs DeepSORT 위젯 -------------------------------------
BYTETRACK_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:10px; }
  .btn-row { display:flex; gap:10px; margin-bottom:14px; justify-content:center; }
  .play-btn { background:linear-gradient(135deg,#FF6B35,#FFC857); color:#0B0E14; font-weight:700;
    border:none; padding:10px 18px; border-radius:8px; cursor:pointer; font-size:12px; letter-spacing:0.08em; }
  .row { display:grid; grid-template-columns: 90px repeat(8, 1fr); gap:4px; margin-bottom:6px; align-items:center; }
  .row-label { font-size:11px; color:#8B95A5; font-weight:600; }
  .frame { height:46px; border-radius:6px; background:#0A0D13; border:1px solid rgba(255,255,255,0.08);
    display:flex; flex-direction:column; align-items:center; justify-content:center; font-size:10px; color:#8B95A5;
    transition: all 0.4s; position:relative; }
  .frame .conf { font-size:9px; color:#6B7280; margin-top:2px; }
  .frame.id3 { background:#1A3A5F; border-color:#4F8BF9; color:#8FC1FF; }
  .frame.id7 { background:#4A1A1A; border-color:#FF6B6B; color:#FF9999; }
  .frame.drop { background:#1A1A1A; border-style:dashed; color:#555; }
  .section-title { font-size:12px; font-weight:700; margin: 10px 0 6px 0; }
  .section-title.ds { color:#FF6B6B; }
  .section-title.bt { color:#23C552; }
  .verdict { margin-top:14px; padding:12px 14px; border-radius:10px; font-size:12.5px; line-height:1.6; }
  .verdict.bad { background:rgba(255,107,107,0.1); border-left:3px solid #FF6B6B; color:#FFB3B3; }
  .verdict.good { background:rgba(35,197,82,0.1); border-left:3px solid #23C552; color:#A7EBBA; }
</style>
<div class="wrap">
  <div class="btn-row">
    <button class="play-btn" onclick="runScenario()">▶ "손님이 의자에 앉는 순간" 시뮬레이션</button>
  </div>
  <div class="section-title ds">❌ 일반 트래커 (DeepSORT) — 저신뢰 탐지 버림</div>
  <div class="row">
    <div class="row-label">DeepSORT</div>
    <div class="frame" id="ds0">#50<div class="conf">0.92</div></div>
    <div class="frame" id="ds1">#51<div class="conf">0.65</div></div>
    <div class="frame" id="ds2">#52<div class="conf">0.30</div></div>
    <div class="frame" id="ds3">#53<div class="conf">0.25</div></div>
    <div class="frame" id="ds4">#54<div class="conf">0.40</div></div>
    <div class="frame" id="ds5">#55<div class="conf">0.55</div></div>
    <div class="frame" id="ds6">#56<div class="conf">0.80</div></div>
    <div class="frame" id="ds7">#57<div class="conf">0.92</div></div>
  </div>
  <div class="section-title bt">✅ ByteTrack — 저신뢰 탐지도 재활용</div>
  <div class="row">
    <div class="row-label">ByteTrack</div>
    <div class="frame" id="bt0">#50<div class="conf">0.92</div></div>
    <div class="frame" id="bt1">#51<div class="conf">0.65</div></div>
    <div class="frame" id="bt2">#52<div class="conf">0.30</div></div>
    <div class="frame" id="bt3">#53<div class="conf">0.25</div></div>
    <div class="frame" id="bt4">#54<div class="conf">0.40</div></div>
    <div class="frame" id="bt5">#55<div class="conf">0.55</div></div>
    <div class="frame" id="bt6">#56<div class="conf">0.80</div></div>
    <div class="frame" id="bt7">#57<div class="conf">0.92</div></div>
  </div>
  <div id="verdict"></div>
</div>
<script>
  async function runScenario() {
    const verdictEl = document.getElementById('verdict');
    verdictEl.innerHTML = "";
    for (let i=0;i<8;i++) {
      document.getElementById('ds'+i).className = 'frame';
      document.getElementById('bt'+i).className = 'frame';
    }
    await sleep(300);
    // DeepSORT: drop low-conf
    const dsAssign = ['id3','id3','drop','drop','id7','id7','id7','id7'];
    // ByteTrack: keep id3 via low-conf match
    const btAssign = ['id3','id3','id3','id3','id3','id3','id3','id3'];
    for (let i=0;i<8;i++) {
      document.getElementById('ds'+i).classList.add(dsAssign[i]);
      document.getElementById('bt'+i).classList.add(btAssign[i]);
      const dsLabel = dsAssign[i]==='drop' ? 'DROP' : (dsAssign[i]==='id3' ? 'ID-3' : 'ID-7');
      document.getElementById('ds'+i).childNodes[0].textContent = '#'+(50+i)+' '+dsLabel;
      document.getElementById('bt'+i).childNodes[0].textContent = '#'+(50+i)+' ID-3';
      await sleep(300);
    }
    await sleep(400);
    verdictEl.innerHTML =
      '<div class="verdict bad">DeepSORT: 신뢰도 0.25~0.30 구간에서 탐지를 버림 → ID-3 소멸 → 재등장 시 새 ID-7 부여. <b>체류시간 측정 실패</b>.</div>' +
      '<div class="verdict good">ByteTrack: 저신뢰 탐지를 칼만 예측 위치와 IoU로 재매칭. <b>ID-3이 8프레임 내내 유지됨</b>. 정확한 체류시간 계산 가능.</div>';
  }
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
</script>
"""


# --- 5. Kalman Filter 예측 위젯 ------------------------------------------------
KALMAN_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:14px; display:flex; flex-direction:column; align-items:center; }
  .canvas { position:relative; width:460px; height:220px; background:#0A0D13;
    border:1px solid rgba(255,255,255,0.08); border-radius:10px; overflow:hidden; }
  .track-dot { position:absolute; width:14px; height:14px; border-radius:50%; transition: all 0.6s ease-out; }
  .track-dot.past { background: rgba(79,139,249,0.4); border: 1px solid #4F8BF9; }
  .track-dot.now { background: #4F8BF9; box-shadow: 0 0 10px #4F8BF9; }
  .track-dot.pred { background: transparent; border: 2px dashed #FF6B35; }
  .arrow { position:absolute; height: 2px; background: linear-gradient(90deg, #4F8BF9, #FF6B35); transform-origin: left; }
  .legend { display:flex; gap:16px; margin-top:12px; font-size:11px; color:#8B95A5; flex-wrap:wrap; justify-content:center; }
  .legend-item { display:flex; align-items:center; gap:6px; }
  .lg-dot { width:10px; height:10px; border-radius:50%; }
  .btn { margin-top:12px; background:linear-gradient(135deg,#4F8BF9,#7FE5BA); color:#0B0E14; font-weight:700; font-size:12px;
    border:none; padding:9px 16px; border-radius:8px; cursor:pointer; letter-spacing:0.06em; }
</style>
<div class="wrap">
  <div class="canvas" id="kc"></div>
  <div class="legend">
    <div class="legend-item"><div class="lg-dot" style="background:rgba(79,139,249,0.4);border:1px solid #4F8BF9"></div> 과거 관측</div>
    <div class="legend-item"><div class="lg-dot" style="background:#4F8BF9;box-shadow:0 0 6px #4F8BF9"></div> 현재</div>
    <div class="legend-item"><div class="lg-dot" style="background:transparent;border:2px dashed #FF6B35"></div> 다음 프레임 예측</div>
  </div>
  <button class="btn" onclick="step()">▶ 다음 프레임 예측</button>
</div>
<script>
  const kc = document.getElementById('kc');
  const path = [[40,120],[90,110],[140,105],[190,100],[240,95]];
  let idx = 0;
  function render() {
    kc.innerHTML = '';
    for (let i=0;i<idx;i++) {
      const [x,y] = path[i];
      const d = document.createElement('div'); d.className='track-dot past'; d.style.left=x+'px'; d.style.top=y+'px';
      kc.appendChild(d);
    }
    if (idx < path.length) {
      const [x,y] = path[idx];
      const d = document.createElement('div'); d.className='track-dot now'; d.style.left=x+'px'; d.style.top=y+'px';
      kc.appendChild(d);
      if (idx >= 1) {
        const [px,py] = path[idx-1];
        const vx = x - px, vy = y - py;
        const nx = x + vx, ny = y + vy;
        const p = document.createElement('div'); p.className='track-dot pred'; p.style.left=nx+'px'; p.style.top=ny+'px';
        kc.appendChild(p);
        const a = document.createElement('div'); a.className='arrow';
        const len = Math.sqrt((nx-x)**2+(ny-y)**2);
        const ang = Math.atan2(ny-y, nx-x)*180/Math.PI;
        a.style.left=(x+7)+'px'; a.style.top=(y+7)+'px'; a.style.width=len+'px';
        a.style.transform=`rotate(${ang}deg)`;
        kc.appendChild(a);
      }
    }
  }
  function step() { idx = (idx+1) % (path.length+1); render(); }
  render();
</script>
"""


# --- 5b. 프레임 간 추적 연결선 위젯 -------------------------------------------
TRACKING_LINK_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:14px; display:flex; flex-direction:column; align-items:center; }
  .play-btn { background:linear-gradient(135deg,#FF6B35,#FFC857); color:#0B0E14; font-weight:700;
    border:none; padding:9px 16px; border-radius:8px; cursor:pointer; font-size:12px; letter-spacing:0.06em; margin-bottom:16px; }
  .stage { display:flex; align-items:center; gap:14px; }
  .frame-box {
    width: 130px; height: 150px; background: #0A0D13; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; position: relative; padding: 8px;
  }
  .frame-box .lbl { position:absolute; top:-9px; left:10px; background:#151A24;
    padding:1px 7px; border-radius:4px; font-size:10px; color:#A0A7B4;
    font-weight:700; letter-spacing:0.06em; border:1px solid rgba(255,255,255,0.08); }
  .dot-person {
    position:absolute; width: 22px; height: 22px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.15); background: #3A4253;
    transition: all 0.6s;
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:10px; font-weight:700;
  }
  .dot-person.colored-A { background: radial-gradient(circle, #A78BFA, #7C3AED); border-color:#A78BFA; color:#fff; }
  .dot-person.colored-B { background: radial-gradient(circle, #5EEAD4, #0D9488); border-color:#5EEAD4; color:#0B0E14; }
  .dot-person.colored-C { background: radial-gradient(circle, #FCA5A5, #EF4444); border-color:#FCA5A5; color:#fff; }
  .connector {
    width: 50px; height: 2px; background: rgba(255,255,255,0.1);
    position: relative; overflow: visible;
  }
  .connector svg { position:absolute; top:-14px; left:0; }
  .connector .line { stroke: rgba(255,255,255,0.08); stroke-width: 2; fill: none;
    stroke-dasharray: 100; stroke-dashoffset: 100; transition: stroke 0.6s, stroke-dashoffset 1s; }
  .connector.active .line { stroke-dashoffset: 0; }
  .connector.line-A .line { stroke: #A78BFA; }
  .connector.line-B .line { stroke: #5EEAD4; }
  .connector.line-C .line { stroke: #FCA5A5; }
  .hint { margin-top: 14px; color:#8B95A5; font-size:12px; text-align:center; max-width:520px; line-height:1.6; }
  .hint b { color:#FFC857; }
</style>
<div class="wrap">
  <button class="play-btn" onclick="runLink()">▶ 추적 연결 실행</button>
  <div class="stage">
    <div class="frame-box">
      <span class="lbl">FRAME #1</span>
      <div class="dot-person colored-A" id="f1a" style="top:30px; left:18px">A</div>
      <div class="dot-person colored-B" id="f1b" style="top:70px; left:55px">B</div>
      <div class="dot-person colored-C" id="f1c" style="top:100px; left:88px">C</div>
    </div>
    <svg class="connector" id="c12" width="50" height="30">
      <path class="line" d="M 0 15 C 20 5, 30 25, 50 15" />
    </svg>
    <div class="frame-box">
      <span class="lbl">FRAME #2</span>
      <div class="dot-person" id="f2a" style="top:34px; left:22px">?</div>
      <div class="dot-person" id="f2b" style="top:72px; left:60px">?</div>
      <div class="dot-person" id="f2c" style="top:104px; left:92px">?</div>
    </div>
    <svg class="connector" id="c23" width="50" height="30">
      <path class="line" d="M 0 15 C 20 5, 30 25, 50 15" />
    </svg>
    <div class="frame-box">
      <span class="lbl">FRAME #3</span>
      <div class="dot-person" id="f3a" style="top:40px; left:28px">?</div>
      <div class="dot-person" id="f3b" style="top:76px; left:66px">?</div>
      <div class="dot-person" id="f3c" style="top:108px; left:96px">?</div>
    </div>
  </div>
  <div class="hint" id="link-hint">각 프레임마다 YOLO는 "여기 사람이 있다"만 알 뿐, <b>어느 사람이 같은 사람인지</b> 모릅니다. ByteTrack이 연결해줍니다.</div>
</div>
<script>
  const linkHint = document.getElementById('link-hint');
  async function runLink() {
    // reset
    ['f2a','f2b','f2c','f3a','f3b','f3c'].forEach(id=>{
      const e=document.getElementById(id); e.className='dot-person'; e.textContent='?';
    });
    ['c12','c23'].forEach(id=>{
      const e=document.getElementById(id); e.className='connector';
    });
    linkHint.innerHTML = "1차 매칭: ByteTrack이 Frame 1 → Frame 2 동일 인물 연결 시도…";
    await sleep(700);

    // Frame 2 activation
    document.getElementById('c12').classList.add('active','line-A');
    document.getElementById('f2a').classList.add('colored-A'); document.getElementById('f2a').textContent='A';
    await sleep(350);
    document.getElementById('c12').classList.add('line-B');
    document.getElementById('f2b').classList.add('colored-B'); document.getElementById('f2b').textContent='B';
    await sleep(350);
    document.getElementById('c12').classList.add('line-C');
    document.getElementById('f2c').classList.add('colored-C'); document.getElementById('f2c').textContent='C';

    await sleep(600);
    linkHint.innerHTML = "2차 매칭: Frame 2 → Frame 3 도 같은 방식으로 연결…";
    await sleep(500);

    document.getElementById('c23').classList.add('active','line-A');
    document.getElementById('f3a').classList.add('colored-A'); document.getElementById('f3a').textContent='A';
    await sleep(350);
    document.getElementById('c23').classList.add('line-B');
    document.getElementById('f3b').classList.add('colored-B'); document.getElementById('f3b').textContent='B';
    await sleep(350);
    document.getElementById('c23').classList.add('line-C');
    document.getElementById('f3c').classList.add('colored-C'); document.getElementById('f3c').textContent='C';

    await sleep(600);
    linkHint.innerHTML = "<b>✓ 같은 색 = 같은 사람.</b> ByteTrack이 프레임 간 동일 인물을 IoU·Kalman 예측으로 연결했습니다. 이제 체류시간 측정이 가능합니다.";
  }
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
</script>
"""


# --- 5c. 신뢰도 게이지 변화 위젯 ------------------------------------------------
CONFIDENCE_GAUGE_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:14px; }
  .btn-row { display:flex; justify-content:center; margin-bottom:16px; }
  .go-btn { background:linear-gradient(135deg,#FF6B35,#FFC857); color:#0B0E14; font-weight:700;
    border:none; padding:10px 18px; border-radius:8px; cursor:pointer; font-size:12px; letter-spacing:0.06em; }
  .gauge-row { display:flex; align-items:center; gap:14px; margin-bottom:12px; }
  .gauge-label { width: 120px; font-size:12px; font-weight:600; color:#C0C6D2; }
  .gauge-track {
    flex:1; height: 22px; background:#0A0D13; border-radius:6px; overflow:hidden;
    border:1px solid rgba(255,255,255,0.08);
  }
  .gauge-fill {
    height:100%; width: 92%; transition: width 1s ease-out, background 1s;
    background: linear-gradient(90deg, #23C552, #5EEAD4);
    display:flex; align-items:center; justify-content:flex-end; padding-right:10px;
    color:#0B0E14; font-size:11px; font-weight:700;
  }
  .gauge-fill.orange { background: linear-gradient(90deg, #FFC857, #FF6B35); color:#0B0E14; }
  .gauge-fill.red { background: linear-gradient(90deg, #FF6B6B, #FF3B3B); color:#fff; }
  .verdict { margin-top: 18px; padding:14px 16px; border-radius:10px; font-size:13px; line-height:1.6;
    opacity: 0; transition: opacity 0.6s; }
  .verdict.show { opacity: 1; }
  .verdict.bad { background:rgba(255,107,107,0.1); border-left:3px solid #FF6B6B; color:#FFB3B3; }
  .verdict.good { background:rgba(35,197,82,0.1); border-left:3px solid #23C552; color:#A7EBBA; margin-top:8px; }
</style>
<div class="wrap">
  <div class="btn-row">
    <button class="go-btn" onclick="runGauge()">▶ 착석 시뮬레이션 실행</button>
  </div>
  <div class="gauge-row">
    <div class="gauge-label">🧍 서있음</div>
    <div class="gauge-track"><div class="gauge-fill" id="g1" style="width:92%">0.92</div></div>
  </div>
  <div class="gauge-row">
    <div class="gauge-label">🪑 앉는 중</div>
    <div class="gauge-track"><div class="gauge-fill" id="g2" style="width:92%">0.92</div></div>
  </div>
  <div class="gauge-row">
    <div class="gauge-label">🙈 앉음(가려짐)</div>
    <div class="gauge-track"><div class="gauge-fill" id="g3" style="width:92%">0.92</div></div>
  </div>
  <div class="verdict bad" id="v-bad"></div>
  <div class="verdict good" id="v-good"></div>
</div>
<script>
  async function runGauge() {
    ['g1','g2','g3'].forEach(id=>{
      const e=document.getElementById(id);
      e.style.width='92%'; e.textContent='0.92'; e.className='gauge-fill';
    });
    document.getElementById('v-bad').classList.remove('show');
    document.getElementById('v-good').classList.remove('show');
    await sleep(400);

    // g1 유지 (서있음)
    await sleep(600);
    // g2 앉는 중 → 0.65 (주황)
    const g2 = document.getElementById('g2');
    g2.style.width='65%'; g2.textContent='0.65'; g2.className='gauge-fill orange';
    await sleep(900);
    // g3 앉음(가려짐) → 0.25 (빨강)
    const g3 = document.getElementById('g3');
    g3.style.width='25%'; g3.textContent='0.25'; g3.className='gauge-fill red';
    await sleep(1100);

    const vb = document.getElementById('v-bad');
    vb.innerHTML = "❌ <b>DeepSORT</b>: conf 0.25 → 임계값 미만 → 탐지 폐기 → <b>ID 소멸</b>! 재등장 시 새 ID 부여 → 체류시간 리셋";
    vb.classList.add('show');
    await sleep(700);
    const vg = document.getElementById('v-good');
    vg.innerHTML = "✅ <b>ByteTrack</b>: 저신뢰 탐지도 버리지 않음 → Kalman 예측 위치와 IoU 매칭 성공 → <b>ID 유지!</b> 체류시간 계속 누적";
    vg.classList.add('show');
  }
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
</script>
"""


# --- 5d. 파이프라인 단계 하이라이트 위젯 --------------------------------------
PIPELINE_HIGHLIGHT_WIDGET = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .wrap { padding:14px; display:flex; flex-direction:column; align-items:center; }
  .go-btn { background:linear-gradient(135deg,#FF6B35,#FFC857); color:#0B0E14; font-weight:700;
    border:none; padding:10px 18px; border-radius:8px; cursor:pointer; font-size:12px; letter-spacing:0.06em; margin-bottom:18px; }
  .pipe-row { display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:center; }
  .pipe-stage {
    background:#151A24; border:1px solid rgba(255,255,255,0.08);
    border-radius:10px; padding:12px 14px; min-width:110px; text-align:center;
    opacity: 0.35; transform: scale(1); transition: all 0.6s;
  }
  .pipe-stage.active { opacity: 1; transform: scale(1.04); }
  .pipe-stage.active.latest { animation: pulseBorder 1.5s infinite; }
  .pipe-stage .icon { font-size: 22px; margin-bottom: 4px; }
  .pipe-stage .name { font-size: 12px; font-weight: 700; color: #F5F6F8; }
  .pipe-stage .sub { font-size: 10px; color: #8B95A5; margin-top: 2px; }
  .pipe-arrow { color: rgba(255,255,255,0.2); font-size:18px; transition: color 0.6s; }
  .pipe-arrow.active { color: #FF6B35; }
  @keyframes pulseBorder {
    0%,100% { box-shadow: 0 0 0 0 rgba(255,107,53,0.0); border-color: rgba(255,107,53,0.6); }
    50% { box-shadow: 0 0 0 4px rgba(255,107,53,0.18); border-color: rgba(255,107,53,0.9); }
  }
  .status { margin-top: 18px; color:#8B95A5; font-size:12px; text-align:center; max-width:480px; line-height:1.6; }
  .status b { color:#FFC857; }
</style>
<div class="wrap">
  <button class="go-btn" onclick="runPipe()">▶ 파이프라인 실행</button>
  <div class="pipe-row">
    <div class="pipe-stage" id="ps0">
      <div class="icon">📹</div>
      <div class="name">INPUT</div>
      <div class="sub">CCTV 프레임</div>
    </div>
    <span class="pipe-arrow" id="pa0">→</span>
    <div class="pipe-stage" id="ps1">
      <div class="icon">🧠</div>
      <div class="name">YOLO11-seg</div>
      <div class="sub">감지 + 마스크</div>
    </div>
    <span class="pipe-arrow" id="pa1">→</span>
    <div class="pipe-stage" id="ps2">
      <div class="icon">🔗</div>
      <div class="name">ByteTrack</div>
      <div class="sub">ID 할당</div>
    </div>
    <span class="pipe-arrow" id="pa2">→</span>
    <div class="pipe-stage" id="ps3">
      <div class="icon">📊</div>
      <div class="name">Metadata</div>
      <div class="sub">집계 JSON</div>
    </div>
    <span class="pipe-arrow" id="pa3">→</span>
    <div class="pipe-stage" id="ps4">
      <div class="icon">🤖</div>
      <div class="name">Claude LLM</div>
      <div class="sub">행동 지침</div>
    </div>
  </div>
  <div class="status" id="pipe-status">파이프라인이 대기 중입니다. 버튼을 눌러 각 단계가 순차 활성화되는 것을 확인하세요.</div>
</div>
<script>
  const stageMsgs = [
    "INPUT · 카페 CCTV 프레임이 들어옵니다 (720×804 · 15fps)",
    "YOLO11-seg · 격자 분할 → 모든 칸이 동시에 person 감지 → NMS로 중복 제거",
    "ByteTrack · 칼만 예측 → 고신뢰 매칭 → <b>저신뢰 재매칭(핵심)</b> → ID 일관성 유지",
    "Metadata · 좌표 기반 구역 분류 → 초별 집계 → 체류시간/혼잡도 계산",
    "Claude LLM · 운영 컨설팅 프롬프트 → JSON 스키마 강제 → <b>행동 지침 출력</b>",
  ];
  async function runPipe() {
    for (let i=0;i<5;i++) {
      document.getElementById('ps'+i).classList.remove('active','latest');
      if (i < 4) document.getElementById('pa'+i).classList.remove('active');
    }
    const statusEl = document.getElementById('pipe-status');
    await sleep(300);
    for (let i=0;i<5;i++) {
      // 이전 latest 해제
      if (i>0) document.getElementById('ps'+(i-1)).classList.remove('latest');
      document.getElementById('ps'+i).classList.add('active','latest');
      if (i>0) document.getElementById('pa'+(i-1)).classList.add('active');
      statusEl.innerHTML = stageMsgs[i];
      await sleep(900);
    }
  }
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
</script>
"""


# --- 6. 파이프라인 다이어그램 --------------------------------------------------
PIPELINE_DIAGRAM = """
<style>
  body { background: transparent; color:#E6E8EB; font-family:'Pretendard Variable', sans-serif; margin:0; }
  .pipeline { display:flex; flex-direction:column; gap:12px; padding:14px; align-items:center; }
  .node {
    width: 460px; background: #151A24; border:1px solid rgba(255,255,255,0.08);
    border-left: 4px solid var(--accent, #4F8BF9);
    border-radius: 10px; padding: 12px 16px;
    transition: transform 0.3s;
  }
  .node:hover { transform: translateX(4px); border-color: rgba(255,255,255,0.2); }
  .node-title { font-size: 13px; font-weight: 700; color: #F5F6F8; display:flex; justify-content:space-between; }
  .node-title .tag { font-size: 10px; color: var(--accent, #4F8BF9); letter-spacing: 0.1em; }
  .node-desc { font-size: 12px; color: #A0A7B4; margin-top: 6px; line-height: 1.55; }
  .node-out { font-size: 11px; color:#7FE5BA; margin-top: 6px; font-family: monospace; }
  .arrow-down {
    width: 2px; height: 20px; background: linear-gradient(180deg, rgba(255,255,255,0.3), rgba(255,255,255,0.05));
    position: relative;
  }
  .arrow-down:after {
    content: '▼'; position:absolute; bottom:-4px; left: -5px; color: rgba(255,255,255,0.4); font-size:10px;
  }
</style>
<div class="pipeline">
  <div class="node" style="--accent:#8B95A5">
    <div class="node-title">📹 CCTV 영상 입력 <span class="tag">RAW</span></div>
    <div class="node-desc">720×804 세로 프레임 · 15fps · h264 · 얼굴 블러 처리됨</div>
  </div>
  <div class="arrow-down"></div>
  <div class="node" style="--accent:#4F8BF9">
    <div class="node-title">🧠 YOLO11n-seg <span class="tag">DETECT + SEGMENT</span></div>
    <div class="node-desc">프레임당 격자 분할 → 모든 칸이 동시에 person class 탐지 → NMS로 중복 제거</div>
    <div class="node-out">→ bbox [x,y,w,h] · mask · conf ∈ [0,1]</div>
  </div>
  <div class="arrow-down"></div>
  <div class="node" style="--accent:#23C552">
    <div class="node-title">🔗 ByteTrack <span class="tag">TRACK</span></div>
    <div class="node-desc">칼만 예측 → 고신뢰 IoU 매칭 → 저신뢰 재매칭 → ID 일관성 유지</div>
    <div class="node-out">→ track_id 할당 · 가림 시에도 ID 지속</div>
  </div>
  <div class="arrow-down"></div>
  <div class="node" style="--accent:#FFC857">
    <div class="node-title">📊 메타데이터 추출 <span class="tag">AGGREGATE</span></div>
    <div class="node-desc">좌표 → 구역 매핑 → 초별 집계 → 체류시간 / 혼잡도 / 동선 패턴 계산</div>
    <div class="node-out">→ stats_sec*.json · tracking_data.json · zone_stats.json</div>
  </div>
  <div class="arrow-down"></div>
  <div class="node" style="--accent:#FF6B35">
    <div class="node-title">🤖 Claude LLM <span class="tag">INSIGHT</span></div>
    <div class="node-desc">운영 컨설팅 프롬프트 + JSON 스키마 강제 → 행동 지침 3개 + 예상 효과 생성</div>
    <div class="node-out">→ insight.json { headline, actions: [{text, impact, priority}], summary }</div>
  </div>
</div>
"""


# ------------------------------------------------------------------------------
def tech_hero():
    st.markdown(SECTION_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="tech-hero">
      <h2>🎓 YOLO & ByteTrack 작동 원리</h2>
      <p>"한 번만 보고 다 찾아내는 AI"와 "포기하지 않는 추적자"가 카페 CCTV에서 어떻게 협업하는지 살펴봅니다.
      직접 만져보는 인터랙티브 데모로 설명합니다.</p>
    </div>
    """, unsafe_allow_html=True)


def render_yolo_section():
    st.markdown('#### 📖 YOLO — *You Only Look Once*')
    st.markdown(
        '> **한 줄 요약**: 사진을 한 번 훑으면, 그 안에 있는 모든 사람/물건의 위치와 종류를 동시에 알아냅니다.'
    )

    with st.expander("🐢 전통 방식 (R-CNN) vs ⚡ YOLO — 왜 빠른가", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="concept-card">
              <div class="concept-title">🐢 전통 방식 (R-CNN)</div>
              <div class="concept-body">
                돋보기를 들고 <b>왼쪽 위부터 오른쪽 아래까지</b> 수천 번 이동하며
                "여기 사람? 여기 컵?"을 매번 물어봅니다.<br>
                → 정확하지만 1장당 <b>수 초</b> 소요
              </div>
              <div class="metaphor">🧑‍🏫 <b>비유</b>: 선생님 1명이 답안지 100장을 순서대로 채점</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="concept-card">
              <div class="concept-title">⚡ YOLO 방식</div>
              <div class="concept-body">
                사진을 바둑판처럼 격자로 나누고 <b>모든 칸이 동시에</b>
                "내 담당 구역에 뭐 있어?"를 대답합니다.<br>
                → 1초에 <b>30장 이상</b> 처리 가능
              </div>
              <div class="metaphor">🧑‍🎓 <b>비유</b>: 조교 100명이 1장씩 동시에 채점</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('##### 🎬 단계별로 만져보기')
    components.html(GRID_WIDGET, height=500, scrolling=False)

    st.markdown('##### 🧮 핵심 수학 4가지')
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="concept-card">
          <div class="concept-title">① 신뢰도 (Confidence)</div>
          <div class="concept-body">"이 칸에 사람이 있을 확률" × "상자가 얼마나 정확한지"</div>
          <div class="key-formula">Confidence = P(object) × IoU(pred, truth)</div>
          <div class="metaphor">예: P(사람)=0.95 × 상자 정확도 0.90 → <b>0.855</b></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="concept-card">
          <div class="concept-title">③ NMS — 중복 제거</div>
          <div class="concept-body">같은 사람에 상자 3개가 겹쳐 나오면, 신뢰도 1위만 남기고 나머지는 제거.</div>
          <div class="metaphor">🗳 <b>비유</b>: 반장 선거에서 1위가 당선되면 같은 반 2·3위는 탈락</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="concept-card">
          <div class="concept-title">② 바운딩 박스 (Bounding Box)</div>
          <div class="concept-body">중심점(cx, cy) + 크기(w, h) — 단 4개 숫자로 객체 위치 표현</div>
          <div class="key-formula">bbox = (cx, cy, w, h)</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="concept-card">
          <div class="concept-title">④ IoU (Intersection over Union)</div>
          <div class="concept-body">두 상자가 얼마나 겹치는지. 0 = 안 겹침, 1 = 완벽히 일치.</div>
          <div class="key-formula">IoU = 교집합 ÷ 합집합</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('##### 🎯 IoU 직접 계산해보기 (슬라이더를 움직여보세요)')
    components.html(IOU_WIDGET, height=330, scrolling=False)

    st.markdown('##### 🗳 NMS 시뮬레이션 — "같은 사람에 겹친 상자, 어떻게 하나만 남기는가"')
    components.html(NMS_WIDGET, height=430, scrolling=False)

    with st.expander("🎭 YOLO vs YOLO-seg (세그먼테이션)"):
        st.markdown("""
        <div class="concept-card">
          <div class="concept-body">
            <b>일반 YOLO</b>는 사각형 바운딩 박스만 출력 → 상자 안에 배경도 포함됨.<br>
            <b>YOLO-seg</b>는 각 픽셀이 사람에 속하는지를 0/1로 판정한 <b>마스크(mask)</b>를 함께 출력 →
            실루엣을 따라 정확히 색칠.<br><br>
            <b>이 프로젝트가 YOLO-seg를 쓰는 이유</b>: 정확한 면적 계산, 겹침 판단, 시각적 효과 (색칠된 사람이
            데모의 임팩트를 만듦).
          </div>
        </div>
        """, unsafe_allow_html=True)


def render_bytetrack_section():
    st.markdown('#### 🔗 ByteTrack — *포기하지 않는 추적자*')
    st.markdown(
        '> **한 줄 요약**: YOLO가 매 프레임마다 찾아낸 사람들을 이어 붙여서, '
        '"이 사람이 프레임 1부터 200까지 쭉 같은 사람"이라는 걸 알아냅니다.'
    )

    with st.expander("❓ 왜 추적이 필요한가?", expanded=True):
        st.markdown("""
        <div class="concept-card">
          <div class="concept-body">
            YOLO는 <b>한 프레임만</b> 봅니다. "지금 8명 있다"는 알지만,
            "3초 전에도 여기 앉아있던 그 사람인지"는 모릅니다.<br><br>
            추적이 되어야 <b>체류 시간</b>이 계산됩니다.
            "ID-3 손님이 좌석A에 47분째 체류" → 추적 없이는 불가능.
          </div>
        </div>
        """, unsafe_allow_html=True)

    step1, step2, step3 = st.tabs(["① 칼만 필터", "② 고신뢰 매칭", "③ 저신뢰 매칭 🌟"])

    with step1:
        st.markdown("##### 📐 다음 프레임에 어디 있을지 예측")
        c1, c2 = st.columns([3, 2])
        with c1:
            components.html(KALMAN_WIDGET, height=360, scrolling=False)
        with c2:
            st.markdown("""
            <div class="concept-card">
              <div class="concept-body">
                각 사람의 <b>이동 패턴</b>을 추정해 다음 위치를 예측.<br>
              </div>
              <div class="key-formula">x' = x + vx × Δt<br>y' = y + vy × Δt</div>
              <div class="metaphor">
                🚗 <b>비유</b>: 네비게이션이 터널에서 GPS 끊겨도 마지막 속도·방향으로 위치 추정
              </div>
              <div class="concept-body" style="margin-top:10px">
                상태 벡터: <code>[cx, cy, a, h, vx, vy, va, vh]</code><br>
                (위치 4차원 + 속도 4차원)
              </div>
            </div>
            """, unsafe_allow_html=True)

    with step2:
        st.markdown("##### 🎯 확실한 것부터 연결 — 헝가리안 알고리즘")
        st.markdown("""
        <div class="concept-card">
          <div class="concept-body">
            YOLO 탐지 중 <b>신뢰도 ≥ 0.5</b>인 것만 먼저 추려냄. 기존 트랙(칼만 예측 위치)과
            탐지를 <b>IoU 비용 행렬</b>로 비교해 전체 비용이 최소가 되는 매칭을 찾음.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**예시 비용 행렬 (IoU, 높을수록 좋음):**")
        st.code("""
              탐지A(0.91)   탐지B(0.88)   탐지D(0.79)
ID-1 예측      0.82          0.05         0.01
ID-2 예측      0.03          0.76         0.12
ID-3 예측      0.01          0.08         0.02

헝가리안 최적해:
  ID-1 ↔ 탐지A (0.82)  ✓
  ID-2 ↔ 탐지B (0.76)  ✓
  ID-3 ↔ ?            ✗ → Step 3으로
        """, language="text")
        st.markdown("""
        <div class="metaphor">
          🚕 <b>비유</b>: 택시 배차 시스템 — 승객 3명·택시 3대일 때 전체 이동거리가 최소가 되는 배차를 찾기
        </div>
        """, unsafe_allow_html=True)

    with step3:
        st.markdown("##### ⭐ ByteTrack만의 결정적 차별점")
        st.markdown("""
        <div class="concept-card">
          <div class="concept-body">
            <b>다른 트래커(DeepSORT)는</b> "신뢰도 0.25? 노이즈겠지" 하고 <b>버립니다</b>.<br>
            → ID 소멸 → 재등장 시 새 ID → 체류시간 초기화 (오류!)<br><br>
            <b>ByteTrack은</b> 버려진 저신뢰 탐지를 한 번 더 씁니다. 칼만이 예측한 위치와 IoU를
            계산해 미매칭 트랙과 재연결.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('**📊 신뢰도 게이지 변화 — "앉는 순간 왜 신뢰도가 무너지는가"**')
        components.html(CONFIDENCE_GAUGE_WIDGET, height=400, scrolling=False)

        st.markdown('**🔗 프레임 간 추적 연결 — "같은 색 = 같은 사람"**')
        components.html(TRACKING_LINK_WIDGET, height=280, scrolling=False)

        st.markdown('**📹 프레임 단위 비교 — DeepSORT vs ByteTrack**')
        components.html(BYTETRACK_WIDGET, height=480, scrolling=False)

        st.markdown("""
        <div class="metaphor">
          ☕ <b>왜 카페에서 결정적인가</b>: CCTV 상단 뷰 → 손님이 앉으면 테이블/의자에 가려져 신뢰도 0.9 → 0.3으로 급락.
          일반 트래커면 그 순간 ID가 바뀌어 "2시간 앉아있던 손님"이 여러 명으로 쪼개져 측정됩니다.
          ByteTrack은 이 불확실 구간을 붙잡아 <b>ID를 유지</b>합니다.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🆚 ByteTrack vs DeepSORT 한눈에"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="concept-card">
              <div class="concept-title" style="color:#FF6B6B">DeepSORT</div>
              <div class="concept-body">
                • 외모 특징(Re-ID)에 의존<br>
                • 추가 CNN 모델 필요 → <b>무거움</b><br>
                • 저신뢰 탐지는 <b>버림</b><br>
                • 색깔/체형 바뀌면 혼동
              </div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="concept-card">
              <div class="concept-title" style="color:#23C552">ByteTrack</div>
              <div class="concept-body">
                • 위치(IoU)만으로 매칭<br>
                • 추가 모델 불필요 → <b>가볍고 빠름</b><br>
                • 저신뢰 탐지 <b>재활용</b><br>
                • 가림·혼잡에 강건
              </div>
            </div>
            """, unsafe_allow_html=True)


def render_pipeline_section():
    st.markdown('#### 🛠 전체 파이프라인 — 입력부터 인사이트까지')
    st.markdown("##### ⚡ 파이프라인 단계별 하이라이트 (버튼 클릭)")
    components.html(PIPELINE_HIGHLIGHT_WIDGET, height=300, scrolling=False)
    st.markdown("##### 📋 단계별 입출력 상세")
    components.html(PIPELINE_DIAGRAM, height=720, scrolling=False)


def render_faq_section():
    st.markdown('#### 💬 자주 나오는 질문')
    faqs = [
        ("정확도는 어떻게 되나요?",
         "범용 COCO 모델 기준 사람 탐지 정확도는 약 **80~90%**. 정수리 뷰·가려짐에서는 더 떨어지지만, "
         "우리의 목표는 99% 정확도가 아닙니다. **\"저 테이블이 비정상적으로 오래 차지되고 있다\"는 맥락 파악에는 80%면 충분**합니다. "
         "카페 특화 파인튜닝(로드맵 2단계)으로 개선 예정."),
        ("실시간으로 되는 건가요?",
         "YOLO11 nano는 GPU에서 **30fps 이상** 처리. 카페 CCTV는 보통 15fps이므로 충분히 실시간. "
         "CPU에서도 **5~10fps** 처리 가능 (이 데모는 CPU에서 전처리 후 재생 연출)."),
        ("개인정보는 어떻게 처리하나요?",
         "영상은 분석 직후 **폐기**. 저장되는 것은 \"좌석A에서 47분 체류\" 같은 **비식별 메타데이터**뿐입니다. "
         "얼굴 특징점·원본 영상·생체정보는 시스템이 보관하지 않습니다. 이 데모에 쓰인 영상은 **크리에이터가 사전 블러 처리**한 것."),
        ("ByteTrack이 뭐가 특별한가요?",
         "기존 트래커는 YOLO가 '신뢰도 25%'라고 하면 **무시**합니다. 카페에선 테이블에 가려져 신뢰도가 떨어지는 게 일상입니다. "
         "ByteTrack은 이런 불확실한 탐지도 **포기하지 않고** 추적을 이어갑니다. 덕분에 손님이 앉아있는 동안 ID가 바뀌지 않아 체류시간을 정확히 측정."),
        ("왜 YOLO-seg를 쓰나요? 일반 YOLO로 충분하지 않나요?",
         "세그먼테이션이 주는 **시각적 임팩트**가 커서 데모에선 seg 선택. "
         "기술적으로는 픽셀 단위 면적 계산이 가능해져서 정확한 '좌석 점유 판정'이나 '혼잡 밀도 heatmap'에 유리. "
         "로드맵 후기 단계에서 더 중요해집니다."),
        ("LLM은 뭐하러 쓰나요? 숫자만 보여주면 안 되나요?",
         "데이터 나열은 **사장님이 해석**해야 합니다. 바쁘게 커피 내리는 사장님이 그럴 시간이 없죠. "
         "LLM이 \"창가 노트북족 체류 길어짐 → 30분마다 음료 리필 제안\"처럼 **즉시 행동 가능한 지침**으로 변환해야 "
         "비로소 '자율주행 택시'급 솔루션이 됩니다."),
    ]
    for q, a in faqs:
        with st.expander(f"❓ {q}"):
            st.markdown(a)


def render_tech_tab():
    tech_hero()
    sub = st.tabs([
        "🧠 YOLO 원리",
        "🔗 ByteTrack 원리",
        "🛠 파이프라인",
        "💬 FAQ",
    ])
    with sub[0]:
        render_yolo_section()
    with sub[1]:
        render_bytetrack_section()
    with sub[2]:
        render_pipeline_section()
    with sub[3]:
        render_faq_section()

"""
Phase 1-b: 추적 데이터 → LLM 단일 호출 → insight.json 저장
ANTHROPIC_API_KEY 없으면 폴백 인사이트 작성.
actions 스키마: [{text, impact, priority}]  priority ∈ {urgent, improve, optimize}
"""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

FALLBACK = {
    "headline": "창가 좌석 회전율 저하 가능성 — 테이블 정리 라운딩 권장",
    "actions": [
        {
            "text": "좌석A(노트북 구역) 체류가 긴 고객 비율이 높음. 30분 단위 간단 음료 리필 서비스로 회전율 체감 개선.",
            "impact": "예상 회전율 +15%",
            "priority": "urgent",
        },
        {
            "text": "주문구역에 3인 이상 동시 대기 장면 포착. 자판기 앞 바닥 안내선으로 동선 충돌 방지.",
            "impact": "동선 충돌 -30%",
            "priority": "improve",
        },
        {
            "text": "좌석B(대화 구역)의 테이블 사용이 꾸준함. 오후 피크타임엔 2인 테이블을 창가로 재배치 고려.",
            "impact": "배치 효율 +8%",
            "priority": "optimize",
        },
    ],
    "summary": "단일 카메라 13초 영상 기준, 좌석A 노트북족 체류/주문구역 혼잡/좌석B 대화 고객이라는 3축 패턴이 관찰됨. 회전율 + 동선 + 배치 3가지를 작은 개입으로 개선 가능.",
    "source": "fallback",
}


def build_prompt(tracking: dict, zone_stats: dict) -> str:
    fps = tracking["fps"]
    n_tracks = len(tracking["dwell_seconds_by_track"])
    peak_count = max(tracking["per_frame_count"]) if tracking["per_frame_count"] else 0
    avg_count = (
        sum(tracking["per_frame_count"]) / len(tracking["per_frame_count"])
        if tracking["per_frame_count"] else 0
    )
    compact = {
        "영상_길이_초": round(tracking["total_frames"] / fps, 1),
        "해상도": f"{tracking['width']}x{tracking['height']}",
        "고유_인원_수": n_tracks,
        "평균_동시_인원": round(avg_count, 1),
        "최대_동시_인원": peak_count,
        "구역별_총_체류시간_초": zone_stats["zones"],
        "개별_체류_샘플": dict(list(tracking["dwell_seconds_by_track"].items())[:8]),
        "구역_정의": {
            "좌석A": "왼쪽 하단, 노트북 사용자",
            "좌석B": "왼쪽 상단, 대화 고객",
            "주문구역": "오른쪽, 자판기/주문",
        },
    }
    return (
        "당신은 무인카페 운영 컨설턴트입니다. 다음은 CCTV 13초 구간의 YOLO 추적 분석 결과입니다.\n"
        "이 데이터를 보고 사장님이 당장 실행할 수 있는 행동 지침 3가지를 제안하세요.\n"
        "각 action은 priority(urgent|improve|optimize 중 하나)와 정량적 impact 문구를 포함해야 합니다.\n"
        "반드시 JSON만 출력하세요. 스키마:\n"
        '{"headline": string, '
        '"actions": [{"text": string, "impact": string, "priority": "urgent"|"improve"|"optimize"}, '
        '{"text": string, "impact": string, "priority": "urgent"|"improve"|"optimize"}, '
        '{"text": string, "impact": string, "priority": "urgent"|"improve"|"optimize"}], '
        '"summary": string}\n\n'
        f"분석 데이터:\n{json.dumps(compact, ensure_ascii=False, indent=2)}\n"
    )


def call_claude(prompt: str) -> dict | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[warn] ANTHROPIC_API_KEY 없음 → 폴백 사용")
        return None
    try:
        import anthropic
    except ImportError:
        print("[warn] anthropic 미설치 → 폴백 사용")
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        data["source"] = "claude"
        return data
    except Exception as e:
        print(f"[warn] Claude 호출 실패: {e} → 폴백 사용")
        return None


def main() -> None:
    tracking = json.loads((DATA / "tracking_data.json").read_text(encoding="utf-8"))
    zone_stats = json.loads((DATA / "zone_stats.json").read_text(encoding="utf-8"))

    prompt = build_prompt(tracking, zone_stats)
    insight = call_claude(prompt) or FALLBACK

    out = DATA / "insight.json"
    out.write_text(json.dumps(insight, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] insight → {out} (source={insight.get('source')})")
    print(f"  headline: {insight['headline']}")


if __name__ == "__main__":
    main()

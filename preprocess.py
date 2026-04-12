"""
Phase 1: YOLO11n-seg + ByteTrack 추론 → 프레임/통계/추적데이터 저장
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).parent
DATA = ROOT / "data"
FRAMES_DIR = DATA / "frames"
FRAMES_RAW_DIR = DATA / "frames_raw"
STATS_DIR = DATA / "stats"
VIDEO = DATA / "cafe_video.mp4"

FRAMES_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_RAW_DIR.mkdir(parents=True, exist_ok=True)
STATS_DIR.mkdir(parents=True, exist_ok=True)


def get_zone(cx: float, cy: float) -> str:
    if cx < 400 and cy > 300:
        return "좌석A"
    if cx < 400 and cy <= 300:
        return "좌석B"
    return "주문구역"


def main() -> None:
    if not VIDEO.exists():
        raise FileNotFoundError(f"영상 없음: {VIDEO}")

    cap = cv2.VideoCapture(str(VIDEO))
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    print(f"[video] {w}x{h} {fps:.1f}fps {total_frames}frames")

    model = YOLO("yolo11n-seg.pt")

    cap = cv2.VideoCapture(str(VIDEO))
    raw_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imwrite(
            str(FRAMES_RAW_DIR / f"frame_{raw_idx:04d}.jpg"),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 85],
        )
        raw_idx += 1
    cap.release()
    print(f"[raw] {raw_idx} frames → {FRAMES_RAW_DIR}")

    tracker_yaml = ROOT / "bytetrack.yaml"
    tracker_arg = str(tracker_yaml) if tracker_yaml.exists() else "bytetrack.yaml"

    tracking_rows: list[dict] = []
    per_frame_count: list[int] = []
    per_frame_zone: list[dict[str, int]] = []
    track_zone_durations: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    track_path: dict[int, list[tuple[float, float, int]]] = defaultdict(list)

    results = model.track(
        source=str(VIDEO),
        tracker=tracker_arg,
        classes=[0],
        conf=0.25,
        iou=0.5,
        persist=True,
        stream=True,
        verbose=False,
    )

    for frame_idx, r in enumerate(results):
        rendered = r.plot()
        out_path = FRAMES_DIR / f"frame_{frame_idx:04d}.jpg"
        cv2.imwrite(str(out_path), rendered, [cv2.IMWRITE_JPEG_QUALITY, 85])

        zones_in_frame: dict[str, int] = defaultdict(int)
        count = 0
        if r.boxes is not None and r.boxes.id is not None:
            ids = r.boxes.id.cpu().numpy().astype(int)
            xyxy = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            for tid, box, cf in zip(ids, xyxy, confs):
                x1, y1, x2, y2 = box
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                zone = get_zone(cx, cy)
                zones_in_frame[zone] += 1
                track_zone_durations[int(tid)][zone] += 1
                track_path[int(tid)].append((float(cx), float(cy), frame_idx))
                tracking_rows.append({
                    "frame": frame_idx,
                    "track_id": int(tid),
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "center": [float(cx), float(cy)],
                    "zone": zone,
                    "conf": float(cf),
                })
                count += 1
        per_frame_count.append(count)
        per_frame_zone.append(dict(zones_in_frame))
        if frame_idx % 15 == 0:
            print(f"  frame {frame_idx:03d}: {count} person(s)")

    n_frames = len(per_frame_count)
    fps_int = max(1, int(round(fps)))
    n_seconds = max(1, (n_frames + fps_int - 1) // fps_int)

    for sec in range(n_seconds):
        start = sec * fps_int
        end = min(n_frames, start + fps_int)
        counts = per_frame_count[start:end]
        zones_agg: dict[str, int] = defaultdict(int)
        for z in per_frame_zone[start:end]:
            for k, v in z.items():
                zones_agg[k] += v
        denom = max(1, len(counts))
        payload = {
            "second": sec,
            "person_count": int(round(sum(counts) / denom)) if counts else 0,
            "person_count_max": int(max(counts)) if counts else 0,
            "zones_avg": {k: round(v / denom, 2) for k, v in zones_agg.items()},
            "frame_range": [start, end - 1],
        }
        (STATS_DIR / f"stats_sec{sec:02d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    dwell_seconds: dict[str, dict[str, float]] = {}
    for tid, zmap in track_zone_durations.items():
        dwell_seconds[str(tid)] = {z: round(f / fps, 2) for z, f in zmap.items()}

    zone_stats = {
        "zones": {},
        "total_unique_persons": len(track_zone_durations),
        "total_frames": n_frames,
        "fps": fps,
    }
    all_zone_totals: dict[str, float] = defaultdict(float)
    for tid, zmap in track_zone_durations.items():
        for z, f in zmap.items():
            all_zone_totals[z] += f / fps
    zone_stats["zones"] = {z: round(s, 2) for z, s in all_zone_totals.items()}

    (DATA / "tracking_data.json").write_text(
        json.dumps({
            "fps": fps,
            "width": w,
            "height": h,
            "total_frames": n_frames,
            "rows": tracking_rows,
            "dwell_seconds_by_track": dwell_seconds,
            "per_frame_count": per_frame_count,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (DATA / "zone_stats.json").write_text(
        json.dumps(zone_stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[done] {n_frames} frames → {FRAMES_DIR}")
    print(f"[done] {n_seconds} sec stats → {STATS_DIR}")
    print(f"[done] unique tracks: {len(track_zone_durations)}")
    print(f"[done] zone totals (sec): {dict(all_zone_totals)}")


if __name__ == "__main__":
    main()

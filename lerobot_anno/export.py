"""Pure pandas/pyarrow export of FiftyOne annotations to a LeRobot v3.0 copy.

Adapted from /Users/burhan/Documents/_code/lerobot-annotate (backend/app.py).
No FiftyOne imports here so it is unit-testable in isolation.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


def make_task_key(seg: dict[str, Any]) -> str:
    return "||".join(
        [
            seg.get("user_prompt", "") or "",
            seg.get("robot_utterance", "") or "",
            seg.get("skill", "") or "",
            seg.get("scenario_type", "") or "",
            seg.get("response_type", "") or "",
        ]
    )


def build_subtasks_dataframe(
    annotations: dict[int, dict],
) -> tuple[pd.DataFrame, dict[str, int]]:
    labels = sorted(
        {
            seg["label"]
            for ann in annotations.values()
            for seg in ann.get("subtasks", [])
            if seg.get("label")
        }
    )
    df = pd.DataFrame(
        [{"subtask": lbl, "subtask_index": i} for i, lbl in enumerate(labels)]
    )
    if not df.empty:
        df = df.set_index("subtask")
    return df, {lbl: i for i, lbl in enumerate(labels)}


def build_high_level_dataframe(
    annotations: dict[int, dict],
) -> tuple[pd.DataFrame, dict[str, int]]:
    task_map: dict[str, int] = {}
    ordered: list[dict] = []
    for ann in annotations.values():
        for seg in ann.get("high_levels", []):
            key = make_task_key(seg)
            if key not in task_map:
                task_map[key] = len(task_map)
                ordered.append(seg)
    rows = [
        {
            "task": f"{seg.get('user_prompt', '')} | {seg.get('robot_utterance', '')}",
            "task_index": task_map[make_task_key(seg)],
            "user_prompt": seg.get("user_prompt", ""),
            "robot_utterance": seg.get("robot_utterance", ""),
            "skill": seg.get("skill") or "",
            "scenario_type": seg.get("scenario_type") or "",
            "response_type": seg.get("response_type") or "",
        }
        for seg in ordered
    ]
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.set_index("task")
    return df, task_map


def assign_indices_by_segments(timestamps, segments, mapping, label_key):
    values = [-1] * len(timestamps)
    if not segments:
        return values
    segments_sorted = sorted(segments, key=lambda s: float(s.get("start", 0)))
    for i, ts in enumerate(timestamps):
        ts_val = float(ts)
        for seg_idx, seg in enumerate(segments_sorted):
            start = float(seg.get("start", 0))
            end = float(seg.get("end", 0))
            is_last = seg_idx == len(segments_sorted) - 1
            if (start <= ts_val < end) or (is_last and ts_val <= end):
                label = (
                    make_task_key(seg)
                    if label_key == "task_key"
                    else seg.get(label_key, "")
                )
                values[i] = mapping.get(label, -1)
                break
    return values


def export_lerobot(lerobot_root, output_dir, annotations, copy_videos=False):
    root = Path(lerobot_root)
    out = Path(output_dir)
    if (root / "meta" / "info.json").exists() is False:
        raise FileNotFoundError(f"Missing {root / 'meta' / 'info.json'}")
    data_files = sorted((root / "data").rglob("*.parquet"))
    if not data_files:
        raise FileNotFoundError(f"No data parquet under {root / 'data'}")
    if out.resolve() == root.resolve():
        raise ValueError("output_dir must differ from lerobot_root")
    out.mkdir(parents=True, exist_ok=True)

    dst_meta = out / "meta"
    if dst_meta.exists():
        shutil.rmtree(dst_meta)
    shutil.copytree(root / "meta", dst_meta)

    subtasks_df, subtask_map = build_subtasks_dataframe(annotations)
    tasks_df, task_map = build_high_level_dataframe(annotations)
    if not subtasks_df.empty:
        subtasks_df.to_parquet(
            dst_meta / "subtasks.parquet", engine="pyarrow", compression="snappy"
        )
    if not tasks_df.empty:
        tasks_df.to_parquet(
            dst_meta / "tasks_high_level.parquet",
            engine="pyarrow",
            compression="snappy",
        )

    info = json.loads((dst_meta / "info.json").read_text())
    info.setdefault("features", {})
    info["features"].setdefault(
        "subtask_index", {"dtype": "int64", "shape": [1], "names": None}
    )
    info["features"].setdefault(
        "task_index_high_level", {"dtype": "int64", "shape": [1], "names": None}
    )
    (dst_meta / "info.json").write_text(json.dumps(info, indent=2))

    for src_path in data_files:
        dst_path = out / src_path.relative_to(root)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.read_parquet(src_path)
        df["subtask_index"] = -1
        df["task_index_high_level"] = -1
        for ep_idx in df["episode_index"].unique():
            ann = annotations.get(int(ep_idx))
            if not ann:
                continue
            mask = df["episode_index"] == ep_idx
            if ann.get("subtasks") and subtask_map:
                df.loc[mask, "subtask_index"] = assign_indices_by_segments(
                    df.loc[mask, "timestamp"], ann["subtasks"], subtask_map, "label"
                )
            if ann.get("high_levels") and task_map:
                df.loc[mask, "task_index_high_level"] = assign_indices_by_segments(
                    df.loc[mask, "timestamp"], ann["high_levels"], task_map, "task_key"
                )
        df.to_parquet(dst_path, engine="pyarrow", compression="snappy", index=False)

    src_videos = root / "videos"
    dst_videos = out / "videos"
    if src_videos.exists():
        if dst_videos.is_symlink():
            dst_videos.unlink()
        elif dst_videos.exists():
            shutil.rmtree(dst_videos)
        if copy_videos:
            shutil.copytree(src_videos, dst_videos)
        else:
            try:
                os.symlink(src_videos, dst_videos)
            except OSError:
                shutil.copytree(src_videos, dst_videos)

    return {
        "output_dir": str(out),
        "num_subtasks": len(subtask_map),
        "num_tasks_high_level": len(task_map),
        "num_episodes_annotated": len(annotations),
    }

import json
from pathlib import Path

import pandas as pd

from lerobot_anno.export import assign_indices_by_segments, export_lerobot


def _make_root(tmp_path: Path) -> Path:
    root = tmp_path / "src"
    (root / "meta").mkdir(parents=True)
    (root / "data" / "chunk-000").mkdir(parents=True)
    (root / "videos").mkdir(parents=True)
    (root / "meta" / "info.json").write_text(
        json.dumps({"codebase_version": "v3.0", "fps": 10, "features": {}})
    )
    rows = [
        {"episode_index": ep, "frame_index": i, "timestamp": round(i / 10, 3)}
        for ep in (0, 1)
        for i in range(5)
    ]
    pd.DataFrame(rows).to_parquet(
        root / "data" / "chunk-000" / "file-000.parquet", engine="pyarrow"
    )
    return root


def test_export_assigns_indices(tmp_path):
    root = _make_root(tmp_path)
    out = tmp_path / "out"
    annotations = {
        0: {
            "subtasks": [
                {"start": 0.0, "end": 0.25, "label": "reach"},
                {"start": 0.25, "end": 0.5, "label": "grasp"},
            ],
            "high_levels": [
                {
                    "start": 0.0,
                    "end": 0.5,
                    "user_prompt": "pick it up",
                    "robot_utterance": "ok",
                    "skill": "",
                    "scenario_type": "",
                    "response_type": "",
                },
            ],
        }
    }
    result = export_lerobot(str(root), str(out), annotations, copy_videos=True)
    assert result["num_subtasks"] == 2
    assert result["num_tasks_high_level"] == 1
    assert result["num_episodes_annotated"] == 1

    df = pd.read_parquet(out / "data" / "chunk-000" / "file-000.parquet")
    ep0 = df[df.episode_index == 0].sort_values("frame_index")
    # labels sorted alphabetically -> grasp=0, reach=1
    assert list(ep0.subtask_index) == [1, 1, 1, 0, 0]
    assert list(ep0.task_index_high_level) == [0, 0, 0, 0, 0]
    assert set(df[df.episode_index == 1].subtask_index) == {-1}

    assert (out / "meta" / "subtasks.parquet").exists()
    assert (out / "meta" / "tasks_high_level.parquet").exists()
    info = json.loads((out / "meta" / "info.json").read_text())
    assert "subtask_index" in info["features"]
    assert "task_index_high_level" in info["features"]


def test_export_rejects_same_dir(tmp_path):
    root = _make_root(tmp_path)
    import pytest

    with pytest.raises(ValueError):
        export_lerobot(str(root), str(root), {})


def test_gap_and_pre_segment_frames_unlabeled():
    # Non-contiguous segments with a gap; frames before the first segment and
    # inside the gap must stay -1 (not inherit the last segment's index).
    segs = [
        {"start": 0.0, "end": 0.2, "label": "a"},
        {"start": 0.5, "end": 0.8, "label": "b"},
    ]
    mapping = {"a": 0, "b": 1}
    got = assign_indices_by_segments([-1.0, 0.1, 0.3, 0.6, 0.9], segs, mapping, "label")
    assert got == [-1, 0, -1, 1, -1]

import fiftyone as fo
from fiftyone import Group

from lerobot_anno.segments import (
    seconds_to_support,
    resolve_anchor_sample,
    get_episode_segments,
    save_segment,
    delete_segment,
    gather_annotations,
)


def _grouped():
    d = fo.Dataset()  # non-persistent (cleared at session end)
    d.add_group_field("group", default="up")
    g = Group()
    up = fo.Sample(filepath="/tmp/ep0_up.mp4", group=g.element("up"), episode_index=0)
    side = fo.Sample(
        filepath="/tmp/ep0_side.mp4", group=g.element("side"), episode_index=0
    )
    d.add_samples([up, side])
    d.info = {"fps": 10}
    d.save()
    return d, side.id  # NON-default slice id, as the modal may pass


def test_seconds_to_support():
    assert seconds_to_support(0.0, 0.5, 10, 100) == [1, 6]
    assert seconds_to_support(0.0, 0.0, 10, 100) == [1, 1]
    assert seconds_to_support(0.0, 100.0, 10, 50) == [1, 50]
    assert seconds_to_support(0.0, 0.5, 0, None) == [
        1,
        1,
    ]  # fps unknown -> degrade, no crash


def test_anchor_is_default_slice():
    d, side_id = _grouped()
    anchor = resolve_anchor_sample(d, side_id)
    assert anchor.group.name == "up"
    assert anchor.episode_index == 0


def test_save_get_update_gather_delete():
    d, side_id = _grouped()
    r = save_segment(
        d, side_id, "subtask", {"start_s": 0.0, "end_s": 0.5, "label": "reach"}
    )
    assert r["ok"] and r["id"]
    save_segment(
        d,
        side_id,
        "high_level",
        {"start_s": 0.0, "end_s": 0.5, "user_prompt": "pick", "robot_utterance": "ok"},
    )

    data = get_episode_segments(d, side_id)
    assert data["episode_index"] == 0 and data["fps"] == 10
    assert len(data["subtasks"]) == 1 and data["subtasks"][0]["label"] == "reach"
    assert data["subtasks"][0]["start_s"] == 0.0
    assert data["high_level"][0]["user_prompt"] == "pick"

    sid = data["subtasks"][0]["id"]
    save_segment(
        d,
        side_id,
        "subtask",
        {"id": sid, "start_s": 0.1, "end_s": 0.6, "label": "grasp"},
    )
    data2 = get_episode_segments(d, side_id)
    assert len(data2["subtasks"]) == 1 and data2["subtasks"][0]["label"] == "grasp"
    assert data2["subtasks"][0]["id"] == sid

    ann = gather_annotations(d)
    assert set(ann) == {0}
    assert ann[0]["subtasks"][0] == {"start": 0.1, "end": 0.6, "label": "grasp"}
    assert ann[0]["high_levels"][0]["user_prompt"] == "pick"

    delete_segment(d, side_id, "subtask", sid)
    assert len(get_episode_segments(d, side_id)["subtasks"]) == 0

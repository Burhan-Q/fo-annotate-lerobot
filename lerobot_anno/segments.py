"""Read/write per-episode segments as TemporalDetections on the group's
default-slice anchor sample, plus seconds<->frame conversion and export gather."""


import fiftyone as fo

SUBTASK_FIELD = "subtasks"
HIGH_LEVEL_FIELD = "high_level"
FIELD_FOR_KIND = {"subtask": SUBTASK_FIELD, "high_level": HIGH_LEVEL_FIELD}
DIALOG_ATTRS = (
    "user_prompt",
    "robot_utterance",
    "skill",
    "scenario_type",
    "response_type",
)


def seconds_to_support(start_s, end_s, fps, num_frames=None):
    fps = float(fps or 0)
    first = int(round(float(start_s) * fps)) + 1
    last = int(round(float(end_s) * fps)) + 1
    if num_frames:
        first = min(first, int(num_frames))
        last = min(last, int(num_frames))
    first = max(1, first)
    last = max(first, last)
    return [first, last]


def resolve_anchor_sample(dataset, sample_id):
    sample = dataset[sample_id]
    if dataset.media_type != "group":
        return sample
    return dataset.get_group(sample.group.id)[dataset.default_group_slice]


def episode_fps_frames(dataset, sample):
    md = sample.metadata
    fps = getattr(md, "frame_rate", None) if md else None
    nframes = getattr(md, "total_frame_count", None) if md else None
    info = dataset.info or {}
    if not fps:
        fps = info.get("fps")
    if not nframes and sample.media_type == "video":
        nframes = len(sample.frames)
    return (float(fps) if fps else None), (int(nframes) if nframes else None)


def _serialize(sample, field):
    out = []
    dets = sample[field] if sample.has_field(field) else None
    if dets is None:
        return out
    for d in dets.detections:
        item = {
            "id": d.id,
            "label": d.label,
            "support": list(d.support) if d.support else None,
            "start_s": getattr(d, "start_s", None),
            "end_s": getattr(d, "end_s", None),
        }
        for k in DIALOG_ATTRS:
            v = getattr(d, k, None)
            if v is not None:
                item[k] = v
        out.append(item)
    return out


def get_episode_segments(dataset, sample_id):
    anchor = resolve_anchor_sample(dataset, sample_id)
    fps, num_frames = episode_fps_frames(dataset, anchor)
    return {
        "episode_index": int(anchor["episode_index"])
        if anchor.has_field("episode_index") and anchor["episode_index"] is not None
        else None,
        "fps": fps,
        "num_frames": num_frames,
        "subtasks": _serialize(anchor, SUBTASK_FIELD),
        "high_level": _serialize(anchor, HIGH_LEVEL_FIELD),
    }


def save_segment(dataset, sample_id, kind, segment):
    field = FIELD_FOR_KIND[kind]
    anchor = resolve_anchor_sample(dataset, sample_id)
    fps, num_frames = episode_fps_frames(dataset, anchor)
    support = seconds_to_support(segment["start_s"], segment["end_s"], fps, num_frames)
    attrs = {"start_s": float(segment["start_s"]), "end_s": float(segment["end_s"])}
    if kind == "high_level":
        for k in DIALOG_ATTRS:
            attrs[k] = segment.get(k) or ""
        label = segment.get("user_prompt") or "dialogue"
    else:
        label = segment["label"]

    dets = (
        anchor[field]
        if anchor.has_field(field) and anchor[field] is not None
        else fo.TemporalDetections()
    )
    seg_id = segment.get("id")
    if seg_id:
        target = next((d for d in dets.detections if d.id == seg_id), None)
        if target is None:
            raise ValueError(f"segment id {seg_id} not found in '{field}'")
        target.label = label
        target.support = support
        for k, v in attrs.items():
            target[k] = v
        out_id = target.id
    else:
        det = fo.TemporalDetection(label=label, support=support, **attrs)
        dets.detections = list(dets.detections) + [det]
        out_id = det.id
    anchor[field] = dets
    anchor.save()
    return {"ok": True, "id": out_id}


def delete_segment(dataset, sample_id, kind, seg_id):
    field = FIELD_FOR_KIND[kind]
    anchor = resolve_anchor_sample(dataset, sample_id)
    dets = anchor[field] if anchor.has_field(field) else None
    if dets is not None:
        dets.detections = [d for d in dets.detections if d.id != seg_id]
        anchor[field] = dets
        anchor.save()
    return {"ok": True}


def _to_export(d, kind):
    base = {
        "start": float(getattr(d, "start_s", 0.0) or 0.0),
        "end": float(getattr(d, "end_s", 0.0) or 0.0),
    }
    if kind == "subtask":
        base["label"] = d.label
    else:
        for k in DIALOG_ATTRS:
            base[k] = getattr(d, k, "") or ""
    return base


def gather_annotations(dataset):
    if dataset.media_type == "group":
        view = dataset.select_group_slices(dataset.default_group_slice)
    else:
        view = dataset
    annotations = {}
    for s in view:
        if not s.has_field("episode_index") or s["episode_index"] is None:
            continue
        subs = [
            _to_export(d, "subtask")
            for d in (
                s[SUBTASK_FIELD].detections
                if s.has_field(SUBTASK_FIELD) and s[SUBTASK_FIELD]
                else []
            )
        ]
        highs = [
            _to_export(d, "high_level")
            for d in (
                s[HIGH_LEVEL_FIELD].detections
                if s.has_field(HIGH_LEVEL_FIELD) and s[HIGH_LEVEL_FIELD]
                else []
            )
        ]
        if subs or highs:
            annotations[int(s["episode_index"])] = {
                "subtasks": subs,
                "high_levels": highs,
            }
    return annotations

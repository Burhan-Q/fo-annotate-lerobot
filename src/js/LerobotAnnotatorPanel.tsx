// src/js/LerobotAnnotatorPanel.tsx
import React, { useState } from "react";
import { useFrameSync } from "./useFrameSync";
import { useEpisodeSegments } from "./useEpisodeSegments";
import { frameToSeconds, validateSegment, type Kind, type SegmentInput } from "./segmentUtils";

const FIELDS: Record<Kind, string[]> = {
  subtask: ["label"],
  high_level: ["user_prompt", "robot_utterance", "skill", "scenario_type", "response_type"],
};
const REQUIRED: Record<string, true> = { label: true, user_prompt: true, robot_utterance: true };
const EMPTY: SegmentInput = { start_s: 0, end_s: 0 };

const tabStyle = (active: boolean): React.CSSProperties => ({ padding: "4px 10px", cursor: "pointer", borderRadius: 6, border: "1px solid #3a4150", background: active ? "#ff6d04" : "transparent", color: active ? "#0b0e14" : "inherit", fontWeight: 600 });

const s: Record<string, React.CSSProperties> = {
  root: { padding: 12, color: "rgba(230,230,235,0.95)", fontSize: 13, height: "100%", overflowY: "auto" },
  tabs: { display: "flex", gap: 8, marginBottom: 10 },
  row: { display: "flex", gap: 6, alignItems: "center", marginBottom: 6, flexWrap: "wrap" },
  input: { background: "#10141c", border: "1px solid #3a4150", borderRadius: 6, color: "inherit", padding: "4px 6px", fontSize: 12 },
  btn: { padding: "4px 10px", borderRadius: 6, border: "1px solid #3a4150", background: "#1b2230", color: "inherit", cursor: "pointer" },
  primary: { padding: "4px 10px", borderRadius: 6, border: "none", background: "#ff6d04", color: "#0b0e14", cursor: "pointer", fontWeight: 600 },
  item: { display: "flex", gap: 6, alignItems: "center", padding: "4px 0", borderTop: "1px solid #222a36", flexWrap: "wrap" },
  center: { display: "flex", alignItems: "center", justifyContent: "center", height: "100%", textAlign: "center", padding: 16 },
};

export default function LerobotAnnotatorPanel() {
  const { currentFrame, seekFrame, isTimelineActive } = useFrameSync();
  const { sampleId, data, loading, error, addOrUpdate, remove } = useEpisodeSegments();
  const [kind, setKind] = useState<Kind>("subtask");
  const [form, setForm] = useState<SegmentInput>(EMPTY);

  if (!sampleId) return <div style={s.center}>Open a LeRobot episode in the modal to annotate.</div>;
  if (error) return <div style={s.center}>Failed to load segments: {error}</div>;
  if (loading || !data) return <div style={s.center}>Loading segments…</div>;
  const fps = data.fps ?? 0;
  if (!fps) return <div style={s.center}>This dataset has no fps; cannot map the playhead to time.</div>;

  const list = kind === "subtask" ? data.subtasks : data.high_level;
  const setField = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  const captureStart = () => currentFrame != null && setForm((f) => ({ ...f, start_s: frameToSeconds(currentFrame, fps) }));
  const captureEnd = () => currentFrame != null && setForm((f) => ({ ...f, end_s: frameToSeconds(currentFrame, fps) }));

  const onSubmit = async () => {
    if (!validateSegment(kind, form)) return;
    await addOrUpdate(kind, form);
    setForm(EMPTY);
  };
  const onEdit = (seg: any) => { setKind(kind); setForm({ ...seg }); };

  const fmt = (x?: number) => (x == null ? "–" : `${x.toFixed(3)}s`);

  return (
    <div style={s.root}>
      <div style={s.tabs}>
        {(["subtask", "high_level"] as Kind[]).map((k) => (
          <div key={k} style={tabStyle(kind === k)} onClick={() => { setKind(k); setForm(EMPTY); }}>
            {k === "subtask" ? "Subtasks" : "High-level"}
          </div>
        ))}
      </div>

      <div style={s.row}>
        <button style={s.btn} onClick={captureStart} disabled={!isTimelineActive}>Set start</button>
        <span>{fmt(form.start_s)}</span>
        <button style={s.btn} onClick={captureEnd} disabled={!isTimelineActive}>Set end</button>
        <span>{fmt(form.end_s)}</span>
        <span style={{ opacity: 0.6 }}>frame {currentFrame ?? "–"}</span>
      </div>

      {FIELDS[kind].map((f) => (
        <div style={s.row} key={f}>
          <label style={{ width: 110, opacity: 0.8 }}>{f}{REQUIRED[f] ? " *" : ""}</label>
          <input
            style={{ ...s.input, flex: 1 }}
            value={(form as any)[f] ?? ""}
            onChange={(e) => setField(f, e.target.value)}
            placeholder={f}
          />
        </div>
      ))}

      <div style={s.row}>
        <button style={s.primary} onClick={onSubmit} disabled={!validateSegment(kind, form)}>
          {form.id ? "Update" : "Add"}
        </button>
        {form.id && <button style={s.btn} onClick={() => setForm(EMPTY)}>Cancel</button>}
      </div>

      <div>
        {list.length === 0 && <div style={{ opacity: 0.6, padding: "8px 0" }}>No {kind} segments yet.</div>}
        {list.map((seg) => (
          <div style={s.item} key={seg.id}>
            <button style={s.btn} title="Seek to start"
              onClick={() => seg.support && seekFrame(seg.support[0])} disabled={!isTimelineActive}>▶</button>
            <span style={{ flex: 1 }}>
              <strong>{seg.label || "(dialogue)"}</strong> &nbsp;{fmt(seg.start_s)}→{fmt(seg.end_s)}
            </span>
            <button style={s.btn} onClick={() => onEdit(seg)}>Edit</button>
            <button style={s.btn} onClick={() => remove(kind, seg.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}

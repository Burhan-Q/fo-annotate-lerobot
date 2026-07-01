export type Kind = "subtask" | "high_level";

export interface SegmentInput {
  id?: string;
  start_s: number;
  end_s: number;
  label?: string;
  user_prompt?: string;
  robot_utterance?: string;
  skill?: string;
  scenario_type?: string;
  response_type?: string;
}

export function frameToSeconds(frame: number, fps: number): number {
  return fps > 0 ? (frame - 1) / fps : 0;
}

export function validateSegment(kind: Kind, seg: SegmentInput): boolean {
  if (!(seg.end_s > seg.start_s)) return false;
  if (kind === "subtask") return Boolean(seg.label && seg.label.trim());
  return Boolean(seg.user_prompt?.trim()) && Boolean(seg.robot_utterance?.trim());
}

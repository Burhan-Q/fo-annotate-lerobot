import { describe, it, expect } from "vitest";
import { frameToSeconds, validateSegment } from "../../src/js/segmentUtils";

describe("frameToSeconds", () => {
  it("maps 1-based frame to seconds", () => {
    expect(frameToSeconds(1, 10)).toBe(0);
    expect(frameToSeconds(6, 10)).toBeCloseTo(0.5);
  });
  it("guards fps<=0", () => {
    expect(frameToSeconds(5, 0)).toBe(0);
  });
});

describe("validateSegment", () => {
  it("subtask needs label and end>start", () => {
    expect(validateSegment("subtask", { start_s: 0, end_s: 1, label: "pick" })).toBe(true);
    expect(validateSegment("subtask", { start_s: 0, end_s: 1, label: "" })).toBe(false);
    expect(validateSegment("subtask", { start_s: 1, end_s: 1, label: "pick" })).toBe(false);
  });
  it("high_level needs prompt+utterance and end>start", () => {
    expect(validateSegment("high_level", { start_s: 0, end_s: 1, user_prompt: "p", robot_utterance: "r" })).toBe(true);
    expect(validateSegment("high_level", { start_s: 0, end_s: 1, user_prompt: "p" })).toBe(false);
  });
});

import { useCallback, useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { modalLooker } from "@fiftyone/state";

// Frame read/seek must go through the modal looker instance: for grouped
// datasets (dataset.mediaType === "group", all LeRobot imports) FiftyOne 1.17
// never creates a @fiftyone/playback timeline for video samples, and
// dispatchTimelineSetFrameNumberEvent only drives ImaVid lookers, not real
// video. Setting looker state `frameNumber` seeks the underlying <video>
// (the same mechanism as the built-in "," "." and 0-9 shortcuts); `updater`
// is protected only at the TypeScript level.
interface VideoLookerLike {
  frameNumber?: number;
  pause?: () => void;
  subscribeToState: (field: string, cb: (value: number) => void) => () => void;
  updater?: (update: Record<string, unknown>) => void;
}

export function useFrameSync() {
  const looker = useRecoilValue<VideoLookerLike | null>(modalLooker);
  const isPlayheadActive = Boolean(
    looker &&
      typeof looker.subscribeToState === "function" &&
      typeof looker.frameNumber === "number",
  );

  const [currentFrame, setCurrentFrame] = useState<number | null>(null);

  useEffect(() => {
    if (!looker || !isPlayheadActive) {
      setCurrentFrame(null);
      return;
    }
    setCurrentFrame(looker.frameNumber ?? null);
    return looker.subscribeToState("frameNumber", (frame) =>
      setCurrentFrame(frame),
    );
  }, [looker, isPlayheadActive]);

  const seekFrame = useCallback(
    (frame: number) => {
      if (!looker || !isPlayheadActive) return;
      looker.pause?.();
      looker.updater?.({ frameNumber: Math.max(1, Math.round(frame)) });
    },
    [looker, isPlayheadActive],
  );

  return { currentFrame, seekFrame, isPlayheadActive };
}

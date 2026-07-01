import { useCallback, useEffect, useRef, useState } from "react";
import {
  dispatchTimelineSetFrameNumberEvent,
  useDefaultTimelineNameImperative,
  useTimeline,
} from "@fiftyone/playback";
import { usePanelId } from "@fiftyone/spaces";

// Read the modal video playhead (1-based frames) and seek it. Frame sync is
// client-side; subscribe per-panel id so multiple panels don't collide.
export function useFrameSync() {
  const panelId = usePanelId();
  const { getName } = useDefaultTimelineNameImperative();
  const timelineName = getName();
  const { subscribe, isTimelineInitialized } = useTimeline(timelineName);

  const [currentFrame, setCurrentFrame] = useState<number | null>(null);
  const ref = useRef<number | null>(null);
  ref.current = currentFrame;

  const renderFrame = useCallback((n: number) => {
    if (ref.current !== n) setCurrentFrame(n);
  }, []);

  useEffect(() => {
    if (!isTimelineInitialized) return;
    subscribe({ id: panelId, loadRange: async () => {}, renderFrame });
  }, [isTimelineInitialized, subscribe, renderFrame, panelId]);

  const seekFrame = useCallback(
    (n: number) => {
      if (!timelineName) return;
      dispatchTimelineSetFrameNumberEvent({ timelineName, newFrameNumber: n });
    },
    [timelineName],
  );

  return { currentFrame, seekFrame, timelineName, isTimelineActive: isTimelineInitialized };
}

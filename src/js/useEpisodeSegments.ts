import { useCallback, useEffect, useRef, useState } from "react";
import { useRecoilValue } from "recoil";
import { nullableModalSampleId } from "@fiftyone/state";
import { useOperatorExecutor } from "@fiftyone/operators";
import type { Kind, SegmentInput } from "./segmentUtils";

const PLUGIN = "@Burhan-Q/annotate-lerobot";

interface Segment extends SegmentInput {
  id: string;
  label: string;
  support: [number, number] | null;
}
export interface EpisodeData {
  episode_index: number | null;
  fps: number | null;
  num_frames: number | null;
  subtasks: Segment[];
  high_level: Segment[];
}

function usePromisified(uri: string) {
  const ex = useOperatorExecutor(uri);
  const ref = useRef(ex);
  ref.current = ex;
  return useCallback(
    (params: Record<string, any>) =>
      new Promise<any>((resolve, reject) => {
        ref.current.execute(params, {
          callback: (raw) => (raw.error ? reject(raw.error) : resolve(raw.result)),
        });
      }),
    [],
  );
}

export function useEpisodeSegments() {
  const sampleId = useRecoilValue<string | null>(nullableModalSampleId);
  const get = usePromisified(`${PLUGIN}/get_episode_segments`);
  const save = usePromisified(`${PLUGIN}/save_segment`);
  const del = usePromisified(`${PLUGIN}/delete_segment`);

  const [data, setData] = useState<EpisodeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!sampleId) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await get({ sample_id: sampleId }));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [sampleId, get]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const addOrUpdate = useCallback(
    async (kind: Kind, segment: SegmentInput) => {
      if (!sampleId) return;
      await save({ sample_id: sampleId, kind, segment });
      await refresh();
    },
    [sampleId, save, refresh],
  );

  const remove = useCallback(
    async (kind: Kind, id: string) => {
      if (!sampleId) return;
      await del({ sample_id: sampleId, kind, id });
      await refresh();
    },
    [sampleId, del, refresh],
  );

  return { sampleId, data, loading, error, addOrUpdate, remove, refresh };
}

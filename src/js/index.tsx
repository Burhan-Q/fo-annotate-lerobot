// src/js/index.tsx
import "@voxel51/voodo/theme.css";
import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import LerobotAnnotatorPanel from "./LerobotAnnotatorPanel";

// Gate to imported LeRobot datasets via the importer's sample fields. The
// activator ctx is { schema, dataset }; schema is the SAMPLE-field dict.
// (episode_index + camera_view verified present on the real svla_so101 import)
function isLerobotDataset(ctx?: { schema?: Record<string, unknown> }): boolean {
  return Boolean(ctx?.schema?.episode_index) && Boolean(ctx?.schema?.camera_view);
}

registerComponent({
  name: "lerobot_annotator",
  label: "LeRobot Annotator",
  component: LerobotAnnotatorPanel,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },
  activator: isLerobotDataset,
});

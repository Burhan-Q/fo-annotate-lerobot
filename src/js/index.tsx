// src/js/index.tsx  (temporary; replaced in Task 6)
import "@voxel51/voodo/theme.css";
import { registerComponent, PluginComponentType } from "@fiftyone/plugins";

function Placeholder() {
  return null;
}

registerComponent({
  name: "lerobot_annotator",
  label: "LeRobot Annotator",
  component: Placeholder,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },
  activator: () => false,
});

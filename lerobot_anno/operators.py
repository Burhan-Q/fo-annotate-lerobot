import fiftyone.operators as foo
import fiftyone.operators.types as types

from .segments import (
    get_episode_segments,
    save_segment,
    delete_segment,
    gather_annotations,
)
from .export import export_lerobot


class GetEpisodeSegments(foo.Operator):
    @property
    def config(self) -> foo.OperatorConfig:
        return foo.OperatorConfig(
            name="get_episode_segments",
            label="Get LeRobot episode segments",
            unlisted=True,
        )

    def execute(self, ctx) -> dict:
        return get_episode_segments(ctx.dataset, ctx.params["sample_id"])


class SaveSegment(foo.Operator):
    @property
    def config(self) -> foo.OperatorConfig:
        return foo.OperatorConfig(
            name="save_segment", label="Save LeRobot segment", unlisted=True
        )

    def execute(self, ctx) -> dict:
        return save_segment(
            ctx.dataset,
            ctx.params["sample_id"],
            ctx.params["kind"],
            ctx.params["segment"],
        )


class DeleteSegment(foo.Operator):
    @property
    def config(self) -> foo.OperatorConfig:
        return foo.OperatorConfig(
            name="delete_segment", label="Delete LeRobot segment", unlisted=True
        )

    def execute(self, ctx) -> dict:
        return delete_segment(
            ctx.dataset, ctx.params["sample_id"], ctx.params["kind"], ctx.params["id"]
        )


class ExportLerobot(foo.Operator):
    @property
    def config(self) -> foo.OperatorConfig:
        return foo.OperatorConfig(
            name="export_lerobot",
            label="Export annotations to LeRobot v3.0",
            allow_delegated_execution=True,
            default_choice_to_delegated=True,
            allow_immediate_execution=True,
        )

    def resolve_input(self, ctx) -> types.Property:
        inputs = types.Object()
        inputs.str(
            "lerobot_root",
            label="Original LeRobot dataset root",
            description="Path to the source LeRobot v3.0 dataset (read-only).",
            required=True,
        )
        inputs.str(
            "output_dir",
            label="Output directory",
            description="Where the annotated copy is written (must differ from root).",
            required=True,
        )
        inputs.bool("copy_videos", label="Copy videos (else symlink)", default=False)
        return types.Property(inputs, view=types.View(label="Export to LeRobot v3.0"))

    def execute(self, ctx) -> dict:
        annotations = gather_annotations(ctx.dataset)
        return export_lerobot(
            ctx.params["lerobot_root"],
            ctx.params["output_dir"],
            annotations,
            bool(ctx.params.get("copy_videos", False)),
        )

    def resolve_output(self, ctx) -> types.Property:
        outputs = types.Object()
        outputs.str("output_dir", label="Output directory")
        outputs.int("num_subtasks", label="Unique subtasks")
        outputs.int("num_tasks_high_level", label="Unique high-level tasks")
        outputs.int("num_episodes_annotated", label="Episodes annotated")
        return types.Property(outputs, view=types.View(label="Export complete"))


def register(p) -> None:
    p.register(GetEpisodeSegments)
    p.register(SaveSegment)
    p.register(DeleteSegment)
    p.register(ExportLerobot)

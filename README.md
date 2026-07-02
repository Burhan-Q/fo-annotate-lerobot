# @Burhan-Q/annotate-lerobot

A FiftyOne hybrid plugin to **annotate imported LeRobot datasets** with per-episode
**subtask** and **high-level dialogue** time segments, directly in the FiftyOne App, and
**export an annotated LeRobot v3.0 dataset** ready for training.

It complements the importer
[`harpreetsahota204/fiftyone_lerobot_importer`](https://github.com/harpreetsahota204/fiftyone_lerobot_importer)
— you import a LeRobot dataset into FiftyOne with that, then use this plugin to add the
subtask/dialogue segments the LeRobot ecosystem consumes, and export the annotated copy.
Import is out of scope.

## Prerequisites

- **FiftyOne ≥ 1.17.0.**
- A LeRobot v3.0 dataset **imported into FiftyOne** via the importer above — a *grouped video*
  dataset (group = episode, slice = camera) with sample fields `episode_index` + `camera_view`
  and a per-frame `timestamp`. The plugin's panel only activates on such datasets.
- The **original LeRobot dataset directory on disk** (the export reads/rewrites its parquet;
  the re-encoded FiftyOne media alone can't reconstruct it).
- Python: `pyarrow` (see `requirements.txt`); `pandas` ships with FiftyOne.

> The importer additionally needs **system ffmpeg with AV1 decode** (`ffmpeg -decoders | grep av1`)
> and `ffmpeg-python`; those are the *importer's* requirements, not this plugin's runtime.

## Installation

```shell
fiftyone plugins download https://github.com/Burhan-Q/fo-annotate-lerobot
```

Then install the plugin's Python requirements:

```shell
fiftyone plugins requirements @Burhan-Q/annotate-lerobot --install
```

To work on the plugin from a local clone instead, see
[Developer install](#developer-install).

## Usage

1. Open an episode (group) in the **sample modal**.
2. **Split** the modal (e.g. *Split horizontally*) so the **video (Sample)** is in one pane
   and the **LeRobot Annotator** panel in the other — the panel reads and seeks the playhead
   through the mounted video looker (Set start/end are disabled until it mounts).
3. On the **Subtasks** tab: scrub the video, click **Set start** / **Set end** (they capture the
   current frame → seconds), type a subtask **label**, click **Add**.
4. On the **High-level** tab: same, plus `user_prompt` + `robot_utterance` (required) and optional
   `skill` / `scenario_type` / `response_type`.
5. Segments list under each tab with **seek** (▶), **Edit**, **Delete**. They persist immediately
   as `TemporalDetections` on the episode.
6. When done, run the **`Export annotations to LeRobot v3.0`** operator (operator browser). It
   takes your **original LeRobot dataset root** + an **output directory** (+ optional *copy
   videos*), and writes the annotated copy (see *What it produces*). Runs delegated by default.

## What it produces

On export (the `export_lerobot` operator), against your original LeRobot v3.0 dataset:
- `meta/subtasks.parquet` — unique subtask labels → `subtask_index`.
- `meta/tasks_high_level.parquet` — unique dialogue rows → `task_index`.
- Rewritten `data/chunk-*/file-*.parquet` with per-frame `subtask_index` and
  `task_index_high_level` (default `-1`), matched by the frame `timestamp`.
- Updated `meta/info.json` features; copied/symlinked `videos/`.

## Data model

Annotation is **per-episode and camera-agnostic** (mirrors the reference `lerobot-annotate`
tool). Segments are stored once, on the **group's default slice** ("anchor") sample, in two
`fo.TemporalDetections` fields:
- `subtasks` — each detection: `label`, `support=[first,last]` (1-based frames), dynamic attrs
  `start_s`/`end_s`.
- `high_level` — same, plus dynamic attrs `user_prompt`, `robot_utterance`, `skill`,
  `scenario_type`, `response_type`.

`support` drives the App timeline rendering; `start_s`/`end_s` (seconds) are the export source
of truth. Conversions: `seconds = (frame − 1) / fps`. Export rule: a frame with `timestamp = ts`
gets a segment's index iff `start_s ≤ ts < end_s`, with the **last** segment (by start time)
**end-inclusive** but still lower-bounded (so gap / pre-first-segment frames stay `-1`).

## Operators

| Operator | Listed | Purpose |
|---|---|---|
| `get_episode_segments` | no | Panel read: episode fps/frames + current segments |
| `save_segment` | no | Panel write: add/update a segment |
| `delete_segment` | no | Panel write: delete a segment |
| `export_lerobot` | yes (delegated) | Export annotated LeRobot v3.0 copy |

The three `*_segment` operators are JS-panel-driven (unlisted); `export_lerobot` is the only
user-facing (operator browser) entry point. It can also be invoked from the Python SDK using
its full URI:

```python
import fiftyone as fo
import fiftyone.operators as foo

dataset = fo.load_dataset("my-lerobot-dataset")

foo.execute_operator(
    "@Burhan-Q/annotate-lerobot/export_lerobot",  # full operator URI
    ctx={
        "dataset": dataset,
        "params": {
            "lerobot_root": "/path/to/original/lerobot/dataset",
            "output_dir": "/path/to/annotated/output",
            "copy_videos": False,
        },
        # "request_delegation": True,  # optionally schedule as a delegated job
    },
)
```

## Known limitations

- **Tested against a single dataset** so far:
  [`lerobot/svla_so101_pickplace`](https://huggingface.co/datasets/lerobot/svla_so101_pickplace)
  (v3.0, 50 episodes, 2 cameras, 30 fps).
- **Single-slice storage:** native timeline rendering of segments appears only when viewing the
  **default (anchor) camera slice**; the panel's list shows them from any slice. (Accepted MVP
  trade-off vs. replicating across slices.)
- The playhead-driven **Set start/end** and ▶ seek require the video looker to be mounted
  (Split the modal); the buttons are disabled otherwise. If the video pane is later replaced,
  the panel may briefly reference the unmounted looker and seeks become no-ops until the video
  pane is restored.

## Development

### Developer install

```bash
# Into your FiftyOne plugins dir (fo.config.plugins_dir)
git clone https://github.com/Burhan-Q/fo-annotate-lerobot.git @Burhan-Q/annotate-lerobot
cd @Burhan-Q/annotate-lerobot
pip install -r requirements.txt          # pyarrow
npm install && npm run build             # builds dist/index.umd.js (the JS panel)
fiftyone plugins list                    # confirm @Burhan-Q/annotate-lerobot is enabled
```

The built `dist/index.umd.js` is committed so the standard `fiftyone plugins download`
install works without a Node toolchain — rebuild (`npm run build`) and commit it whenever
the JS source changes.

### Tests

```bash
pip install pytest
python -m pytest tests/ -v          # Python: export + segment-store (6 tests)
npx vitest run                      # JS: pure helpers (4 tests)
npx tsc --noEmit                    # typecheck
npm run build                       # dist/index.umd.js
```

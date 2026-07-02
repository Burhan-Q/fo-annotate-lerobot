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

---

### Annotation UI

The panel has two tabs, one per segment kind. The numbered boxes in each image below map
to the rows of the table beneath it.

The **Subtasks** tab annotates the fine-grained motion phases of an episode — labeled
time spans like `reach`, `grab`, `release` — which export to the per-frame
`subtask_index` column (unique labels become `meta/subtasks.parquet`). Capture the span
from the playhead, name it, and click <kbd>Add</kbd>.

<details>
<summary><b>🏞️ Subtasks Tab Reference Image</b></summary>

<img
  height="840" 
  alt="FiftyOne LeRobot Annotation sub-tasks panel UI." 
  src="https://github.com/user-attachments/assets/fa624cf7-a962-4391-9787-097e360af6ec"
/>

| # | Element | Description | Expected values | How to use | Required |
|---|---|---|---|---|---|
| 1 | **Subtasks tab** | Active segment kind: labeled time spans that export to per-frame `subtask_index`. | active = orange | Click to select. Switching tabs clears the in-progress form (not saved segments). | — |
| 2 | **High-level tab** | Switches the editor to dialogue annotation (see the High-level image). | — | Click; clears the in-progress form. | — |
| 3 | **Set start** | Captures the current playhead frame as the segment start; `seconds = (frame − 1) / fps`. | — | Pause/scrub the video at the start moment, click. Disabled until the video looker is mounted. | yes |
| 4 | **Captured start time** | Read-only display of the captured start. | seconds, `0.000s` default | Re-click *Set start* to overwrite. | — |
| 5 | **Set end** | Captures the current playhead frame as the segment end. | must be **>** start | Scrub past the start moment, click. | yes |
| 6 | **Captured end time** | Read-only display of the captured end. | seconds | Re-click *Set end* to overwrite. | — |
| 7 | **Frame readout** | Live 1-based playhead frame number. | `frame N`; `frame –` until the video looker mounts | Reference while scrubbing; if `–`, split the modal so the video pane is visible. | — |
| 8 | **`label` input** | Subtask name; unique labels become `meta/subtasks.parquet` rows (`subtask_index`) at export. | short free text, e.g. `reach`, `grasp` | Type the name after capturing times. | yes |
| 9 | **Add / Update** | Saves the segment (validates `end > start` + label present). Shows *Update* + *Cancel* while editing. | enabled ⇔ valid | Click to persist to the episode's anchor sample; the list and the video's label overlays update. | — |
| 10 | **▶ seek** (one per segment row) | Jumps the video playhead to that segment's start frame. | — | Click to review a segment in the video. | — |
| 11 | **Segment summary** | Label and `start → end` span of a saved segment. | `label start_s→end_s` | Read-only. | — |
| 12 | **Edit** | Loads the row into the form for changes. | — | Click, adjust times/label, *Update* (or *Cancel*). | — |
| 13 | **Delete** | Removes the segment immediately (no confirmation). | — | Click to delete. | — |

</details>

The **High-level** tab annotates dialogue exchanges — what the human asked and how the
robot responded over a time span, plus optional `skill` / `scenario_type` /
`response_type` tags — which export to the per-frame `task_index_high_level` column
(unique exchanges become `meta/tasks_high_level.parquet`). The tab switcher, *Set start*
/ *Set end*, captured times, and frame readout behave exactly as rows 1–7 of the
Subtasks table; the boxes below cover what is specific to dialogue annotation.

<details>
<summary><b>🌌 High-level Tab Reference Image</b></summary>

<img
  height="840"
  alt="FiftyOne LeRobot Annotation high-level panel UI."
  src="https://github.com/user-attachments/assets/b32beefe-b36d-44fc-8cd1-b6242734e45d"
/>

| # | Element | Description | Expected values | How to use | Required |
|---|---|---|---|---|---|
| 1 | **`user_prompt`** | What the human asks the robot; also the row's display label, and part of the dedup key for `task_index_high_level` at export. | free text, e.g. `put the lego brick into the box` | Type the instruction/question. | yes |
| 2 | **`robot_utterance`** | The robot's spoken/logged response. | free text | Type the response. | yes |
| 3 | **`skill`** | Optional skill tag for the exchange. | short token, e.g. `pick_and_place` | Fill if your training setup uses it (exported to `meta/tasks_high_level.parquet`). | no |
| 4 | **`scenario_type`** | Optional scenario tag. | short token, e.g. `tabletop` | Optional. | no |
| 5 | **`response_type`** | Optional response category. | short token, e.g. `action`, `confirmation` | Optional. | no |
| 6 | **Add / Update** | Saves the exchange once valid (`end > start`, fields 1–2 non-empty). | enabled ⇔ valid | Click to persist. | — |
| 7 | **Dialogue entry** | Saved exchange: `user_prompt` + `start_s→end_s`, with ▶ seek / *Edit* / *Delete*. | — | Same row controls as subtasks. | — |
| 8 | **Dialogue entry (2nd)** | Episodes can hold any number of exchanges; each unique dialogue tuple gets one `task_index` at export. | — | — | — |

</details>

---

## What Gets Exported

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

## Plugin Operators

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

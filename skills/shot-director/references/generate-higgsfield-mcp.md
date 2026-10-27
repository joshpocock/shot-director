# GENERATE: run a take through the Higgsfield MCP (optional)

Use this only when the user asks you to generate ("generate it for me", "run take 2", "send it to Higgsfield")
and the Higgsfield MCP server is connected in this Claude Code session. Otherwise the user generates on
higgsfield.ai as usual and nothing here applies.

Connect it once: add the Higgsfield MCP server to Claude Code (see Higgsfield's own MCP setup page) and sign in.
Check with "what Higgsfield models can you see?": `kling4_0` must be listed.

## What the MCP can and cannot do with Kling 4.0

| Website tab | MCP `mode` | Media roles | Notes |
|---|---|---|---|
| References | `reference-to-video` | `image_references` (one per reference, in upload order) | Same as the tab: "Reference image 1 is..." follows this order |
| Frames, start and end only | `image-to-video` | `start_image`, `end_image` | The website's middle keyframes are **not** available here. A scene that needs middle keyframes stays on the website |
| Edit video | `video-edit` | `video_references` (the source clip), `image_references` (the reference still) | Source can be a job ID from an earlier generation |

Parameters: `model: "kling4_0"`, `resolution` `720p` or `1080p`, `duration` 3 to 30 (whole seconds),
`aspect_ratio` `16:9`, `9:16`, `21:9`, `1:1`. Check `models_explore` (`action: get`, `model_id: kling4_0`)
if anything here looks out of date; the live answer wins.

## The run, every time

1. **Uploads.** Reference images and keyframes from the user's folder: `media_upload` for each file, PUT the
   bytes to the returned URL, then `media_confirm`. Images made earlier on Higgsfield can be passed by their
   job ID instead. Write every ID into `scene.json` / `plan.json` under `"higgsfield_ids"` so reruns reuse them.
2. **Quote first.** Call `generate_video` with the full params plus `get_cost: true`. Nothing is submitted.
3. **Ask.** Tell the user the quote in credits and what will run (mode, duration, resolution, aspect,
   which references in which order). **Wait for a clear yes. Never generate without one, for every take.**
   "Run all three" is a yes for those three, quoted together first.
4. **Generate.** The same call without `get_cost`. If the tool offers a preset instead, decline it and run the
   plain model. If the call times out, do not resubmit: look the job up first.
5. **Download** the result into `takes/take-N.mp4` (scenes) or `attempts/attempt-N.mp4` (shots).
6. **Log** the quote you were given: `tally.py add --attempt N --mode references|frames|edit --credits <quote>`.
7. **Grade** as normal (GRADE-SCENE, GRADE or DRIFT). One prompt change per take, as always.

## Rules that do not change

- The human's call on every grade is still final.
- Quote, then ask, then spend. Never retry automatically after a failed or bad take; propose the one change
  and ask again.
- Never claim 4K, HDR or a two-minute extension.
- If the user is recording a video that must show the Higgsfield website workflow, generate there, not here.

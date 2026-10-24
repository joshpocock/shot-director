# shot-director

A Claude Code skill that plans an AI video shot as keyframes, grades each
generated attempt against that plan, and checks an edited clip for drift.

Built for **Kling 4.0 on Higgsfield** (Frames mode and Edit video). It works
with any video model that takes keyframes.

It never generates anything and never spends credits. You make every image and
video on the platform; Claude writes the plan, reads the frames you pull, and
keeps the bill.

## What it does

| You ask | Claude does |
|---|---|
| "Plan a 30-second ad for a small matte terracotta desk speaker as 4 keyframes." | Writes `plan.md` and `plan.json`: subject spec, keyframes with roles, times and a "must be true" list, an image prompt per keyframe, the Frames prompt, an Edit prompt for a likely client note, a scoring rule and a consistency checklist. |
| "Grade attempt-1.mp4 against the plan." | Runs `grade.py`, looks at the plan-versus-output images, calls each keyframe HIT, LATE / EARLY or MISS, lists cuts with timestamps, scores it, and proposes exactly one prompt change for the next attempt. Your call is final. |
| "The client wants it matte black. Check edited.mp4 against the source." | Runs `drift.py`, reads the heatmap and numbers, and tells you what changed that you did not ask for. |
| "Log 42 credits for attempt 2." / "What has this cost?" | Keeps a CSV ledger with `tally.py`: totals, credits per usable second, dollar total. |

## Install

Copy the skill folder into your Claude Code skills:

```
# for every project
cp -r skills/shot-director ~/.claude/skills/

# or for one project
cp -r skills/shot-director <your-project>/.claude/skills/
```

On Windows, copy `skills\shot-director` to `%USERPROFILE%\.claude\skills\`.

Requirements:

- Python 3.10 or newer
- ffmpeg and ffprobe on your PATH
- `pip install numpy pillow opencv-python`

## Quick start

1. **Plan.** "Use shot-director to plan a 30-second ad for a small matte
   terracotta desk speaker as 4 keyframes for Kling 4.0 Frames."
   Make the keyframe images from the plan's prompts, then send them back:
   Claude runs the consistency checklist before you spend video credits.
2. **Grade.** Generate in Frames, download the clip, then: "Grade
   attempts/attempt-1.mp4 against plan.json with the keyframes in keyframes/."
3. **Drift.** After Edit video: "Check edit/edited.mp4 against edit/source.mp4
   for drift. The edit should only change the speaker."

## How Higgsfield's Frames mode shapes the plan

Checked on 2026-10-23 (the skill's `references/kling4-higgsfield-rules.md` has
the full list; trust your screen if it has changed):

- Up to 10 frames. The first upload is the start frame and the **last upload is
  pinned to the final frame**. There is no per-keyframe time field: middle
  frames are timed only by the timestamps in your prompt.
- Frames has no aspect ratio control. Your first keyframe sets the shape.
  Keyframes must be JPEG or PNG.
- Multi-shot cuts are the default, so the prompt asks for one continuous shot
  in its first line. There is no audio toggle, so the prompt describes the
  sound and says "No music, no voice, no subtitles."
- Insert `@image_1` and `@video_1` with the @ picker. Typed tags do not link.
- Edit video takes a 3 to 30 s mp4 or mov up to 200 MB, plus image references.
- Duration carries across tabs, and prices change. Read the quote on the
  Generate button before every click. The skill never quotes a price.

## The scripts

All three have `--help`, take media paths as arguments, need no network and
run on Windows, macOS and Linux.

### grade.py

```
python grade.py --plan plan.json --keyframes keyframes --video attempt-1.mp4 --out grade-1 [--search 3.0 --step 0.25 --scene 0.3]
```

- Reads the clip's real duration. Keyframe 1 is graded at the first frame, the
  last keyframe at the final frame, the rest at their planned times.
- For each keyframe it searches every frame within +/- `--search` seconds for
  the best match (structural similarity on downscaled grayscale plus a colour
  histogram term) and reports the best-match time, the offset and the span
  that matches about equally well (a hold or a freeze).
- Finds cuts with a frame-difference spike test plus the ffmpeg scene score,
  and lists "possible cuts" (whip pans, flashes, morphs) to check by eye.
- Writes `report.md`, `report.json`, `pairs/kf<N>_pair.png` (plan, output at
  the planned time, best match, similarity curve) and `overview.png`.
- Suggests a label and a score. It does not decide; Claude and you do.

Scoring: keyframe 1 hits by construction and is not scored. Keyframes 2 to N
score HIT 1, LATE or EARLY 0.5, MISS 0, plus 1 point for no cuts, so the score
is out of (N-1) + 1.

### drift.py

```
python drift.py --source source.mp4 --edited edited.mp4 --out drift-1 [--fps 6 --blur 7 --thresh 25] [--focus-hint "speaker"] [--expect-box x,y,w,h] [--start 17 --end 27]
```

- Resamples both clips to the same size and frame rate, aligns them by frame,
  blurs, differences luminance and chroma, thresholds and cleans up the mask.
- Writes `heatmap.png` (how often each pixel changed; main hotspot in green,
  other hotspots in orange), `worst/*.png` (source, edited, changed pixels),
  `diff.mp4`, and `report.md` / `report.json` with per-frame changed %, the
  main edited region's share of all changes, how much changed outside it and
  where, and the brightness and colour shift in areas that did not change.
- A generated re-render shifts every pixel slightly, even where nothing was
  meant to change. That is why it blurs and thresholds, and why the numbers
  are a guide that points your eyes, not proof.

### tally.py

```
python tally.py add --attempt 1 --mode frames --duration 28 --quality 720p --credits 42 --note "first pass" [--usable yes/no]
python tally.py mark --attempt 1 --usable no
python tally.py list
python tally.py summary --dollars-per-credit 0.02
```

A plain CSV (`credits-ledger.csv` by default, `--ledger` to change). `summary`
prints total credits, seconds generated, usable seconds, credits per usable
second (all spend divided by usable seconds) and the dollar total. Numbers in
the examples are placeholders; log what your Generate button says.

## Examples

- `examples/terracotta-speaker/`: a worked plan (`plan.md`, `plan.json`) for a
  fictional product: a small matte terracotta desk speaker shaped like a squat
  rounded block with one thin white light bar on the front, no logo. Client
  note: make it matte black.
- `examples/tests/`: outputs from the tests below, trimmed to a few small
  images per test, plus the script that draws the test scene
  (`tools/make_synth.py`) so you can rerun everything.
- `examples/ledger/credits-ledger.csv`: a sample ledger with placeholder numbers.

### How the scripts were tested

On a synthetic 15 s desk scene drawn by `examples/tests/tools/make_synth.py`
(no AI footage, no credits): a box opens, the terracotta speaker moves to the
desk, its light bar turns on at 9.5 s and the camera pushes in from 10 s.
Four keyframes are planned at 0, 6, 10 and 15 s.

| Test | Expected | Result |
|---|---|---|
| grade, same clip | all hit, no cuts | 4 / 4, no cuts. The scene holds still from 6 to 10 s, and the report flags those matches as ambiguous ("judge by eye") instead of pretending to be sure |
| grade, whole timeline slowed to 0.8x | later frames land late | keyframe 2 +2.08 s LATE, 3.5 / 4; keyframe 3 sits inside a hold, flagged as ambiguous |
| grade, 2 s of a different scene spliced over 9 to 11 s | cuts at 9 and 11 s, keyframe 3 wrong | cuts found at 9.00 s and 11.00 s; keyframe 3 scores 0.44 at its planned time, 2.5 / 4. The best match it found (1.5 s earlier) still has the light bar off, a detail only your eye catches, which is why the pair images exist |
| grade, keyframes against an unrelated scene | everything missed | 1 / 4 (only the no-cuts point), every keyframe under the similarity floor |
| drift, product recoloured to black and nothing else | changes on the product only | 100% of changed pixels in the main region, on the speaker |
| drift, recolour plus a plant that also changed colour | second hotspot found | main region 62% of changes, an "other hotspot" flagged middle right (2.53% of the frame): the plant |
| drift, recolour plus a darker grade | grade shift reported | brightness shift in unchanged areas -9.53 (0 to 255 scale) |
| drift, the same clip encoded at two quality levels | noise floor near zero | no changed pixels above the threshold |

Real generations are messier than a drawn scene: expect lower similarity
scores and more scattered drift. The thresholds are a starting point; check
them against your first real attempt.

## Limits

- Similarity is pixel based. Big lighting changes, fast motion and heavy camera
  moves lower the scores even when a frame is right, and a near-identical
  composition can score well when a detail is wrong. Always look at the pair
  images; the human's call is final.
- The last keyframe is pinned to the final frame on Higgsfield, so it nearly
  always matches there. Watch for the end state arriving early and holding.
- Cut detection can miss slow dissolves and morphs, and can flag whip pans or
  flashes as possible cuts.
- drift.py aligns frames by index. If an edit comes back retimed or a
  different length, the numbers stop meaning anything (the script warns).
  Edits that regenerate the whole frame will show more scattered change than
  the tests above; read the heatmap, not just the totals.
- Interface facts were checked on 2026-10-23 and can change.

## License

MIT. Copyright (c) 2026 Josh Pocock.

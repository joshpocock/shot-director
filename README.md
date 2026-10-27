# shot-director

A Claude Code skill that plans multi-shot AI video scenes with dialogue and
grades what comes back (cuts, lines, lip sync, faces), plans a single shot as
keyframes and grades each attempt against it, and checks an edited clip for
drift.

Built for **Kling 4.0 on Higgsfield** (References, Frames and Edit video). The
keyframe tools work with any video model that takes keyframes.

It never generates anything and never spends credits. You make every image and
video on the platform; Claude writes the plan, reads the frames you pull, and
keeps the bill.

## What you get

- **Three scene formats** that worked in Kling 4.0, with beat timing and
  pitfalls: the cinematic scene, the vertical micro-drama Reel, the animated
  story ad (plus the client colour change in Edit video).
- **Reference image prompts** for characters, creatures and products that
  keep identity across cuts.
- **A look playbook** for stills that make the video look expensive: light,
  contrast, palette, lens, materials, what to drop, and the build order.
- **Plans you paste:** shot lists, lines, the Kling prompt, image prompts.
- **Grades from the downloaded clip:** cuts, lines, lip sync, faces,
  keyframes, drift after an edit, and a credit ledger.

## What it does

| You ask | Claude does |
|---|---|
| "Write the scene: a 30 s vertical micro-drama where she reads one message on his phone and assumes the worst." | Writes `scene.md` and `scene.json`: references and the job each one does, a timed shot list with one speaker and one line per shot, delivery notes, and the ready-to-paste Kling 4.0 References prompt. Checks it with `scene_grade.py --check`. |
| "Grade this scene. Did every line land? Did the faces stay the same?" | Runs `scene_grade.py`: cuts against the plan, every line transcribed and matched (garbled words listed), a lip-sync strip per line and a face grid per shot that Claude reads and calls, then asks you to confirm. Score out of 4. |
| "Plan a 30-second ad for a small matte terracotta desk speaker as 4 keyframes." | Writes `plan.md` and `plan.json`: subject spec, keyframes with roles, times and a "must be true" list, an image prompt per keyframe, the Frames prompt, an Edit prompt for a likely client note, a scoring rule and a consistency checklist. |
| "Grade attempt-1.mp4 against the plan." | Runs `grade.py`, looks at the plan-versus-output images, calls each keyframe HIT, LATE / EARLY or MISS, lists cuts with timestamps, scores it, and proposes exactly one prompt change for the next attempt. Your call is final. |
| "The client wants it matte black. Check edited.mp4 against the source." | Runs `drift.py`, reads the heatmap and numbers, and tells you what changed that you did not ask for. |
| "Which format should I use?" / "Write an animated ad for a small speaker." | Picks one of three proven 30 s formats (cinematic scene, micro-drama Reel, animated story ad), says why, and writes the scene on its beat timing. |
| "Make reference images for the two characters." | Writes one image prompt per character, creature or product (framing, background, light, the identifiers to keep) and the keep-line for each in the video prompt. Checks the images when you send them. |
| "Make it look expensive." | Art-directs the stills: contrast against the set, what the light does, one palette with the product brightest, a named lens, fixed light, materials, and what to drop. Gives the build order and the consistency check. |
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
- For Scene mode: `pip install faster-whisper` (transcribes on your CPU; the
  first run downloads the model), or bring a transcript from any
  speech-to-text tool

## Quick start

Dialogue scene:

1. **Plan.** "Use shot-director to write the scene: a 30 s vertical
   micro-drama, two people in a restaurant booth." Make the reference images,
   send them back for a check, paste the prompt in the References tab.
2. **Grade.** Download the take, then: "Grade takes/take-1.mp4 against
   scene.json with the references in refs/."

Single keyframed shot:

1. **Plan.** "Use shot-director to plan a 30-second ad for a small matte
   terracotta desk speaker as 4 keyframes for Kling 4.0 Frames."
   Make the keyframe images from the plan's prompts, then send them back:
   Claude runs the consistency checklist before you spend video credits.
2. **Grade.** Generate in Frames, download the clip, then: "Grade
   attempts/attempt-1.mp4 against plan.json with the keyframes in keyframes/."
3. **Drift.** After Edit video: "Check edit/edited.mp4 against edit/source.mp4
   for drift. The edit should only change the speaker."

## Scene mode: dialogue scenes

Kling 4.0 makes a 3 to 30 s multi-shot scene with dialogue and lip sync in one
generation (References tab). Scene mode plans it and grades what comes back.

**Plan.** "Use shot-director to write the scene: a 30 s vertical micro-drama
where she reads one message on his phone and assumes the worst." Claude writes
`scene.md` and `scene.json`: aspect, duration, each reference image and its job
("Reference image 1 is the woman: keep her face ... the same in every shot"),
a shot list (start and end seconds, framing, who is on screen, action, one
speaker, the exact line, delivery) and the ready-to-paste Kling 4.0 prompt.
`scene_grade.py --check scene.json` holds the plan to the rules below.

Rules baked in, from real generations on 2026-10-27:

- Size each shot to its line: 3 to 6 words gets a 3 to 4 s shot. Long silent
  shots only for spectacle.
- One speaker per shot. Two people talking in one shot made the lines collide
  ("I ruined it" came out as "I ruined of did").
- Say the delivery: natural, normal conversational speed, real emotion, no
  long pauses before lines. Contractions and fillers read human.
- Each line at the start of its shot, hard cuts at stated seconds, "No fades.",
  "no subtitles".
- References and Frames cannot be combined in one task.

**Grade.** "Grade takes/take-1.mp4 against scene.json." Four marks, one point
each (half for partly there), out of 4:

| Mark | What the script does | Who decides |
|---|---|---|
| SHOTS | finds the real cuts (ffmpeg scene score), matches each planned cut: HIT within 1 s, HALF within 2 s, MISS; lists extra cuts and ignores lightning flashes | script suggests |
| LINES | transcribes the audio (faster-whisper on your CPU, or your own transcript), fuzzy matches every line, says when it was said, in which shot, how similar, and which words came out wrong | script suggests |
| SYNC | exports a 6-frame strip per line across the moment it is heard, and flags lines heard over a shot that does not show the speaker | Claude looks, you confirm |
| SAME | exports one clean frame per shot in a labelled grid under the reference images | Claude looks, you confirm |

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

## The references

The skill reads these from `skills/shot-director/references/`:

| File | What is in it |
|---|---|
| `kling4-higgsfield-rules.md` | interface facts, dialogue rules, prompt craft, money |
| `scene-formats.md` | the three 30 s formats, beat timing, pitfalls, Edit video lessons |
| `reference-sheets.md` | character, creature and product reference prompts, start and end frames, safety-filter wording |
| `look-playbook.md` | art direction for stills, the do and drop lists, build order, consistency check |
| `scene-template.md`, `plan-template.md` | the files the skill writes |

## The scripts

All four have `--help`, take media paths as arguments, need no network
(faster-whisper downloads its model once) and run on Windows, macOS and Linux.

### scene_grade.py

```
python scene_grade.py --scene scene.json --video take-1.mp4 --refs refs --out grade-1 [--cut-threshold 0.3] [--transcript my-stt.json] [--whisper-model small]
python scene_grade.py --check scene.json
python scene_grade.py --fill grade-1 --mark SYNC=HALF --mark SAME=HIT --by claude --why "..."
```

- SHOTS: ffmpeg scene scores above `--cut-threshold` (the same test as
  `select='gt(scene,T)'`), cuts closer than 0.5 s merged, each planned cut
  matched to the nearest real one. A candidate whose shapes stay put across it
  (a lightning flash) is listed as ignored, not counted.
- LINES: the whole script is aligned against the whole transcript after
  normalising case, punctuation, contractions ("it's" = "it is", "'cause" =
  "because", "kinda" = "kind of") and numbers ("thirty" = "30"). HIT at 0.85
  similarity or more and starting inside its shot (+/- 1 s), HALF at 0.6 or in
  the wrong shot, MISS below. Notes when a line starts late in its shot or
  plays over the previous shot.
- `--transcript` takes a list of `{start, end, text}` (word or segment level),
  `{"segments": [{start, end, text, words}]}` or `{"words": [...]}`.
- Writes `report.md`, `report.json`, `sync/lineNN_<time>.jpg`,
  `same-grid.jpg`, `contact-sheet.jpg` and `transcript.json`. Face-similarity
  numbers are added only if `insightface` or `face_recognition` is installed.
- `--fill` records Claude's and your SYNC and SAME calls (and any override)
  and rescores. A human call beats Claude's, which beats the script's.

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

One worked scene per format (`scene.md`, `scene.json`):

- `examples/scene-friday/`: micro-drama Reel. "Friday", 30 s 9:16 in seven
  shots, two original characters, six lines and a silent ring-box insert,
  with the Kling 4.0 prompt that produced the clip tested below.
- `examples/scene-viking/`: cinematic scene. "Edge of the Map", 30 s 16:9 in
  seven shots: a narrator, two Vikings and a giant sea robot, with the three
  reference image prompts.
- `examples/scene-grandpa/`: animated story ad. "Grandpa's Radio", 30 s 16:9
  in Frames mode with a start and an end frame, a made-up speaker brand, and
  the Edit video prompt for the matte black client note (with the fix line
  for the drift the first edit showed).

Single shots and tests:

- `examples/terracotta-speaker/`: a worked plan (`plan.md`, `plan.json`) for a
  fictional product: a small matte terracotta desk speaker shaped like a squat
  rounded block with one thin white light bar on the front, no logo. Client
  note: make it matte black.
- `examples/tests/`: outputs from the tests below, trimmed to a few small
  images per test, plus the script that draws the test scene
  (`tools/make_synth.py`) so you can rerun everything.
- `examples/ledger/credits-ledger.csv`: a sample ledger with placeholder numbers.

### How scene_grade.py was tested

On three real 30 s Kling 4.0 References generations (not in the repository, to
keep it small), transcribed with faster-whisper `small` on a CPU:

| Clip | Expected | SHOTS | LINES |
|---|---|---|---|
| "Friday" v2, 7 shots (the example scene) | cuts near 4 / 7 / 12 / 16 / 20 / 25 s, every line said | HALF: 4 of 6 cuts within 1 s; 4 s came at 5.17 s and 16 s at 17.50 s | HIT: 6 of 6, all 1.00 similar |
| "Friday" v1, 5 shots, last shot with both speakers | the garble caught | HALF: 22 s came at 23.25 s | HALF: 5 of 6; "'it' heard as 'a did'" (0.77) |
| Viking scene, 5 shots, lightning in the last shot | rower line late in its shot, "we've found" | HIT: 4 of 4 within 0.2 s, lightning at 29.1 s ignored | HALF: the rower's line starts 4.2 s into its 6 s shot; the leader's line starts 1.1 s early, over the rower's close-up |

With the same clips transcribed by a second speech-to-text service and passed through `--transcript`, the
lines matched the same way, the v1 garble came out as "'it' heard as 'of
did'", and the leader's "we've found" showed as "extra 'have'" (faster-whisper
had heard "we found" and dropped the shouted "Row!"). SYNC and SAME are calls
for eyes; the strips and grids were read and judged by Claude in testing.

### How the keyframe scripts were tested

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

- Scene mode cannot judge lip sync or faces by itself; it shows you the
  frames. Speech-to-text can drop short shouted words and swallow
  contractions, and its word times can be a fraction of a second off at a
  cut: listen before you call a line wrong. Cut detection can miss slow
  dissolves.
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

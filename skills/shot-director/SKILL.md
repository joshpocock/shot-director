---
name: shot-director
description: Plan an AI video shot as keyframes, grade each generated attempt against that plan, and check an edited clip for drift. Built for Kling 4.0 (Frames and Edit video) on Higgsfield, works with any keyframe video model. Use when the user says "plan this shot", "write the keyframes", "plan a 30 second ad", "grade this attempt", "did it hit the keyframes", "score this clip", "check this edit for drift", "what else changed", "log the credits" or "what has this cost so far".
---

# Shot Director

You are the user's director's assistant for keyframe video. You do three jobs:

1. **PLAN**: turn a one-line brief into keyframes, image prompts, a Frames prompt, an Edit prompt and a scoring rule.
2. **GRADE**: score a downloaded attempt against the plan from pulled frames.
3. **DRIFT**: after an edit, show what changed that was not asked for.

Plus a **credits ledger** so the user always knows the running bill.

## Ground rules

- **You never generate.** The user makes every image and video on the platform (for example higgsfield.ai). Do not call any image or video generation tool or API from this skill, and never spend the user's credits.
- **The human's call is final.** Scripts suggest labels; you give a verdict with reasons; the user confirms or overrides. Record their call, not yours.
- **Never quote prices.** Prices change. Tell the user to read the credit quote on the Generate button before every click, then log what it said with `tally.py`.
- **Never claim 4K, HDR or a two-minute extension on Higgsfield.**
- **Original IP only.** No text, logos or brand marks on products, no real products, no known characters, no real people other than the user.
- Read `references/kling4-higgsfield-rules.md` before you plan, and again before you suggest a retry. If the user's screen disagrees with it, trust the screen.

## Setup (once)

```
python --version          # 3.10 or newer
ffmpeg -version           # ffmpeg and ffprobe on PATH
pip install numpy pillow opencv-python
```

The scripts live in `scripts/` next to this file. Run them with full paths, from the user's shot folder, passing media paths as arguments. Every script has `--help`.

Suggested shot folder:

```
my-shot/
  plan.md  plan.json
  keyframes/  kf1.png kf2.png ...
  attempts/   attempt-1.mp4 ...
  grade-1/    (grade.py output)
  edit/       source.mp4 edited.mp4
  drift-1/    (drift.py output)
  credits-ledger.csv
```

---

## Mode 1: PLAN

Input: one line, for example "30-second ad for a small matte terracotta desk speaker". If something essential is missing, pick a sensible default and say so. Ask at most one question.

Work through these in order, then write `plan.md` and `plan.json` using `references/plan-template.md`. The worked example in the repository (`examples/terracotta-speaker/`) shows the finished result.

1. **Subject spec.** One paragraph: shape, size, colour, finish, and what it does not have ("no text, no logo, no buttons"). This exact wording is reused in every prompt. Products never carry text or logos. Keep the design original; avoid silhouettes that read as a famous product.
2. **Duration and count.** Default 4 keyframes; recommend 3 to 5 for up to 30 s (the platform allows up to 10). Add a keyframe only where the visual state must change.
3. **Roles and times.** Give each keyframe a role (default: setup, discovery, use, hero). Keyframe 1 is at 0 s. **The last keyframe is the final frame of the clip**, so its time is the clip duration. Middle times go on real beats (when the reveal completes, when the product is placed), not evenly spaced. The platform has no per-keyframe timing; the prompt's timestamps are the only clock.
4. **Camera first.** Decide the camera in one sentence before writing any frame, then make every keyframe agree with it. If keyframes share a camera position, the camera is locked between them; plan a move only between keyframes whose framing differs.
5. **"Must be true" list per keyframe.** What the frame must show, including explicit on/off states ("light bar off"), where persistent props are, and "no hands" at keyframe moments.
6. **Image prompts.** Keyframe 1 from scratch. Each later keyframe is an edit of the previous one with the same image model, changing one or two things, opening with "Same photo, same ... same camera position and framing" unless the camera move is planned there, and ending with "Change nothing else." Restate props that stay. Same aspect ratio and pixel size for all; PNG.
7. **Frames prompt.** In this order:
   - Line 1: `One continuous shot for the full N seconds. No cuts, no angle changes, no scene changes.`
   - Line 2: which images are first and last, and the camera behaviour, matching the keyframes.
   - Line 3: the subject spec plus "Its shape, size and color stay exactly the same throughout."
   - Timestamped beats in keyframe order, **one action and one camera move per beat**, naming each keyframe at its time (`8s: matches @image_2, ...`). Time hand entries so hands have left before each keyframe moment.
   - Sound line: what you want to hear, then `No music, no voice, no subtitles.` when wanted.
   - Remind the user to insert every `@image_N` with the @ picker (typed tags do not link).
8. **Edit prompt** for the most likely client note (default: a colour change). `Edit @video_1.` + exactly what changes, where and for which time span + what parts of the target stay (a light bar stays white) + `Keep unchanged:` and named elements, always including the room's brightness and colour, the camera move and the timing. Add the prompt for a reference still (the product in the new colour, made by editing the last keyframe). Suggest a 10 s test slice where the target is on screen throughout.
9. **Scoring rule.** Keyframes 2 to N: HIT 1, LATE or EARLY 0.5, MISS 0; plus 1 for no cuts. Score out of (N-1) + 1.
10. **Consistency checklist** for the keyframe images, to run before any video credits are spent:
    - same pixel size and ratio, JPEG or PNG
    - same room, props, light direction in every frame; persistent props present
    - on/off states exactly as planned
    - no hands or people at keyframe moments (unless planned)
    - camera identical where the plan says locked, different only where the move is planned
    - one or two changes between neighbours; neighbours not near-identical
    - product shape, size and colour identical across frames
    - no text, logos or stray objects
    - beat order in the prompt matches upload order

Close the plan with a short run sheet: make keyframes, check them, short 720p test, grade, full length, edit, drift, summary.

When the user sends the keyframe images, **look at them side by side** (open each file) and run the checklist yourself. Report each failed item with the frame and a one-line image-edit fix.

---

## Mode 2: GRADE

The user downloads the attempt and puts the keyframes in a folder as `kf1.png`, `kf2.png` ... (or the `file` names in plan.json).

```
python <skill>/scripts/grade.py --plan plan.json --keyframes keyframes --video attempts/attempt-1.mp4 --out grade-1
```

Options: `--search 3.0` (seconds either side to search), `--step 0.25` (curve resolution in the report), `--scene 0.3` (ffmpeg scene score that always counts as a cut), `--match-floor 0.55`, `--hit-tol 1.0`, `--late-tol 3.0`.

What it does: reads the real duration, grades keyframe 1 at the first frame and the last keyframe at the final frame, pulls the output frame at every planned time, searches every frame within +/- `--search` s for the best match (grayscale structural similarity plus a colour histogram term on downscaled frames), finds cuts (a frame-difference spike test plus the ffmpeg scene score), and writes:

- `report.md` and `report.json`: per keyframe the similarity at the planned time, best-match time and score, offset, the span that matches about equally well, a suggested label and notes; cuts and possible cuts; a suggested score.
- `pairs/kf<N>_pair.png`: plan (top left), output at the planned time (top right), best-match frame (bottom left), similarity over the whole clip (bottom right; yellow = planned, green = best).
- `overview.png`: one row per keyframe, an 8-frame timeline, and before/after frames for each cut.

Then you:

1. Read `report.md`.
2. **Open every pair image and `overview.png` and look.** Pixel similarity is a pointer, not a verdict. Check each keyframe's "must be true" list against the frame.
3. Give each keyframe after the first a verdict with one reason:
   - **HIT**: best match within about 1 s of the plan and the content matches.
   - **LATE +x s / EARLY -x s**: 1 to 3 s off; give the offset.
   - **MISS**: content wrong (a must-be-true item fails, the product morphed, a prop vanished) or more than 3 s off.
   - Keyframe 1 always hits by construction; only flag it if the first frame does not match (wrong upload order).
   - The last keyframe is pinned, so it nearly always matches at the final frame. If the report says the end state was reached early and held, call out the freeze.
4. **Cuts**: list each with its timestamp. Confirm every "possible cut" by eye in the overview before counting it; whip pans, flashes and fast motion can look like cuts to the detector.
5. **Score**: points out of (N-1) + 1.
6. **Propose exactly one prompt change** for the next attempt, aimed at the biggest failure. One change, so the next attempt shows whether it worked:

   | Symptom | One change |
   |---|---|
   | A cut | Strengthen line 1, remove anything that reads like a second location, keep one camera instruction, add "locked tripod camera" while the camera should be still |
   | Keyframe late | Move that beat's timestamp earlier or remove an action from the beat before it |
   | Keyframe early, then a hold | Shorten the move window (for example "20-30s" instead of "17-30s") |
   | Keyframe content wrong | Restate the frame's state in its beat line ("8s: matches @image_2, light bar off"); check that neighbouring keyframes do not contradict it |
   | Motion stalls | Neighbouring keyframes too similar, or the camera line contradicts the frames; fix the camera line first |
   | Product changes shape or colour | Restate the subject line and "stays exactly the same throughout" |
   | Hands mangle a prop | Take the hands out of that beat ("The lid lifts off and settles beside the box") |

7. Ask the user to confirm or override each verdict. Write their final calls into the "Final (human)" column of `report.md`, then log the attempt: `tally.py mark --attempt N --usable yes|no`.

---

## Mode 3: DRIFT

After an Edit video pass: source = the clip that went into Edit, edited = what came back. Both should cover the same time span.

```
python <skill>/scripts/drift.py --source edit/source.mp4 --edited edit/edited.mp4 --out drift-1 --focus-hint "speaker"
```

Options: `--fps 6`, `--blur 7`, `--thresh 25`, `--width 480`, `--chroma-gain 2.0`, `--start` / `--end` (compare a slice of both clips), `--expect-box x,y,w,h` (fractions 0 to 1 or source pixels; reports the share of changes inside it).

What it does: resamples both clips to the same size and frame rate, aligns them frame by frame, blurs, takes the luminance and chroma difference, thresholds and cleans it up, finds the largest connected changed region per frame (the main edited region), and writes:

- `heatmap.png`: how often each pixel changed (dark never, yellow every frame), green box = main hotspot, orange boxes = other hotspots.
- `worst/worst_<time>.png`: source | edited | changed pixels, for the frames with the most change.
- `diff.mp4`: the same triptych for the whole clip.
- `report.md` / `report.json`: changed % per frame, main-region share of all changes, % of the frame changed outside it and where, other hotspots, and the brightness and colour shift in areas that did not change.

Then you:

1. Read `report.md`, open `heatmap.png` and every `worst/` image.
2. **Did the asked change land?** The main hotspot should sit on the target, and the target should be changed in every frame where it is visible (check the worst frames and the per-frame numbers around the reveal).
3. **What else changed?** Name each other hotspot by place and what it is in the picture. Report the outside-main percentage and the background brightness shift (above about 3 on the 0 to 255 scale means the overall grade moved). Check the parts of the target that were meant to stay (for example the light bar staying white).
4. Rough guide, to be checked by eye: outside-main under 0.5% of the frame is clean; 0.5 to 2% look at the worst frames; above 2% there is probably visible drift.
5. If drift is real, propose one change to the Keep line (name the drifted element) and suggest re-running on the test slice first.

Say this every time you report drift numbers: **a generated re-render shifts every pixel slightly**, so blur and threshold are needed and the numbers point your eyes, they do not prove anything. If the edited clip was retimed or a different length, frame alignment fails and the numbers are meaningless; the script warns about this.

---

## Credits ledger

Before each Generate click, ask the user what the button quotes. Log it:

```
python <skill>/scripts/tally.py add --attempt 3 --mode frames --duration 30 --quality 720p --credits <what the button said> --note "kf3 moved to 16s"
python <skill>/scripts/tally.py mark --attempt 3 --usable yes
python <skill>/scripts/tally.py list
python <skill>/scripts/tally.py summary --dollars-per-credit <the user's plan price>
```

`summary` gives total credits, seconds generated, usable seconds, credits per usable second (all spend, including failed attempts, divided by usable seconds) and the dollar total. Default ledger: `credits-ledger.csv` in the current folder (`--ledger` to change). Remind the user that duration and quality carry across tabs, so the quote can silently change between modes.

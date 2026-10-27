---
name: shot-director
description: Plan and grade multi-shot AI video scenes with dialogue (shot list, lines and the Kling 4.0 References prompt; then cuts, lines, lip sync and face consistency graded from the downloaded clip), plan a single shot as keyframes and grade attempts against it, and check an edited clip for drift. Built for Kling 4.0 (References, Frames and Edit video) on Higgsfield. Use when the user says "write the scene", "plan a dialogue scene", "grade this scene", "did every line land", "did the faces stay the same", "plan this shot", "write the keyframes", "plan a 30 second ad", "grade this attempt", "did it hit the keyframes", "score this clip", "check this edit for drift", "what else changed", "log the credits", "what has this cost so far", "make it look expensive", "make reference images", "which format should I use", "write a micro-drama" or "write an animated ad".
---

# Shot Director

You are the user's director's assistant for AI video. Your jobs:

1. **PLAN-SCENE**: turn a one-line brief into a multi-shot dialogue scene: references and their jobs, a timed shot list with one speaker and one line per shot, and the ready-to-paste Kling 4.0 References prompt.
2. **GRADE-SCENE**: score a downloaded scene on four marks: SHOTS, LINES, SYNC, SAME.
3. **PLAN**: turn a one-line brief into keyframes, image prompts, a Frames prompt, an Edit prompt and a scoring rule.
4. **GRADE**: score a downloaded keyframe attempt against the plan from pulled frames.
5. **DRIFT**: after an edit, show what changed that was not asked for.
6. **GENERATE** (optional): when the user asks and the Higgsfield MCP is connected, run a take for them: quote, ask, generate, download, grade.

A brief with characters who talk is a scene (Scene mode). A single continuous shot built on keyframes is Modes 1 and 2.

Plus a **credits ledger** so the user always knows the running bill.

## Ground rules

- **By default the user generates.** You write the image and video prompts; the user makes every image and video on the platform (for example higgsfield.ai). Generate only in GENERATE mode: the user asked you to, the Higgsfield MCP is connected, and they said yes to the credit quote for that take. Never spend credits without that yes.
- **The human's call is final.** Scripts suggest labels; you give a verdict with reasons; the user confirms or overrides. Record their call, not yours.
- **Never quote prices from memory.** Prices change. On the website, tell the user to read the credit quote on the Generate button before every click; in GENERATE mode, use the live `get_cost` quote. Log what it said with `tally.py`.
- **Never claim 4K, HDR or a two-minute extension on Higgsfield.**
- **Original IP only.** No text, logos or brand marks on products, no real products, no known characters, no real people other than the user.
- Read `references/kling4-higgsfield-rules.md` before you plan, and again before you suggest a retry. If the user's screen disagrees with it, trust the screen.
- Which reference to read when:

  | Reference | Read it in | For |
  |---|---|---|
  | `kling4-higgsfield-rules.md` | every mode | interface facts, dialogue rules, prompt craft |
  | `scene-formats.md` | PLAN-SCENE | picking the format (cinematic scene, micro-drama Reel, animated story ad), beat timing, Edit video lessons |
  | `reference-sheets.md` | PLAN-SCENE | character, creature and product reference images, start and end frames, safety-filter wording |
  | `look-playbook.md` | PLAN, and PLAN-SCENE when a product or set must look premium | art direction that makes stills look expensive, build order, consistency check |
  | `scene-template.md` / `plan-template.md` | PLAN-SCENE / PLAN | the files you write |
  | `generate-higgsfield-mcp.md` | GENERATE | what the MCP can run, the quote-ask-generate loop |

## Setup (once)

```
python --version          # 3.10 or newer
ffmpeg -version           # ffmpeg and ffprobe on PATH
pip install numpy pillow opencv-python
pip install faster-whisper   # Scene mode transcription, runs locally on the CPU
```

The scripts live in `scripts/` next to this file. Run them with full paths, from the user's shot folder, passing media paths as arguments. Every script has `--help`.

Suggested scene folder:

```
my-scene/
  scene.md  scene.json
  refs/       her.png him.png ...
  takes/      take-1.mp4 ...
  grade-1/    (scene_grade.py output)
  credits-ledger.csv
```

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

## Scene mode

### PLAN-SCENE

Input: one line, for example "30 s vertical micro-drama: she reads one message on his phone and assumes the worst". If something essential is missing, pick a sensible default and say so. Ask at most one question.

Read `references/kling4-higgsfield-rules.md` (the References mode section), `references/scene-formats.md` and `references/reference-sheets.md`, then write `scene.md` and `scene.json` using `references/scene-template.md`. Worked examples in `examples/` next to this file, one per format (read the matching one before you write; it holds the tested prompt): `examples/scene-viking/` (cinematic scene), `examples/scene-friday/` (micro-drama Reel), `examples/scene-grandpa/` (animated story ad in Frames, with the Edit video pass).

0. **Format.** Pick one of the three in `scene-formats.md` and say which. "Which format should I use?": a product that must appear means the animated story ad, or a micro-drama with the product last; reach on Reels and Shorts means the micro-drama; a showcase or a hook means the cinematic scene. Use its beat table as the starting shot list.
1. **Aspect and duration.** 9:16 for Reels and Shorts, 16:9 for YouTube. Kling 4.0 generates 3 to 30 s in one go; default 30 s.
2. **References.** One image per character, prop or product that must stay the same. For each, the job sentence the prompt opens with: "Reference image 1 is the leader: keep his face, grey braided beard, scar, iron helmet and fur cloak exactly the same in every shot." Upload order sets the number. References and Frames cannot be combined in one task: a dialogue scene with characters is References mode; an animated ad on planned keyframes is Frames, and the start and end frames hold the characters (see `reference-sheets.md`).
3. **Shot list.** Each shot: start and end seconds, framing, who is on screen (`on_screen`), action, **one speaker or none**, the exact line in quotes, delivery notes. The rules, all from real tests:
   - **Size each shot to its line.** 3 to 6 words gets a 3 to 4 s shot. Long silent shots only for spectacle.
   - **One speaker per shot.** Two speakers in one shot collided and garbled a line. Split into shot / reverse shot.
   - **Say the delivery:** natural, normal conversational speed, real emotion, no long pauses before lines.
   - **Contractions and fillers read human** ("'Cause", "Babe. Babe,", "kinda"). Write the line as it should be said.
   - **Each line at the start of its shot.**
   - **Hard cuts at stated seconds.** No text shown on screen; a character reads it aloud.
4. **The Kling 4.0 prompt** (References tab), in this order:
   - the reference job sentences, one per image;
   - one line of look and place, then the delivery sentence, then `Only one person speaks in each shot. <K> shots with hard cuts at 4s, 7s, ... No fades.`;
   - one line per shot: `4-7s, shot 2: <framing>, <action>, <delivery>: "<line>"` (silent shots end `No dialogue.`);
   - the sound line, ending `No music, no subtitles.` (drop "no music" if a score is wanted).
5. **Marks:** what SHOTS, LINES, SYNC and SAME mean for this scene (which cuts, which lines, who must stay the same).
6. Run the plan check and fix every finding before handing it over, or say in `scene.md` why the format accepts it (the one spectacle shot; keyframe-timed shots in an animated ad):

```
python <skill>/scripts/scene_grade.py --check scene.json
```

7. **Make the references** (before anything is generated). Write one image prompt per reference in `scene.md`, from the templates in `reference-sheets.md`: framing, plain background, the same soft light for all, the identifiers the job sentence names, "No text, no logos." For a Frames scene, the start frame prompt and the end frame as an edit of it with the product still as a second image. The user makes the images; you do not. If the image filter blocks one, reword it as `reference-sheets.md` describes.

Close with the run sheet: make the reference images, check them side by side, one 720p test, grade, one fix, keeper at 1080p. When the user sends the reference images, open them and check them against the list at the end of `reference-sheets.md`: one subject each, same light, original faces, every identifier in the job sentence visible, no text or logos.

### GRADE-SCENE

The user downloads the take and puts the reference images in a folder.

```
python <skill>/scripts/scene_grade.py --scene scene.json --video takes/take-1.mp4 --refs refs --out grade-1
```

Options: `--cut-threshold 0.3` (ffmpeg scene score for a cut; lower it for dark footage), `--flash-dist 0.5` (lightning and lamp flashes are ignored when the shapes stay put), `--hit-tol 1.0` / `--half-tol 2.0` (cut timing), `--line-hit 0.85` / `--line-half 0.6` / `--line-tol 1.0` (line matching), `--whisper-model small` (faster-whisper, local CPU), `--transcript path.json` (bring any speech-to-text: a list of `{start, end, text}`, or `{"segments": [...]}`, or `{"words": [...]}`), `--no-face-scores`.

What it writes to the output folder:

- `report.md` / `report.json`: the four marks, a cut table (planned, actual, offset, HIT / HALF / MISS, extra cuts, ignored flashes, near misses), a line table (planned, heard, when, which shot, similarity, verdict), words that came out differently ("'it' heard as 'a did'"), speech that matches no line, plan-check findings.
- `sync/lineNN_<time>.jpg`: per spoken line, 6 frames across the moment it is said, with the audio time, planned and heard text, and face crops underneath when the face is small in the frame.
- `same-grid.jpg`: the reference images on the top row, then one clean mid-shot frame per shot, labelled with the shot, its time and who should be on screen. Face-similarity numbers are added only if `insightface` or `face_recognition` happens to be installed.
- `contact-sheet.jpg`: one frame per second, cut seconds in red.
- `transcript.json`: the faster-whisper transcript, reusable with `--transcript`.

Scoring: HIT 1, HALF 0.5, MISS 0 per mark, out of 4. SHOTS is HIT when every planned cut lands within 1 s and there are no extra cuts, MISS when fewer than half land. LINES is HIT when every line is at least 0.85 similar and starts inside its shot (+/- 1 s), MISS when fewer than half land. SYNC and SAME count once you or the user fill them in.

Then you:

1. Read `report.md`. SHOTS and LINES have script verdicts; read their notes (a line that starts late in its shot, or plays over the previous shot before the cut to its speaker).
2. **LINES:** before calling a garble, check whether the transcriber could be wrong (short shouted words get dropped, contractions get swallowed). If the user has a second transcript, rerun with `--transcript`.
3. **SYNC: open every image in `sync/` and look.** For each line: does a mouth move across the frames where the words are heard, is it the planned speaker's mouth, is the mouth still where the audio is silent? Lines flagged "does not show" the speaker are probably voiced over the wrong shot. Call SYNC: HIT if every line looks in sync on the right face, HALF if one or two are off or unclear, MISS if most are off.
4. **SAME: open `same-grid.jpg` and look.** Compare each shot's tile with the matching reference: face shape, hair, beard, scars, clothes, accessories (earrings, helmet), and the product's shape and colour. Call SAME: HIT if every character and product holds, HALF if one detail drifts (a missing earring, a beard that changes), MISS if a face or product clearly changes. A face seen from behind cannot be judged; say so.
5. Write your calls into the report:

```
python <skill>/scripts/scene_grade.py --fill grade-1 --mark SYNC=HALF --mark SAME=HIT --by claude --why "line 5: mouth closed while 'I ruined it' plays"
```

6. Tell the user the score out of 4 with one reason per mark, and **ask them to confirm or override each call. The human's call is final:** record it with `--fill grade-1 --mark SAME=HALF --by human`. A human call overrides yours, which overrides the script's.
7. **Propose exactly one prompt change** for the next take, aimed at the worst mark:

   | Symptom | One change |
   |---|---|
   | A cut late or missing | Restate the cut list line, shorten the shot before it, move its line to the start of the shot |
   | Extra cut | Remove anything in that shot that reads like a second angle or place |
   | Line garbled | Give the line its own shot with one speaker; simplify the words; write it as it is said |
   | Line missing | Quote it exactly in its shot line and give the shot enough time (about 2.5 words per second plus 1 s) |
   | Line late in its shot, or a long silence | Shorten the shot to the line; add "no long pauses before lines" |
   | Line voiced over the wrong face | Name the speaker in that shot's line ("close-up of the man ... he says") and keep one speaker per shot |
   | Robotic delivery | Add the delivery sentence and a per-line emotion; use contractions |
   | Face or product drifts | Restate that reference's job sentence with the drifting detail named |

8. Log the take with `tally.py` as for any attempt.

---

## Mode 1: PLAN

Input: one line, for example "30-second ad for a small matte terracotta desk speaker". If something essential is missing, pick a sensible default and say so. Ask at most one question.

Read `references/look-playbook.md` first: the look is decided in the stills. Then work through these in order and write `plan.md` and `plan.json` using `references/plan-template.md`. The worked example in `examples/terracotta-speaker/` next to this file shows the finished result.

1. **Subject spec.** One paragraph: shape, size, colour, finish, and what it does not have ("no text, no logo, no buttons"). This exact wording is reused in every prompt. Products never carry text or logos. Keep the design original; avoid silhouettes that read as a famous product.
2. **Duration and count.** Default 4 keyframes; recommend 3 to 5 for up to 30 s (the platform allows up to 10). Add a keyframe only where the visual state must change.
3. **Roles and times.** Give each keyframe a role (default: setup, discovery, use, hero). Keyframe 1 is at 0 s. **The last keyframe is the final frame of the clip**, so its time is the clip duration. Middle times go on real beats (when the reveal completes, when the product is placed), not evenly spaced. The platform has no per-keyframe timing; the prompt's timestamps are the only clock.
4. **Camera first.** Decide the camera in one sentence before writing any frame, then make every keyframe agree with it. If keyframes share a camera position, the camera is locked between them; plan a move only between keyframes whose framing differs.
5. **"Must be true" list per keyframe.** What the frame must show, including explicit on/off states ("light bar off"), where persistent props are, and "no hands" at keyframe moments.
6. **Image prompts.** Art-direct them with `look-playbook.md` ("make it look expensive"): contrast against the set, what the light does, one palette with the subject brightest, a named lens and focus, a fixed light direction, named materials, and nothing from its Drop list. Under each prompt, one line: "Why this looks expensive: ...". Build order: the product still first, then the base frame (the one that contains every object, not necessarily keyframe 1), then each other frame as an edit of its neighbour; put the product still in as a second image when its shape must hold; build the start frame last when it hides things (a closed box). The simple default: Each later keyframe is an edit of the previous one with the same image model, changing one or two things, opening with "Same photo, same ... same camera position and framing" unless the camera move is planned there, and ending with "Change nothing else." Restate props that stay. Same aspect ratio and pixel size for all; PNG.
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

## Mode 4: GENERATE (optional)

Only when the user asks you to generate and the Higgsfield MCP is connected. Read `references/generate-higgsfield-mcp.md` and follow its loop exactly: upload, quote with `get_cost`, ask, generate on a yes, download into `takes/` or `attempts/`, log, grade. The MCP runs References, start and end frames, and Edit video; a plan with middle keyframes stays on the website. Never generate a second take on your own: grade, propose one change, quote, ask again.

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

# Scene template

PLAN-SCENE mode writes two files in the scene folder:

- `scene.md`: for the person. References and their jobs, the shot list, the
  ready-to-paste Kling 4.0 prompt, the four marks.
- `scene.json`: for `scene_grade.py`. Same content, machine-readable.

Worked examples are in the repository: `examples/scene-friday/` (micro-drama
Reel), `examples/scene-viking/` (cinematic scene) and `examples/scene-grandpa/`
(animated story ad in Frames mode, with an Edit video pass).

## scene.md layout

```markdown
# <Title>

Brief: <the one line the user gave you>
Mode: References | Aspect: 9:16 | Duration: <N> s | Shots: <K> | Test at 720p, final at 1080p
Setting: <one sentence: place, time, light>

## References (upload in this order)
| # | Id | What it is | Its job in the prompt |
|---|---|---|---|
| 1 | her | woman, late 20s, ... | Reference image 1 is the woman: keep her face, ... the same in every shot. |

## Shot list
| Shot | Time | Framing | On screen | Action | Speaker | Line | Delivery |
|---|---|---|---|---|---|---|---|
| 1 | 0-4 s | over his shoulder | her, him | ... | her | "..." | ... |
| 5 | 16-20 s | insert | ring box | ... | none | (no line) | |

## Kling 4.0 prompt (References tab)
Upload the references in the order above. Set Duration to <N> s.
    <prompt>

## Marks
SHOTS: cuts at ... within 1 s. LINES: every line said, in its shot.
SYNC: the right mouth moves on the words. SAME: <who and what must not change>.
HIT 1, HALF 0.5, MISS 0 per mark, out of 4. The human's call is final.

## Run sheet
1. Make the reference images ... 2. Check them ... 3. Short 720p test ... 4. Grade ... 5. One fix ... 6. Keeper at 1080p.
```

## scene.json schema

Required by `scene_grade.py`: `shots`, each with `start_s` and `end_s`.
Everything else is read by you, the user and `--check`.

```json
{
  "schema": "shot-director/scene@1",
  "title": "string",
  "brief": "the one-line brief",
  "aspect": "9:16",
  "duration_s": 30,
  "mode": "references",
  "quality": {"test": "720p", "final": "1080p"},
  "setting": "one sentence",
  "references": [
    {"index": 1, "id": "her", "file": "her.png", "role": "character",
     "spec": "what it looks like",
     "job": "Reference image 1 is the woman: keep her face ... exactly the same in every shot."}
  ],
  "delivery": "scene-wide delivery sentence",
  "shots": [
    {"id": 1, "start_s": 0, "end_s": 4,
     "framing": "over the man's shoulder",
     "on_screen": ["her", "him"],
     "action": "what happens",
     "speaker": "her",
     "line": "Do not tell her about Friday?",
     "delivery": "reading it out, half amused then suspicious"},
    {"id": 5, "start_s": 16, "end_s": 20, "framing": "close insert", "on_screen": ["ring box"],
     "subject": "ring box", "action": "...", "speaker": null, "line": null}
  ],
  "sound": "ambience. No music, no subtitles.",
  "kling_prompt": "the exact prompt, lines separated by \\n",
  "marks": {"SHOTS": "...", "LINES": "...", "SYNC": "...", "SAME": "..."}
}
```

Notes:

- Shots are contiguous: shot 1 starts at 0, each shot starts where the last
  ended, the last ends at `duration_s` (3 to 30 s).
- One `speaker` and one `line` per shot, or none. A narrator or off-screen
  voice gets `"voiceover": true` (no lips to grade).
- `on_screen` lists the reference ids (or plain names) the framing shows.
  The grader uses it to flag a line heard over a shot that does not show its
  speaker, and labels the SAME grid with it. `subject` names the reference a
  silent shot is about.
- `speaker` and `subject` should match a reference `id`, so optional face
  scores know which reference to compare against.
- `file` in `references` is relative to `--refs` (default: the folder of
  scene.json).
- A `lines` list (`[{"speaker", "text", "delivery"}]`) is accepted in a shot
  only so an old plan that broke the one-speaker rule can still be graded;
  `--check` flags it.
- Each reference may carry an `image_prompt`: the prompt the user pastes to
  make it (see `reference-sheets.md`).
- A Frames scene (`"mode": "frames"`) has `"references": []` and a `frames`
  list instead (`index`, `id`, `file`, `time_s`, `role`, `must_be_true`,
  `image_prompt`). An `edit` object can hold the Edit video pass (`prompt`,
  `reference_images`, `drift_check`). `scene_grade.py` ignores these fields;
  they are for the user and for you. See `examples/scene-grandpa/scene.json`.

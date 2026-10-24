# Plan template

PLAN mode writes two files in the shot folder:

- `plan.md`: for the person. Upload order, every prompt in a code block ready
  to paste, the checklist, the scoring rule.
- `plan.json`: for `grade.py`. Same content, machine-readable.

A full worked example is in the repository at
`examples/terracotta-speaker/plan.md` and `plan.json`.

## plan.md layout

```markdown
# <Title>

Brief: <the one line the user gave you>
Duration: <N> s | Keyframes: <K> | Aspect: 16:9 | Test at 720p, final at 1080p
Camera: <one sentence, e.g. locked 0 to 17 s, then one slow push-in that lowers to desk height, ending on keyframe 4>

## Subject
<one paragraph spec: shape, size, colour, finish, what it does NOT have>
Rules: no text or logos on the product, original design only.

## Keyframes
| # | Role | Time | Must be true in this frame |
|---|---|---|---|
| 1 | setup | 0 s (start frame) | ... |
| 2 | discovery | 8 s | ... |
| 3 | use | 17 s | ... |
| 4 | hero | 30 s (final frame, pinned) | ... |

### Keyframe 1 image prompt (from scratch)
    <prompt>
### Keyframe 2 image prompt (edit of keyframe 1)
    <prompt>
... one per keyframe ...

## Consistency check (run on the images before you generate)
- [ ] ...

## Frames prompt
Upload kf1.png, kf2.png, ... in that order. Insert every @image_N with the @ picker.
    <prompt>

## Edit prompt (client note: <note>)
Source: the keeper clip, picked from Generations. Reference: <still>. Set Duration to the source length.
    <prompt>

## Scoring
Keyframes 2 to K: HIT 1, LATE or EARLY 0.5, MISS 0. No cuts: 1. Score out of K.
HIT = best match within 1 s of the plan and the content matches.
LATE / EARLY = 1 to 3 s off. MISS = content wrong or more than 3 s off.
The human's call is final.

## Run sheet
1. Make the keyframe images ... 2. Check them ... 3. Short 720p test ... 4. Grade ... 5. Full length ... 6. Edit ... 7. Drift check.
```

## plan.json schema

Required by `grade.py`: `keyframes` (2 to 10 entries), each with `time_s`.
Everything else is read by you and the user.

```json
{
  "schema": "shot-director/plan@1",
  "title": "string",
  "brief": "the one-line brief",
  "duration_s": 30,
  "aspect": "16:9",
  "quality": {"test": "720p", "final": "1080p"},
  "subject": {
    "name": "string",
    "spec": "one paragraph",
    "rules": ["no text or logos on the product", "original design only"]
  },
  "camera": "one sentence that every keyframe and the Frames prompt agree with",
  "keyframes": [
    {
      "id": 1,
      "file": "kf1.png",
      "role": "setup",
      "time_s": 0,
      "made_from": "scratch",
      "must_be_true": ["closed box on the desk", "no hands", "light bar not visible"],
      "image_prompt": "string"
    },
    {
      "id": 2,
      "file": "kf2.png",
      "role": "discovery",
      "time_s": 8,
      "made_from": "edit of kf1",
      "changes": ["lid off", "speaker visible in tissue, light bar off"],
      "must_be_true": ["..."],
      "image_prompt": "string"
    }
  ],
  "frames_prompt": "string, lines separated by \\n",
  "edit": {
    "client_note": "make it matte black",
    "reference_image": "black-still.png",
    "reference_image_prompt": "string",
    "prompt": "string",
    "focus_hint": "speaker",
    "test_slice_s": [15, 25]
  },
  "scoring": {
    "hit_tol_s": 1.0,
    "late_tol_s": 3.0,
    "points": {"HIT": 1, "LATE": 0.5, "EARLY": 0.5, "MISS": 0},
    "no_cuts_point": 1,
    "out_of": 4
  },
  "consistency_checklist": ["string"]
}
```

Notes:

- The first keyframe's `time_s` must be 0 and the last must equal
  `duration_s`. `grade.py` enforces both: keyframe 1 is graded at the first
  frame and the last keyframe at the final frame, whatever the file says.
- `file` is relative to the `--keyframes` folder. If it is missing, `grade.py`
  looks for `kf<id>.png` or `.jpg`.
- `scoring.points` overrides the default points in `grade.py`.

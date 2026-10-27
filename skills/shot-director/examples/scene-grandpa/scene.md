# Grandpa's Radio

Brief: 30-second animated story ad: Grandpa's old radio dies on his birthday; his granddaughter's gift, a small speaker, turns the night around. Client note: make the speaker matte black.
Format: animated story ad (see `references/scene-formats.md`, c)
Mode: Frames, then Edit video | Aspect: 16:9 | Duration: 30 s | Shots: 4 | Test at 720p, final at 1080p
Setting: a cozy stylized 3D animated living room at night, warm lamp light, a birthday cake on the coffee table, an empty wall shelf on the right.
Product: Kiln (a made-up brand), a small matte terracotta speaker, a squat rounded block wider than it is tall, one thin light bar on the front, no text, no logo.

## Frames (upload in this order)

References and Frames cannot be combined in one task, so the characters and
the product are held by the frames. Make the product still first (the
terracotta speaker prompt in `references/look-playbook.md`), then:

| # | Id | Time | Must be true |
|---|---|---|---|
| 1 | start | 0 s (start frame) | grandfather tapping the old radio, frowning in a funny way; wall shelf empty; no speaker anywhere; no granddaughter |
| 2 | end | 30 s (end frame, pinned) | grandfather and granddaughter dancing hand in hand, laughing; the speaker on the wall shelf, light bar on; same room, light and camera as the start frame |

Optional on the web Frames tab: two middle frames, the granddaughter holding
out the gift box at 8 s and the speaker on the shelf at 17 s, for tighter
timing. Upload them between the start and the end frame.

### Start frame (from scratch)

```
Cozy stylized 3D cartoon render, family animation look, soft rounded shapes, warm colors. A living room at night lit by a warm table lamp, a patterned rug, an armchair, bookshelves with framed photos, a small birthday cake on the coffee table. A cheerful-looking older man with a big white mustache, round glasses and a brown cardigan stands at a side table, frowning in a funny way at a chunky old wooden radio and tapping its top. An empty wooden wall shelf is behind him. No text, no logos.
```

A first wording ("in the style of a modern feature animation", "grumpy
grandfather ... scowling") was blocked by the image filter as a false
positive. This wording passed. See the safety-filter tip in
`references/reference-sheets.md`.

### End frame (edit of the start frame; second image = the product still)

```
Edit the first image into a later moment of the same animated film, same stylized 3D cartoon look, same living room, same lamp light, same older man with the white mustache, round glasses and brown cardigan. The old radio is gone from the side table. On the wooden wall shelf behind him now sits the small speaker from the second image, redrawn in the same cartoon style: a squat rounded block, clearly wider than it is tall, matte terracotta, one thin light bar on the front glowing soft cool white. The older man is happily dancing, holding both hands of his granddaughter, a girl about eight with two pigtails and pastel pajamas, both laughing. Warm, joyful, same camera angle. No text, no logos.
```

## Shot list

| Shot | Time | Framing | On screen | Action | Speaker | Line | Delivery |
|---|---|---|---|---|---|---|---|
| 1 | 0-8 s | medium wide | grandpa, radio | taps his radio; it crackles, then dies with a pop and a puff of dust | grandpa | "Forty years. Never let me down." | grumbling, gruff old voice |
| 2 | 8-17 s | closer | girl, grandpa, gift box | she runs in and holds out a small charcoal gift box; he opens it, unimpressed | girl | "Happy birthday, Grandpa! It's better, I promise." | bright |
| 3 | 17-24 s | close-up of the wall shelf, then the grandfather's face | Kiln speaker, grandpa | the light bar glows, a warm old swing tune starts; his eyebrows rise | grandpa | "Well, I'll be." | softly, amazed |
| 4 | 24-30 s | wide | grandpa, girl, Kiln speaker | they dance around the rug, laughing, the speaker glowing on the shelf | narrator (voiceover) | "Kiln. Small speaker, big room." | warm female voice, pronounced "Kill-n" |

Why it is built this way: a small problem in the first shot, the gift in the
second, the product saving the day in the last third, and a short tag line as
a voiceover over the wide. Stylized animation holds faces and the product
better over 30 s than photoreal. The product name has its pronunciation in
the prompt because it is made up.

## Kling 4.0 prompt (Frames tab)

Upload the start frame, then the end frame (any middle frames in between).
Set Duration to 30 s. Frames has no aspect control: the start frame sets 16:9.

```
A stylized 3D animated family film, warm and joyful, same living room, same characters and same look in every shot. The start image is the first frame and the end image is the last frame. Every line is delivered naturally with real emotion, at normal speed, no long pauses before lines. Only one person speaks in each shot. Four shots with hard cuts at 8s, 17s and 24s. No fades.
0-8s, shot 1: the grandfather with the white mustache taps his old wooden radio; it crackles, then dies with a small pop and a puff of dust. He grumbles in English, in a gruff old voice: "Forty years. Never let me down."
8-17s, shot 2: closer: his granddaughter, about eight, with two pigtails and pastel pajamas, runs in and holds out a small charcoal gift box with both hands, and says brightly in English: "Happy birthday, Grandpa! It's better, I promise." He takes it and opens it, unimpressed.
17-24s, shot 3: close-up of the wall shelf: a small matte terracotta speaker, a squat rounded block wider than it is tall, its thin light bar glows soft cool white, and a warm old swing tune starts playing. Cut to the grandfather's eyebrows rising as he says softly in English: "Well, I'll be."
24-30s, shot 4: wide: the grandfather takes the girl's hands and they dance around the rug, laughing, the speaker glowing on the shelf. A warm female voiceover says in English, pronounced "Kill-n": "Kiln. Small speaker, big room."
Sound: radio crackle and pop, footsteps, then the swing music to the end. No subtitles.
```

No "no music": the swing tune is part of the story.

## Plan check

`scene_grade.py --check scene.json` gives three findings. All three are the
same rule, and the format breaks it on purpose:

```
- shot 1: 8 s for a 6-word line leaves a long silence; size the shot to the line (3 to 6 words -> 3 to 4 s)
- shot 2: 9 s for a 7-word line leaves a long silence; size the shot to the line (3 to 6 words -> 3 to 4 s)
- shot 3: 7 s for a 3-word line leaves a long silence; size the shot to the line (3 to 6 words -> 3 to 4 s)
```

The shots are timed to the keyframe beats (gift at 8 s, speaker at 17 s), and
the action fills them: the radio dying, the girl running in and the gift
being opened, the light bar and the music coming on. The lines still sit at
the start of their shots. In a dialogue-led scene, fix these findings; in an
action-led animated ad, accept them.

One thing `--check` does not catch: shot 3 says "Cut to the grandfather's
eyebrows", a cut inside the shot. That came out of the tested prompt and adds
a cut near 20 s that SHOTS will list as extra. To keep the plan clean, make it
two shots (the shelf, 17-20 s, no dialogue; the grandfather, 20-24 s, "Well,
I'll be.") and add 20s to the cut list.

## Edit prompt (client note: "Love it. Can we see it in matte black? Keep everything else.")

Source: the 1080p keeper, picked from Generations (video 1). Reference: the
black still (image 1), made by editing the end frame:

```
Edit this image. Change only the speaker's body color from matte terracotta to matte black, same cartoon style, same shape, size and position, no shine. Its light bar keeps glowing soft cool white. Keep the brightness and color of the room exactly the same. Change nothing else.
```

Set the Edit tab's Duration to the source length. Insert `@video_1` and
`@image_1` with the @ picker.

```
Do not add any object that is not in the original video. The wall shelf stays empty until 17s. Every movement, pose, gesture and camera framing stays exactly as in the original video, frame for frame; only the speaker's color changes.
Edit @video_1. Change only the small speaker's body color: everywhere the speaker appears, in the gift box, on the wall shelf and in the last shot, it becomes matte black like the speaker in @image_1, same cartoon style, same shape, size, position and movement. Its light bar stays soft cool white and comes on at the same moment.
Keep unchanged: the grandfather, the granddaughter, their faces, clothes, voices and lines, the living room, the lamp light, the cake, the old radio, the gift box, the cuts, the camera, the timing, the music and the voiceover.
```

The first line is the fix. The tested edit ran without it, and two things
came back that nobody asked for: a black speaker stood on the shelf before
the gift was opened, and the hand-off and the dance were re-animated. The fix
line forbids new objects, says where the shelf is empty, and asks for the
original motion frame for frame. It was written from that result; check the
next pass with drift.py:

```
python <skill>/scripts/drift.py --source edit/keeper.mp4 --edited edit/edited.mp4 --out drift-1 --focus-hint "speaker"
```

Look hardest at 0 to 17 s: any change on the shelf before 17 s is an extra
object. Test on a 10 s slice at 720p first.

## Marks

- SHOTS: cuts at 8, 17 and 24 s, each within 1 s (plus the cut inside shot 3, see Plan check).
- LINES: "Forty years. Never let me down.", the girl's line, "Well, I'll be." and the tag line all said, each in its shot.
- SYNC: grandpa's mouth on his lines, the girl's on hers. The tag line is a voiceover.
- SAME: grandpa, the girl and the room the same in every shot; the speaker's shape and colour the same in shots 3 and 4; the shelf empty until 17 s.

HIT 1, HALF 0.5, MISS 0 per mark, out of 4. The human's call is final.

## Run sheet

1. Make the product still, the start frame, then the end frame as an edit of
the start frame. 2. Check them side by side (same room, same light, same
camera, shelf empty in the start frame, no text). 3. One 720p test at full
length. 4. Grade it:
`scene_grade.py --scene scene.json --video take-1.mp4 --out grade-1`.
5. One fix to the prompt, aimed at the worst mark. 6. The keeper at 1080p.
7. The black still, then the Edit video pass on a 10 s slice, then the full
clip. 8. Drift check. Read the credit quote on the Generate button before
every click.

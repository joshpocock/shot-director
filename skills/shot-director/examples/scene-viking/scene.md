# Edge of the Map

Brief: 30-second cinematic scene: Vikings sail past the edge of every map and meet something that has been waiting under the sea.
Format: cinematic scene (see `references/scene-formats.md`, a)
Mode: References | Aspect: 16:9 | Duration: 30 s | Shots: 7 | Test at 720p, final at 1080p
Setting: cold blue dawn on a dark stormy sea in thick fog; a Viking longship with a carved dragon prow, a striped sail and round wooden shields.

## References (upload in this order)

| # | Id | What it is | Its job in the prompt |
|---|---|---|---|
| 1 | leader | Viking chieftain in his fifties, long grey beard braided at the chin, pale scar through his left eyebrow, round iron helmet with a nose guard, heavy brown fur cloak over chain mail | Reference image 1 is the Viking leader: keep his face, grey braided beard, scar through his left eyebrow, iron helmet and fur cloak exactly the same in every shot. |
| 2 | rower | young Viking rower about seventeen, freckles, red-brown hair, no helmet | Reference image 2 is the young rower: keep his face, freckles and red-brown hair the same in every shot. |
| 3 | robot | colossal ancient sea robot, broad rounded head, two round amber eyes, rusted dark iron plates, barnacles and seaweed | Reference image 3 is the giant sea robot: keep its shape, rusted iron, barnacles and amber eyes the same in every shot. |

Image prompts (3:4 portrait for the two men, the same light for all three;
see `references/reference-sheets.md`):

```
Photorealistic character reference portrait, waist up, facing the camera, plain dark grey studio background, soft even light. A Viking chieftain in his fifties: long grey beard braided at the chin, weathered skin, a pale scar running through his left eyebrow, piercing grey eyes, a round iron helmet with a nose guard, a heavy brown fur cloak over chain mail and dark wool, a leather strap across his chest. Stern, calm expression. No text, no logos.
```

```
Photorealistic character reference portrait, waist up, facing the camera, plain dark grey studio background, soft even light. A young Viking rower about seventeen: red-brown hair, a freckled face, no helmet, a plain undyed wool tunic with a leather belt. Wary, calm expression. No text, no logos.
```

```
Photorealistic creature design reference, front view, head and torso, plain dark grey studio background, soft even light. A colossal ancient robot that has slept under the sea for centuries: a broad rounded head, two large round eyes glowing warm amber, dark weathered iron plates streaked with orange rust, clusters of barnacles and strands of seaweed hanging from its shoulders. No text, no logos.
```

## Shot list

| Shot | Time | Framing | On screen | Action | Speaker | Line | Delivery |
|---|---|---|---|---|---|---|---|
| 1 | 0-4 s | wide and low over the water | longship, crew | the longship slides out of the fog, the crew rowing | narrator (voiceover) | "They sailed past the edge of every map." | an old man, low, slow, Norse-accented English |
| 2 | 4-8 s | close-up of the leader at the prow | leader | raises a fist | leader | "Hold the oars. Something's under us." | quiet and tense |
| 3 | 8-12 s | close-up of the young rower | rower | freezes mid-stroke | rower | "What is it?" | whispering, scared |
| 4 | 12-19 s | wide | robot, longship | the sea swells, two amber lights glow under the water, the robot's head and shoulders rise, seawater pouring off; a deep metallic groan | none | (no line) | |
| 5 | 19-22 s | close-up of the young rower | rower | looking up | rower | "That's no whale." | his voice shaking |
| 6 | 22-26 s | close-up of the leader | leader | a grim half smile, tightening his grip on his axe | leader | "No, boy. That's the end of the world." | low and certain |
| 7 | 26-30 s | low hero shot from behind the leader | leader, robot | he lifts his axe toward the robot, lightning forks across the clouds; a thunderclap | leader | "Row!" | roars |

Why it is built this way: the narrator sells the premise over the opening
wide; two short close-ups build the tension; the only silent shot is the
spectacle (the robot rising), given 7 s because nobody talks over it; the
payoff line has its own close-up, and the last shot carries one shouted word.
This is the 7-shot version of a 5-shot take that was generated and graded:
in that take the rower's line started 4.2 s into a 6 s shot, and the leader's
last line (payoff and shout together) started 1.1 s early, over the rower's
close-up. Shorter shots sized to the lines and a separate payoff shot fix both.

## Kling 4.0 prompt (References tab)

Upload leader, rower, robot in that order. Set Duration to 30 s.

```
Reference image 1 is the Viking leader: keep his face, grey braided beard, scar through his left eyebrow, iron helmet and fur cloak exactly the same in every shot. Reference image 2 is the young rower: keep his face, freckles and red-brown hair the same in every shot. Reference image 3 is the giant sea robot: keep its shape, rusted iron, barnacles and amber eyes the same in every shot.
A photorealistic cinematic scene, cold blue dawn on a dark stormy sea in thick fog. A Viking longship with a carved dragon prow, a striped sail and round wooden shields. Fast, natural pacing like a real film: every line is delivered in natural English with real emotion, at normal speed, no long pauses before lines. Only one person speaks in each shot. Seven shots with hard cuts at 4s, 8s, 12s, 19s, 22s and 26s. No fades.
0-4s, shot 1: wide and low over the water, the longship slides out of the fog, the crew rowing. A narrator, an old man with a low, slow Norse-accented English voice: "They sailed past the edge of every map."
4-8s, shot 2: close-up of the leader at the prow raising a fist, quiet and tense: "Hold the oars. Something's under us."
8-12s, shot 3: close-up of the young rower freezing mid-stroke, whispering, scared: "What is it?"
12-19s, shot 4: wide: the sea ahead swells, two amber lights glow under the water, then the giant robot's head and shoulders rise slowly out of the sea, seawater pouring off it. A deep metallic groan. No dialogue.
19-22s, shot 5: close-up of the young rower looking up, his voice shaking: "That's no whale."
22-26s, shot 6: close-up of the leader, a grim half smile, tightening his grip on his axe: "No, boy. That's the end of the world."
26-30s, shot 7: low hero shot from behind the leader as he lifts his axe toward the towering robot while lightning forks across the clouds. He roars: "Row!" A thunderclap.
Sound: crashing waves, creaking wood, oars, wind, thunder. No music, no subtitles.
```

## Plan check

`scene_grade.py --check scene.json` gives one finding, and it is expected:

```
- shot 4: 7 s with no line. Fine for spectacle; otherwise shorten it
```

Shot 4 is the spectacle. It is the one long silent shot the format allows.

## Marks

- SHOTS: cuts at 4, 8, 12, 19, 22 and 26 s, each within 1 s. The lightning in shot 7 is not a cut (the grader ignores flashes).
- LINES: all six lines said, each in its own shot, the narrator over the wide. A transcriber can drop the shouted "Row!": listen before calling it missing.
- SYNC: the leader's mouth on his lines in shots 2 and 6, the rower's in shots 3 and 5. Shot 1 is a voiceover; shot 7 is seen from behind and cannot be judged.
- SAME: the leader's beard, scar, helmet and cloak identical in shots 2, 6 and 7; the rower's face and freckles in shots 3 and 5; the robot's shape and amber eyes in shots 4 and 7.

HIT 1, HALF 0.5, MISS 0 per mark, out of 4. The human's call is final.

## Run sheet

1. Make the three reference images. 2. Check them side by side (same light,
plain background, scar and amber eyes visible, no text). 3. One 720p test at
full length. 4. Grade it:
`scene_grade.py --scene scene.json --video take-1.mp4 --refs refs --out grade-1`.
5. One fix to the prompt, aimed at the worst mark. 6. The keeper at 1080p.
Read the credit quote on the Generate button before every click.

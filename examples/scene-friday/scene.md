# Friday

Brief: 30-second vertical micro-drama: she reads one message on his phone and assumes the worst; it is a proposal.
Mode: References | Aspect: 9:16 | Duration: 30 s | Shots: 7 | Test at 720p, final at 1080p
Setting: a warm, dimly lit restaurant booth at night, candle on the table.

## References (upload in this order)

| # | Id | What it is | Its job in the prompt |
|---|---|---|---|
| 1 | her | woman, late 20s, dark curly hair, gold hoop earrings, cream knit top | Reference image 1 is the woman: keep her face, dark curly hair, gold hoop earrings and cream knit top exactly the same in every shot. |
| 2 | him | man, late 20s, short beard, navy overshirt | Reference image 2 is the man: keep his face, short beard and navy overshirt exactly the same in every shot. |

Make each as a plain front-facing portrait on a neutral background, same light,
2:3 or 9:16. Original faces only.

## Shot list

| Shot | Time | Framing | On screen | Action | Speaker | Line | Delivery |
|---|---|---|---|---|---|---|---|
| 1 | 0-4 s | over the man's shoulder | her, him | his phone buzzes face up; she picks it up and reads it out (screen never shown) | her | "Do not tell her about Friday?" | half amused, then suspicious |
| 2 | 4-7 s | close-up of the man | him | caught, a quick nervous laugh | him | "Babe. Babe, it's not what you think." | talking fast, nervous |
| 3 | 7-12 s | close-up of the woman | her | arms crossed | her | "Then what is it? 'Cause it looks exactly like what I think." | cold and quick |
| 4 | 12-16 s | close-up of the man | him | exhales, gives up, reaches into his jacket | him | "Okay. It was supposed to be Friday." | quiet, a little embarrassed |
| 5 | 16-20 s | close insert on the table | ring box, his hand | he sets a small open ring box by the candle; a small gasp off screen | none | (no line) | |
| 6 | 20-25 s | close-up of the woman | her | both hands over her mouth, eyes filling up | her | "Oh my God. I ruined it." | laughing and crying at once |
| 7 | 25-30 s | close-up of the man | him | grinning; she laughs off screen | him | "Yeah. You kinda did." | warm and teasing |

Why it is built this way: every line has its own shot, sized to the line
(3 to 6 words, 3 to 5 s); one speaker per shot; the only silent shot is the
spectacle (the ring); contractions and fillers ("Babe. Babe,", "'Cause",
"kinda") so it reads human; the phone text is read aloud, never shown.

## Kling 4.0 prompt (References tab)

Upload her, then him. Set Duration to 30 s.

```
Reference image 1 is the woman: keep her face, dark curly hair, gold hoop earrings and cream knit top exactly the same in every shot. Reference image 2 is the man: keep his face, short beard and navy overshirt exactly the same in every shot.
A photorealistic vertical micro-drama in a warm, dimly lit restaurant booth at night, candle on the table. Fast, natural pacing like a real TV drama: every line is delivered in casual, natural American English at normal conversational speed with real emotion, no robotic delivery, no long pauses before lines. Only one person speaks in each shot. Seven shots with hard cuts at 4s, 7s, 12s, 16s, 20s and 25s. No fades.
0-4s, shot 1: over the man's shoulder: his phone buzzes face up on the table; she glances at it, picks it up and reads it out, half amused then suspicious: "Do not tell her about Friday?" The phone screen is never shown.
4-7s, shot 2: close-up of the man, caught, a quick nervous laugh, talking fast: "Babe. Babe, it's not what you think."
7-12s, shot 3: close-up of the woman, arms crossed, cold and quick: "Then what is it? 'Cause it looks exactly like what I think."
12-16s, shot 4: close-up of the man, he exhales, gives up, reaches into his jacket, quiet and a little embarrassed: "Okay. It was supposed to be Friday."
16-20s, shot 5: close insert: his hand sets a small open ring box on the table next to the candle; the ring catches the light. A small surprised gasp off screen. No dialogue.
20-25s, shot 6: close-up of the woman, both hands over her mouth, eyes filling up, laughing and crying at once: "Oh my God. I ruined it."
25-30s, shot 7: close-up of the man grinning, warm and teasing: "Yeah. You kinda did." She laughs off screen.
Sound: quiet restaurant ambience, cutlery, low chatter. No music, no subtitles.
```

## Marks

- SHOTS: cuts at 4, 7, 12, 16, 20 and 25 s, each within 1 s.
- LINES: all six lines said, each in its own shot.
- SYNC: the speaking mouth moves on the words, and it is the right person's mouth.
- SAME: both faces, her hoops and knit top, his beard and overshirt identical in every shot; the ring box appears from shot 5.

HIT 1, HALF 0.5, MISS 0 per mark, out of 4. The human's call is final.

## Run sheet

1. Make the two reference images. 2. Check them side by side (same light, no
text, original faces). 3. One 720p test at full length. 4. Grade it:
`scene_grade.py --scene scene.json --video take-1.mp4 --refs refs --out grade-1`.
5. One fix to the prompt, aimed at the worst mark. 6. The keeper at 1080p.
Read the credit quote on the Generate button before every click.

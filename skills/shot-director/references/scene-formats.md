# Scene formats: three 30 s structures that work

Three formats, each made and previewed in Kling 4.0 on Higgsfield in
2026-10. Pick one before writing the shot list. Read this in PLAN-SCENE mode
together with `reference-sheets.md`.

| Format | Aspect | Mode | Look | Use it for | Example |
|---|---|---|---|---|---|
| Cinematic scene | 16:9 | References | photoreal | showing what the model can do, a trailer, a hook | `examples/scene-viking/` |
| Micro-drama Reel | 9:16 | References | photoreal | Reels, Shorts and TikTok reach | `examples/scene-friday/` |
| Animated story ad | 16:9 or 9:16 | Frames, then Edit video | stylized 3D animation | a product ad that tells a story, with a client revision | `examples/scene-grandpa/` |

Every format follows the dialogue rules in `kling4-higgsfield-rules.md`:
size each shot to its line, one speaker per shot, say the delivery, each line
at the start of its shot, hard cuts at stated seconds, no text on screen.

How to choose, if the user has not said: a product that must appear means
the animated story ad (or a micro-drama with the product last); reach on
short-form platforms means the micro-drama; a showcase or a hook for a longer
video means the cinematic scene.

---

## (a) The cinematic scene

**Structure:** an establishing wide with one narrator line, a quiet build in
close-ups, one silent spectacle shot in the middle, a reaction, a payoff line,
a hero shot to end.

| Beat | Time (30 s, 7 shots) | Shot | Audio |
|---|---|---|---|
| Open | 0-4 s | wide, establishing | one narrator line, the premise |
| Build | 4-8 s | close-up, character A | a short tense line |
| Build | 8-12 s | close-up, character B | a 3-word reaction |
| Spectacle | 12-19 s | wide | no dialogue, one big sound |
| Reaction | 19-22 s | close-up, character B | a 3-word line |
| Payoff | 22-26 s | close-up, character A | the payoff line |
| Hero | 26-30 s | low hero shot | one shouted word, a big sound |

**Why it works:** the narrator line sells the premise in four seconds; the
close-ups make the stakes personal before the reveal; the spectacle gets room
to breathe because nobody talks over it; the payoff line lands right after it,
while the viewer is still looking up.

**Pitfalls:**

- **Only one silent shot.** The spectacle is the one place a long silent shot
  belongs (about 7 s). Every other shot is sized to its line. `--check` lists
  the spectacle shot as a long silent shot; that finding is expected.
- **The narrator is a voiceover over a wide shot.** Mark it
  `"voiceover": true` so no lips are graded. Describe the voice in the shot
  line ("A narrator, an old man with a low, slow voice:").
- **The payoff needs its own close-up.** In an earlier 5-shot take the leader
  had the payoff and the shout in one long last shot, and his line started
  over the rower's close-up, 1.1 s before the cut. The 7-shot version
  splits it into a payoff close-up and a hero shot with one word.
- **A short shouted word ("Row!") can be dropped by the transcriber.** Listen
  before calling LINES.
- **Lightning and flashes** are fine on screen; `scene_grade.py` ignores
  flashes when the shapes stay put. Keep them in the last shot so a flash does
  not sit next to a planned cut.
- **Fog, sea and storms are forgiving** for photoreal: texture hides the
  plastic look that close photoreal faces in bright light can get.

---

## (b) The vertical micro-drama Reel

AI micro-dramas with dialogue are pulling millions of views on Reels. The
pattern: a relatable dilemma, fast shot / reverse-shot close-ups, one twist,
and a question as the caption.

**Structure:** a hook line in the first shot, an accusation, a defence, a
reveal, a silent insert of the twist, a reaction, a punchline.

| Beat | Time (30 s, 7 shots) | Shot | Audio |
|---|---|---|---|
| Hook | 0-4 s | over the shoulder, both in frame | A reads something out (the dilemma) |
| Defence | 4-7 s | close-up B | short, fast, nervous |
| Accusation | 7-12 s | close-up A | the longest line, cold |
| Turn | 12-16 s | close-up B | the reveal begins |
| Twist | 16-20 s | close insert | no dialogue, a small sound off screen |
| Reaction | 20-25 s | close-up A | the emotional line |
| Punchline | 25-30 s | close-up B | short, warm, funny |

**Why it works:** the hook is a situation everyone has an opinion about, so
the viewer picks a side in the first line; cutting back and forth between
close-ups gives the pace of a real drama (the ones that spread cut about
every 3 s); the twist turns the viewer's own assumption against them; the
punchline gives a reason to rewatch and share.

**Rules for this format:**

- **One speaker per shot, close-ups cutting back and forth.** Two people
  talking in one shot made "I ruined it" come out as "I ruined of did".
- **Contractions and fillers:** "Babe. Babe,", "'Cause", "kinda". Natural
  speech is the whole point of the format.
- **Never show the phone screen, a letter or a sign.** A character reads it
  out. AI text garbles.
- **Caption = a question for the comments:** "Would you have read it?" It
  turns the dilemma into replies. Write it in `scene.json` as `caption`.
- **Product last or none.** If there is a product, it is the twist or sits in
  the last shot. A product in the first half turns the drama into an ad and
  the viewer leaves.

**Pitfalls:** long 5 to 7 s shots carrying 4 to 8 word lines produced long
silent gaps and robotic delivery in the first take; seven shorter shots sized
to the lines fixed it. Lines can still start 2 to 4 s into a shot; grade for it.

---

## (c) The animated story ad

**Structure:** a small problem, a person who solves it with the product, the
product saving the day in the last third, a short spoken tag line.

| Beat | Time (30 s, 4 shots) | Shot | Audio |
|---|---|---|---|
| Problem | 0-8 s | medium wide, main character | the old thing fails; one grumbling line |
| Gift | 8-17 s | closer, second character enters | one bright line; the product is handed over, unopened or unimpressive |
| Save | 17-24 s | close-up of the product, then the reaction | the product switches on, music starts; a 3-word reaction |
| Joy | 24-30 s | wide, both characters, product in frame | the tag line as a voiceover |

**Why it works:**

- **Stylized animation holds better than photoreal over 30 s.** Rounded
  cartoon faces and warm, soft light do not get the plastic skin or face drift
  that 30 s of photoreal close-ups can get, and an animated family scene is
  far from the uncanny valley.
- **The product arrives in the last third, as the answer.** By 17 s the viewer
  cares about the character, so the product is the payoff, not an
  interruption.
- **A short spoken tag line** (product name plus four or five words) lands as
  a voiceover over the wide shot. For a made-up name, add how to say it:
  `pronounced "Kill-n": "Kiln. Small speaker, big room."`
- **The client revision is built in.** Make the colour change with Edit video
  (see below), and check it with `drift.py`.

**Mode:** Frames, with a start frame and an end frame (and optionally middle
frames on the web Frames tab, at the gift hand-off and when the product is on
the shelf). Frames pins the composition and the product's shape; References
cannot be combined with it. The prompt still carries the shot list, the lines
and the hard cuts. Make the frames as in `reference-sheets.md` (start frame,
then the end frame as an edit with the product still).

**Pitfalls:**

- Shots are timed to the keyframe beats, not to the lines, so they run 7 to
  9 s with short lines. `--check` flags them as long silences. That is
  expected here: the action (the radio dying, the gift being opened, the
  dance) fills the time. Keep each line at the start of its shot anyway.
- The tag line is a voiceover over a wide shot: mark it `"voiceover": true`.
- One shot, one framing. A "Cut to ..." inside a shot line adds an unplanned
  cut; if a shot needs two framings, make it two shots.
- If the image filter blocks a start frame, see the safety-filter tip in
  `reference-sheets.md`.

---

## Edit video lessons (the client colour change)

Tested on the animated ad: the speaker changed from terracotta to matte black
with a still of the black speaker as the reference image. The colour changed,
and two things came back that nobody asked for:

1. **An extra object appeared early.** A black speaker stood on the wall shelf
   before the gift was even opened. The model "explained" the product by
   putting it everywhere.
2. **Motion was re-animated.** The gift hand-off and the dance were played
   differently from the source, so the edit was a new performance, not a
   recolour.

The prompt had a long keep list, but it did not forbid new objects and did
not ask for the original motion. What to write:

- **Scope the change by place and time:** "everywhere the speaker appears, in
  the gift box, on the wall shelf and in the last shot".
- **Name every element to keep:** each character with their face, clothes,
  voice and lines; the room and its light; each prop; the cuts, the camera,
  the timing, the music and the voiceover. A blanket "keep everything else"
  fights the change.
- **Forbid new objects, and say where the target is absent:** "Do not add any
  object that is not in the original video. The wall shelf stays empty until
  17s."
- **Ask for the original motion, frame for frame:** "Every movement, pose,
  gesture and camera framing stays exactly as in the original video, frame
  for frame; only the speaker's color changes."

Put the fix line at the top of the Edit prompt, then the change, then the keep
list. The fix line was written from this test's result; check the next pass
with `drift.py` and look at the worst frames, especially before the product's
first appearance (any change there is an extra object).

Test the edit on a 10 s slice where the target is on screen the whole time at
720p before paying for the full clip.

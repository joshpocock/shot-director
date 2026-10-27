# Kling 4.0 on Higgsfield: rules a plan must respect

Interface facts were checked on 2026-10-23; References mode dialogue rules
on 2026-10-27. Interfaces change. If the screen
disagrees with this file, trust the screen, tell the user, and update this file.

## Frames mode (keyframes)

- Up to 10 frames. **The first upload is the start frame. The last upload is
  pinned to the final frame of the clip.** Frames in between follow upload
  order.
- **There is no per-keyframe time field.** Middle frames are timed only by the
  timestamps you write in the prompt ("8s: matches @image_2 ..."). So in the
  plan: keyframe 1 is at 0 s, the last keyframe is at the clip duration, and
  only the middle times are choices.
- **No aspect ratio control in Frames.** The first keyframe sets the output
  shape. Make every keyframe the same pixel size and ratio (16:9 for YouTube,
  9:16 for Shorts and Reels).
- **JPEG or PNG only** for keyframes (the file picker may offer WebP or HEIC;
  do not use them). At least 300 px on the short side, aspect between 1:2.5
  and 2.5:1. PNG at one fixed size is safest.
- Duration is a slider from 3 to 30 s in whole seconds.
- No Elements in Frames. The prompt is optional there, but always write one.
- **No audio toggle.** Describe the sound you want and say what you do not
  want: "No music, no voice, no subtitles."
- **Multi-shot cuts are the default.** For one take, the first line of the
  prompt must ask for it: "One continuous shot for the full 30 seconds. No
  cuts, no angle changes, no scene changes."

## Tags (@image_1, @video_1)

- Typing @ in the prompt box opens a picker. The chips it inserts are sent as
  `@image_1`, `@video_1`, `@element_1`.
- **Hand-typed tags are plain text and do not link to anything.** Write the tag
  in the plan so the user knows where it goes, and tell them to delete it and
  insert it from the @ picker.
- In Frames, keyframe 1 to N are image 1 to N in upload order. In Edit video,
  the source clip is always video 1 and reference images are numbered in
  upload order.

## Edit video

- Source clip: mp4 or mov, **3 to 30 s, up to 200 MB**. You can add image
  references (for example a still of the product in its new colour).
- Prompt shape: `Edit @video_1.` then exactly what changes and how, then
  `Keep unchanged:` and a list of named elements. Do not write
  "Reference @video_1"; that reads as reference generation, not an edit.
- Describe the target by its place in the scene and the time span it is
  visible ("everywhere the speaker appears, from the moment it is revealed to
  the last frame"). Name the parts of the target that must not change with it
  (the light bar stays white).
- A blanket "keep everything else unchanged" can fight the change you asked
  for. Name the elements to keep instead, and always include "the overall
  brightness and colour of the room, the camera move and the timing".
- The Edit tab has its own Duration control. Set it to the source length.
- The edit's audio may be regenerated rather than copied.
- Test an edit on a short slice (about 10 s where the target is on screen the
  whole time) at 720p before paying for the full clip.

## References mode (multi-shot dialogue scenes)

Checked in real generations on 2026-10-27 (two takes of a 30 s two-person
micro-drama and one 30 s three-speaker movie scene, all References mode).

- **Kling 4.0 generates 3 to 30 s in one go, multi-shot, with dialogue and lip
  sync.** You write the shot list and the lines; it cuts and voices them.
- **References and Frames cannot be combined in one task.** A scene with
  characters uses References (one reference image per character, prop or
  product). If you need a pinned start or end frame, that is Frames mode and
  the reference images go.
- Open the prompt with one sentence per reference image saying its job:
  "Reference image 1 is the leader: keep his face, beard, scar, helmet and
  cloak exactly the same in every shot." Upload order sets the number.
- **Size each shot to its line.** A 3 to 6 word line gets a 3 to 4 s shot.
  5 to 7 s shots carrying 4 to 8 word lines produced long silent gaps. Long
  silent shots only for spectacle (the creature rising, the ring box).
- **One speaker per shot.** A final shot with two people talking made the
  lines collide: "I ruined it" came out as "I ruined of did". Split it into a
  shot / reverse shot.
- **Say the delivery** in the prompt, once for the scene and per line: "every
  line is delivered in casual, natural English at normal conversational
  speed with real emotion, no robotic delivery, no long pauses before lines".
  Without it the delivery read robotic.
- **Contractions and fillers read human:** "'Cause", "Babe. Babe,", "kinda".
  Write the line exactly as it should be said.
- **Put each line at the start of its shot** in the prompt, so the cut does
  not wait for it. In testing, lines often still started 2 to 4 s into a
  shot, and one line began over the previous shot before the cut; grade for
  it.
- **Hard cuts at stated seconds.** One line listing them ("Seven shots with
  hard cuts at 4s, 7s, 12s, 16s, 20s and 25s."), then one line per shot
  starting with its window ("4-7s, shot 2: ..."). Cuts landed within about
  0.5 s of the stated time on most shots, and up to 1.5 s late on some.
- Add "No fades." and end with the sound line plus "No music, no subtitles."
  (drop "no music" when you want a score).
- Say "Only one person speaks in each shot."
- Never show text on screen in the scene (a phone screen, a sign): have a
  character read it aloud instead. AI text garbles.
- A transcript can drop very short shouted words ("Row!") and swallow small
  contractions ("we've found" heard as "we found"). Listen before you call a
  line wrong.

## Money

- **Duration and quality carry across tabs and page reloads.** A 28 s setting
  in Frames is still 28 s when you open Edit video. Read the credit quote on
  the Generate button before every click.
- **Prices change.** Never quote a credit price from memory. Ask the user what
  the button says and log it with `tally.py add`.
- Explore short and cheap (720p, the shortest duration that shows the beat),
  then go full length and 1080p once the beats land.

## Never claim

- 4K output, HDR, or a two-minute extension on Higgsfield. None of these are
  available there as of the check date.

## Prompt craft

Kling's own guidance plus rules that held up in hands-on tests.

1. **Keyframes show the important moments. The prompt explains how the video
   moves between them.**
2. **Fewer, more different keyframes.** Add one only where the visual state
   must change. 3 to 5 for a 30 s clip. Space them on real beats, not evenly:
   even spacing gives stop-start motion.
3. **Change one or two things per keyframe.** Adjacent frames that are too
   similar stall the motion; frames that change character, place, product,
   angle, light and style at once break it.
4. **Build keyframes from one base image.** Make keyframe 1 from scratch, then
   make each next keyframe as an image edit of the previous one, with the same
   image model, changing one or two things. Faces, products and rooms then
   match before video generation starts.
5. **Whatever is in a keyframe, the model will try to explain.** Clean every
   frame of stray objects. Keep hands and people out of frame at keyframe
   moments, and time hand entries so they leave before each keyframe time.
6. **State on and off explicitly.** "Light bar unlit and pale grey" in one
   frame, "light bar glowing soft white" in the next, so the change has
   something to change from.
7. **Restate props that persist.** If the lid and tissue stay on the desk,
   say so in every keyframe prompt, or the image edit may drop them and the
   video model has to explain the disappearance.
8. **Camera must agree with the keyframes.** If keyframes 1 to 3 share one
   camera position, the camera is locked until keyframe 3. A push-in that
   starts at 0 s cannot also match two locked frames. Plan the move only
   between keyframes whose framing differs. For a continuous push-in through
   middle frames, make those frames digital crops of their own edit (about 92%
   and 80%), scaled back to the same pixel size.
9. **One scene, one subject, one camera rule.** A prompt that reads like a
   list of places becomes a list of shots.
10. **One action and one camera move per timestamped beat.** Beats in the same
    order as the keyframes. Name the keyframe at its time ("17s: matches
    @image_3").
11. **Restate the product.** One line with shape, size, colour and finish, plus
    "Its shape, size and color stay exactly the same throughout."
12. **Concrete words.** "Soft morning light from the window on the left", not
    "premium look". Avoid negative prompts except "no subtitles" and "no
    music".
13. **Change one thing per retry** (one prompt line, one keyframe, or the
    duration) so you know what fixed it.
14. Stylized looks hold a long single take better than intense photoreal
    action. Simple, calm realism works.

## Content rules

- No text, logos or brand marks on products. Original IP only: no known
  characters, no real products, no real people other than the user (with
  their consent).

# Terracotta desk speaker: unbox to hero, one take

Brief: "30-second ad for a small matte terracotta desk speaker, unboxed on a desk, ending on a hero shot."

Duration: 30 s | Keyframes: 4 | Aspect: 16:9 (set by keyframe 1) | Test at 720p, final at 1080p

Camera: locked in the keyframe 1 position from 0 to 17 s, then one slow push-in that lowers to desk height and comes to rest on keyframe 4 at 30 s.

## Subject

A small matte terracotta desk speaker shaped like a squat rounded block, about the size of a coffee mug, smooth surface with no visible seams, one thin white light bar across the lower front face. No text, no logo, no buttons, no fabric, no grille.

Rules: no text or logos on the product, original design only, same shape, size and colour in every frame.

## Keyframes

| # | Role | Time | Must be true in this frame |
|---|---|---|---|
| 1 | setup | 0 s (start frame) | Closed plain kraft box slightly left of centre on a walnut desk. Window on the left edge, soft morning light. Empty desk on the right. Plant out of focus back right. Chest-height three-quarter camera. No hands. |
| 2 | discovery | 8 s | Same camera. Lid flat on the desk left of the box. Speaker's top half visible in white tissue. Light bar **off**. No hands. |
| 3 | use | 17 s | Same camera. Box, tissue and lid unchanged. Speaker standing on the desk right of centre, facing camera. Light bar **on**. No hands. |
| 4 | hero | 30 s (final frame, pinned) | Camera at desk height, half the distance. Speaker fills the right half, light bar on. Box, lid, plant and window soft behind it. No hands. |

Why these times: 8 s is when the reveal is complete, 17 s is when the speaker is placed and lit, and the last 13 s are the push-in. The last keyframe is always the final frame on Higgsfield, so it is 30 s, not "about 27".

### Product still (reference only, not uploaded to Frames)

```
Product photo on a plain light grey background, soft studio light. A small matte terracotta desk speaker shaped like a squat rounded block, about the size of a coffee mug, smooth surface with no visible seams, one thin white light bar across the lower front face. No text, no logo, no buttons, no fabric, no grille.
```

### Keyframe 1 (from scratch)

```
Photorealistic 16:9 photo. A closed plain kraft-paper box with no printing, lid on, sits slightly left of center on a walnut desk. A window at the left edge of the frame lets in soft morning light from the left. Empty desk space to the right of the box. A small green plant softly out of focus in the back right. Camera at chest height, looking slightly down, three-quarter angle. No text, no logos, no people, no hands.
```

### Keyframe 2 (edit of keyframe 1, second image = product still)

```
Same photo, same desk, same window and light, same plant, same camera position and framing. The box lid is off and lies flat on the desk just left of the box. Inside the open box, the speaker from the second image sits upright in white tissue paper, top half visible, its light bar unlit and pale grey. Use the second image only for the speaker's shape and color. No hands. Change nothing else.
```

### Keyframe 3 (edit of keyframe 2)

```
Same photo, same desk, same window and light, same plant, same camera position and framing. The open box, the white tissue paper inside it and the lid stay exactly where they are. The speaker now stands upright on the desk just in front of and to the right of the box, slightly right of center, facing the camera, its light bar glowing soft white. No hands. Change nothing else.
```

### Keyframe 4 (edit of keyframe 3, the planned camera move)

```
Same scene, same moment, same light direction and color. The camera has moved forward and down to desk height, about half the distance to the speaker, looking straight at it. The speaker fills the right half of the frame, its light bar glowing soft white. The box, the lid, the plant and the window are softly out of focus behind it on the left. No hands. Change nothing else.
```

## Consistency check (lay the four images side by side before you generate)

- [ ] All four are PNG, the same pixel size, 16:9
- [ ] Same desk grain, window, plant and light direction in all four
- [ ] Box, lid and tissue present and in the same place in keyframes 2, 3 and 4
- [ ] Light bar off in 2, on in 3 and 4
- [ ] Speaker shape, size and colour identical in 2, 3 and 4
- [ ] No hands or people in any keyframe
- [ ] Keyframes 1, 2 and 3 share one camera position; only 4 differs (the planned push-in)
- [ ] Empty desk on the right in 1, speaker right of centre in 3, so the push-in lands on 4
- [ ] No text, logos or stray objects anywhere
- [ ] Prompt beats name the keyframes in upload order

## Frames prompt

Upload kf1.png, kf2.png, kf3.png, kf4.png in that order. Delete each typed `@image_N` below and insert it with the @ picker, or it will not link.

```
One continuous shot for the full 30 seconds. No cuts, no angle changes, no scene changes.
@image_1 is the first frame and @image_4 is the last frame. The camera stays locked in the @image_1 position until 17s, then makes one slow, smooth push-in that lowers to desk height and comes to rest exactly on @image_4 at 30s.
The product is a small matte terracotta desk speaker, a squat rounded block with a smooth surface with no visible seams, no buttons, no fabric, one thin white light bar on the front, no text or logo. Its shape, size and color stay exactly the same throughout.
0-7s: A closed kraft box sits on a walnut desk in soft morning light from the window on the left. Two hands enter from the bottom of the frame, lift the lid straight up, lay it flat beside the box and leave the frame.
8s: matches @image_2, the speaker sits in white tissue in the open box, its light bar off.
9-16s: The hands come back, lift the speaker out, stand it on the desk in front of and to the right of the box, and leave the frame.
16-17s: The light bar fades on. 17s matches @image_3.
17-30s: The camera slowly pushes in and lowers toward the speaker while the light bar pulses gently. The box, lid and window fall softly out of focus. The camera stops on @image_4.
Sound: paper rustle, a soft chime when the light bar comes on, quiet room tone. No music, no voice, no subtitles.
```

## Edit prompt (client note: "make it matte black")

Source: the keeper clip (pick it from Generations). Reference: `black-still.png`, made by editing keyframe 4 with the prompt below. Set Duration to the source length and read the quote on Generate.

Black still:

```
Change only the speaker's body color from matte terracotta to matte black, same matte finish, no new reflections. The light bar stays glowing soft white. Keep the brightness and color of the room exactly the same. Change nothing else.
```

Edit video:

```
Edit @video_1. Change only the speaker's body color: everywhere the speaker appears, from the moment it is revealed in the tissue paper to the last frame, it becomes matte black like the speaker in @image_1, same matte finish, same shape, size, position and movement. The light bar stays white and comes on at the same moment.
Keep unchanged: the kraft box and lid, the white tissue paper, the hands, the walnut desk, the plant, the window light and the overall brightness and color of the room, the camera move and the timing.
```

Test it first on a 10 s slice where the speaker is on screen the whole time (17 to 27 s) at 720p.

## Scoring

- Keyframe 1 is the start frame: it hits by construction and is not scored.
- Keyframes 2, 3 and 4: HIT 1 point, LATE or EARLY 0.5, MISS 0.
- No cuts in the clip: 1 point.
- Score out of 4.
- HIT: the best match is within about 1 s of the planned time and the content matches. LATE / EARLY: 1 to 3 s off (give the offset). MISS: content wrong or more than 3 s off.
- The human's call is final.

## Run sheet

1. Make the product still, then keyframe 1, then keyframes 2 to 4 as edits, all with the same image model, 16:9, PNG.
2. Run the consistency check. Fix any frame that fails before spending video credits.
3. Frames tab: upload in order, paste the prompt, insert tags with the @ picker. Set Duration and Quality (720p for tests). Read the Generate quote, log it (`tally.py add`), generate.
4. Download, grade (`grade.py`), make one prompt change, repeat until 3.5 / 4 or better.
5. Full length at 1080p, grade, pick the keeper.
6. Edit video with the client note, test slice first. Drift check (`drift.py`) on source vs edit.
7. `tally.py summary` for the bill.

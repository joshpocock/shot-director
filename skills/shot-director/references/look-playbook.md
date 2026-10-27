# Look playbook: stills that make the video look expensive

The video model copies the look of the images it is given. A flat, evenly lit
start frame becomes a flat, evenly lit 30 s clip, however good the motion is.
So the look is decided in the stills (keyframes, start and end frames,
reference images), before any video credits are spent.

Read this in PLAN mode before writing image prompts, and in PLAN-SCENE mode
when the scene has a product or a set that must read as premium. It applies to
products, characters and whole scenes.

Learned on a 30 s product ad (a small matte terracotta desk speaker), a
cinematic sea scene, a restaurant micro-drama and an animated living room, all
on Kling 4.0 (2026-10). The rules are general; the examples are those scenes.

## Why plain AI stills look cheap

The first build of the speaker ad was clean and consistent and still looked
like a stock photo. Six reasons, all common:

1. **Flat, frontal light.** No lit side, no shadow side, no edge light. Nothing
   says where the light comes from or what time it is, so there is no mood.
2. **No contrast between subject and set.** A terracotta speaker on a red-brown
   wooden desk: same hue family, same brightness. The product does not separate
   from the surface.
3. **A busy, bright background.** A blown-out window and a big plant compete
   with the product.
4. **Generic props.** A plain cardboard shipping box reads as a delivery, not
   a launch.
5. **Deep focus everywhere.** Sharp front to back reads as a phone photo.
   Shallow focus only in the hero frame makes three quarters of the ad cheap.
6. **Texture escalation.** Asked for a "fine matte finish", the image model
   twice gave the speaker a knitted fabric weave.

## Do

1. **Contrast the subject against the set.** Pale subject on a dark set, or
   dark on pale, and a different hue family. A terracotta or matte black
   product on pale warm stone reads at a glance.
2. **Describe what the light does, not how it feels.** Not "premium look" or
   "cinematic lighting". Write the effect you would see:
   - "Low warm late-afternoon sun from behind on the left draws a thin bright
     edge along the top of the speaker."
   - "Soft shadows stretch toward the camera. The shadow side stays soft and
     readable, warm grey, never black."
   - "The tissue paper glows slightly where the sun shines through it."
3. **One palette, with the subject the brightest or most saturated thing in
   frame.** One dominant colour temperature, at most one accent. In the speaker
   ad the whole frame is warm (cream stone, charcoal box, warm plaster wall) and
   the one cool colour is the product's light bar, so the eye goes to it.
4. **Name the lens, the camera height and the focus.** "50 mm lens, camera at
   seated eye height, three-quarter angle looking slightly down, shallow depth
   of field." Shallow focus from the first frame, not just the hero. Keep one
   lens for the whole clip; move the camera, not the focal length, or the
   move reads as a zoom or a cut.
5. **Keep the camera simple.** One move per clip, written once. State stillness
   as a positive instruction: "The camera stays locked on a tripod until 17s."
   Polish comes from light and lens, not from extra moves.
6. **Fix the light direction and give every light a reason.** Each source is
   something in the room (a window out of frame, a lamp, a candle, the
   product's own light). Say it does not move: "The sunbeam and its shadows
   stay fixed in place for the whole shot." The model then never has to
   invent or move a light.
7. **Name the materials, and fence off the wrong ones.** "Smooth matte
   terracotta with a very fine even grain like unglazed fired clay, no fabric,
   no mesh, no weave." Restate the fence in every frame that shows the
   subject, including the colour-change still.
8. **Pare the set back to two or three objects** and make the props look
   designed: "a rigid two-piece box in deep charcoal-brown matte paper, crisp
   corners, no printing" instead of a shipping box.
9. **Concrete wardrobe for anyone in frame,** described identically every
   time: "one pair of slim hands with cream knit sleeve cuffs, no rings, no
   watch."

For characters and scenes the same rules hold. A scene gets one dominant
light ("cold blue dawn on a dark stormy sea in thick fog", "a warm, dimly lit
restaurant booth at night, candle on the table", "warm lamp light in a cozy
living room at night"); a character gets concrete, distinctive features and
wardrobe (see `reference-sheets.md`).

## Drop

These cost more than they add in a long take, and several make a later Edit
video pass drift:

| Drop | Why |
|---|---|
| Moving light: leaf shadows, flicker, passing car lights | The model animates it over 30 s; it reads as a timelapse and makes drift checks noisy |
| Haze, smoke, fog machines indoors | Shimmers; the model invents volume that changes between frames |
| Lens flares | They move with the camera and change in an edit |
| Glossy or mirrored surfaces | Reflections drift and re-render differently every frame |
| Orbits, macro moves, a second camera move | More moves, more regenerations; a one-take wants one move |
| Bright windows and busy backgrounds | They compete with the subject |
| "Premium", "cinematic", "high-end", "vintage feel" | Abstract words tell the model nothing |
| Text, logos, brand marks | Text garbles, and it is not original IP |

A few slow dust motes in a sunbeam are the one "real air" cue worth trying in
a video prompt (never in a still). Cut them first if anything slips.

The biggest risk in this look is the light itself: a low sun is what makes the
frames look expensive and also the thing the model most likes to animate.
Only a short 720p test proves it holds.

## Prompt fragments

Product still (the shape reference for everything else):

```
Photorealistic studio product photo, 16:9. A small desk speaker shaped like a squat rounded block, about 11 cm wide and 9 cm tall, with softly rounded edges. Its body is smooth matte terracotta with a very fine even grain like unglazed fired clay, no seams, no buttons, no fabric, no mesh, no weave. One thin light bar runs across the lower front face, glowing soft cool white. It stands on a seamless warm cream background. Warm light from the back left draws a thin bright edge along its top and left side, a soft fill keeps the front evenly visible, and it casts a soft short shadow toward the camera. 85 mm lens, eye level with the speaker. No text, no logo.
```

Set and light (inside a base frame):

```
50 mm lens, camera at seated eye height, three-quarter angle looking slightly down, shallow depth of field. A desk top of pale honed travertine stone, warm cream with a few tiny natural pits, satin finish. ... Low warm late-afternoon sun comes from behind on the left: a long sunbeam crosses the desk, a thin bright edge lights the top of the box and the speaker, and soft shadows stretch toward the camera. The shadow side stays soft and readable, warm grey. Behind the desk, a warm plaster wall in soft shadow, and a single olive branch in a small clay vase at the back right, strongly out of focus. No people, no hands, no text.
```

Colour-change still (keeps the rim so a dark product does not become a hole):

```
Edit this image. Change only the speaker's body color from matte terracotta to matte black, smooth like fine powder-coated ceramic with the same very fine grain, no fabric, no mesh, no weave, no shine. The thin bright edge of light along its top and left side stays, so its shape is still clear. The light bar keeps glowing soft cool white. Keep the brightness and color of the room exactly the same. Change nothing else.
```

Under every image prompt in a plan, add one line: "Why this looks
expensive: ..." If you cannot finish that sentence, the frame is not done.

## Build order

1. **Product still first** (if there is a product): the shape, colour and
   finish reference for every later frame.
2. **Then the base frame: the one that contains every object.** Not
   necessarily keyframe 1. In the speaker ad the base was the 8 s frame (box
   open, lid beside it, speaker in the tissue), because it shows everything
   the other frames need.
3. **Derive every other frame by editing the one before it, changing one or
   two things,** with the same image model. Open with "Edit this image. Same
   photo, same ..., same camera position and framing", restate the props that
   persist, end with "Change nothing else."
4. **Put the product still in as a second image** whenever the product's shape
   must hold through a big change (a camera move to a close hero, a restyle):
   "Edit the first image. ... The speaker keeps exactly the shape, proportions
   and finish of the speaker in the second image."
5. **Build the start frame last when it hides things.** A closed box made from
   scratch never matches the open box made later. Make the open frame, then
   edit it back: "Put the lid back on the box: ... in exactly the same
   position and size." The same trick works for any "before" state (a dark
   room before the lamp, an empty shelf before the product).
6. The colour-change still for a later Edit video pass is an edit of the hero
   frame, so the light and set match.

For a Frames scene with characters (a start image and an end image, as in
`examples/scene-grandpa/`), make the start frame, then make the end frame as
an edit of the start frame with the product still as the second image. The
room, the characters and the product then match before video generation.

Use one image model for the whole set. Do not mix models inside a chain. If
two edits in a row move the furniture, rebuild the chain rather than patching
frames.

## Consistency check

Open every still side by side before any video credits are spent:

- same pixel size and ratio, PNG
- same surface, props, wall and background objects in every frame
- light from the same side in every frame; same colour temperature
- the subject's shape, size, colour and finish identical (watch for texture
  creeping in: fabric, mesh, knit)
- on and off states exactly as planned (light bar unlit, then lit)
- props that persist are present; props that should be gone are gone
- no stray objects, no text, no logos
- camera identical where the plan says locked, different only where the move
  is planned

If one frame moved the furniture or the light, redo that frame only, from its
parent in the chain.

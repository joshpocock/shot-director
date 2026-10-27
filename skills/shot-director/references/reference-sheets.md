# Reference sheets: images that keep identity across cuts

In Kling 4.0 References mode every character, creature, prop or product that
must look the same in every shot gets one reference image. The scene's SAME
mark is won or lost here, before the video is generated.

Read this in PLAN-SCENE mode, before writing the References table, and give
the user one image prompt per reference. **You write the prompts; the user
makes the images.** When they send them back, open each one and check it
against the list at the end.

Learned on three 30 s References scenes (two photoreal people, a three-speaker
sea scene with a giant robot) and one animated Frames scene, 2026-10-27.

## The rules

1. **One job per reference.** One image is one character, or one creature, or
   one product. Do not put two people in one reference, and do not use a scene
   still as a character reference. Two or three strong references beat five
   weak ones.
2. **Plain framing, plain background, plain light.** The model should learn
   the subject, not a room:
   - characters: waist up, facing the camera, 3:4 portrait;
   - creatures: front view, head and torso;
   - products: a studio product photo on a seamless background, the whole
     object in frame.
   - plain dark grey studio background (or seamless warm cream for a
     product), soft even light, the same light for every reference in a scene.
3. **Describe the identifiers, specifically.** Age range, build, hair (colour,
   length, how it is worn), one or two marks that are easy to see (a scar, a
   braid, freckles), wardrobe pieces with colour and material, one accessory.
   These are the details the model can drift on, and the details you grade.
   For a product: shape, size, colour, finish, and what it does not have.
4. **Neutral, calm expression** for people ("stern, calm expression"). The
   scene prompt adds the emotion; a reference with a big expression leaks it
   into every shot.
5. **Original faces only.** No real people other than the user (with their
   consent), no known characters, no real products.
6. **End every prompt with "No text, no logos."**
7. **Same aspect ratio and size for all references in a scene.** PNG.

## Upload order sets the number

The first image uploaded is Reference image 1, the second is Reference image
2, and so on. The References table in `scene.md` lists them in upload order,
and the prompt names them in that order.

## Restate the keep-line in the prompt

Open the Kling prompt with one sentence per reference, naming the same
identifiers the reference prompt described, in the same words:

```
Reference image 1 is the Viking leader: keep his face, grey braided beard, scar through his left eyebrow, iron helmet and fur cloak exactly the same in every shot. Reference image 2 is the young rower: keep his face, freckles and red-brown hair the same in every shot. Reference image 3 is the giant sea robot: keep its shape, rusted iron, barnacles and amber eyes the same in every shot.
```

If a detail drifts in a take (a missing earring, a beard that changes), the
one fix is to name that detail in its reference's job sentence.

## Templates

Fill the angle brackets. Keep the fixed parts word for word.

### Character (photoreal)

```
Photorealistic character reference portrait, waist up, facing the camera, plain dark grey studio background, soft even light. <Who, with age>: <hair and face, with one or two visible marks>, <eyes>, <headwear if any>, <outer layer, with colour and material> over <inner layer>, <one accessory or strap>. <Calm expression word>, calm expression. No text, no logos.
```

Example that held across seven shots:

```
Photorealistic character reference portrait, waist up, facing the camera, plain dark grey studio background, soft even light. A Viking chieftain in his fifties: long grey beard braided at the chin, weathered skin, a pale scar running through his left eyebrow, piercing grey eyes, a round iron helmet with a nose guard, a heavy brown fur cloak over chain mail and dark wool, a leather strap across his chest. Stern, calm expression. No text, no logos.
```

The same pattern made the other people in the examples; these are the
identifiers each one carried, the words reused in its keep-line:

- the young rower: about seventeen, freckles, red-brown hair, no helmet;
- the woman: late twenties, dark curly hair, gold hoop earrings, cream knit
  top;
- the man: late twenties, short beard, navy overshirt.

### Creature

```
Photorealistic creature design reference, front view, head and torso, plain dark grey studio background, soft even light. <What it is and its scale>: <head and eyes, with the one feature you want to see in every shot>, <surface materials and colours>, <what grows on it or hangs off it>. No text, no logos.
```

Example:

```
Photorealistic creature design reference, front view, head and torso, plain dark grey studio background, soft even light. A colossal ancient robot that has slept under the sea for centuries: a broad rounded head, two large round eyes glowing warm amber, dark weathered iron plates streaked with orange rust, clusters of barnacles and strands of seaweed hanging from its shoulders. No text, no logos.
```

Give the creature one signature feature that survives darkness, fog and
water (glowing eyes worked). The scene can then light it badly and it still
reads as the same creature.

### Product

```
Photorealistic studio product photo, <aspect>. <What it is, shape, size in cm, proportions>, <edges>. Its body is <colour and finish, with a texture comparison>, <what it does not have: no seams, no buttons, no fabric, no mesh, no weave>. <Its one feature, with on or off state>. It stands on a seamless <colour> background. <Light from one side, what it draws>. <Lens>, eye level with the product. No text, no logo.
```

A full example is in `look-playbook.md` (the product still). The fence ("no
fabric, no mesh, no weave") matters: without it a "fine matte finish" turned
into a knitted texture twice.

### Stylized (animated) characters

```
Cozy stylized 3D cartoon render, family animation look, soft rounded shapes, warm colors. <Who>: <hair, face, glasses, clothes>, <expression, kept light>. <Setting, one sentence>. No text, no logos.
```

Describe the look by its features ("soft rounded shapes, warm colors,
family animation look"), not by naming a studio or a film.

## Start and end frames instead of references (Frames mode)

References and Frames cannot be combined in one Kling 4.0 task. An animated
ad with planned keyframes is a Frames scene, so the characters are held by the
frames themselves:

1. Make the start frame from scratch: the room, the characters, the props, the
   light.
2. Make the end frame as an **edit of the start frame**, with the product
   still as a second image: same room, same characters, the new pose and the
   product in place. Everything then matches.
3. Optional middle frames are edits of their neighbours, one or two changes
   each (see `look-playbook.md`, Build order).

## Safety-filter false positives

Image filters sometimes block an innocent prompt. In testing, a start frame
for the animated ad was blocked when it said "in the style of a modern feature
animation" and "grumpy grandfather ... scowling". The same picture passed as
"Cozy stylized 3D cartoon render, family animation look, soft rounded shapes,
warm colors ... a cheerful-looking older man ... frowning in a funny way".

If a prompt is blocked:

- reword instead of resubmitting the same text;
- describe the style by its features, never "in the style of" a studio, film
  or artist;
- soften harsh emotion words about older people and children ("frowning in a
  funny way", "unimpressed", not "scowling" or "angry");
- add one cheerful or cozy word to the scene description.

## Check the references before the video

When the user sends the images, open them side by side:

- one subject per image, framed as above, plain background
- the same light and the same aspect ratio for every reference
- every identifier in the job sentence is visible (the scar, the hoops, the
  amber eyes); if one is missing, the keep-line cannot hold it
- original faces, no text, no logos, no real products
- for Frames scenes: the start and end frames share the room, the characters
  and the product exactly

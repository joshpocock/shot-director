# Drift: speaker.mp4 vs speaker-black-leak.mp4

Compared 90 frames at 6 fps, 480x270, blur 7, threshold 25.

- Changed pixels per frame: mean **3.79%**, median 3.78%, max 6.26%.
- Main changed region (the edit targets: speaker): holds **62%** of all changed pixels, hotspot in the centre of frame.
- Changes outside the main region: mean **1.46%** of the frame, max 2.66%. Most of it in: middle right (70%), centre (16%), top right (15%).
- Other hotspots (changed in 25%+ of frames, outside the main one): middle right (2.53% of frame). Look there first.
- Brightness shift in unchanged areas: -0.00 (0 to 255 scale); colour shift 0.13. Above about 3 means the overall grade moved.

Worst frames: `worst_012.67s.png`, `worst_013.67s.png`, `worst_014.67s.png`

How to read it: a clean edit shows one hot region on the object you asked about, a high main-region share and almost nothing outside it. Changes outside the main region are the drift to check by eye in `worst/` and `diff.mp4`. A re-render nudges every pixel, so small scattered specks are normal; the numbers point your eyes, they are not proof.

# Drift: speaker.mp4 vs speaker-black-darker.mp4

Compared 90 frames at 6 fps, 480x270, blur 7, threshold 25.

- Changed pixels per frame: mean **1.87%**, median 1.98%, max 4.81%.
- Main changed region (the edit targets: speaker): holds **100%** of all changed pixels, hotspot in the centre of frame.
- Changes outside the main region: mean **0.00%** of the frame, max 0.00%. Most of it in: nowhere.
- Brightness shift in unchanged areas: -9.53 (0 to 255 scale); colour shift 1.52. Above about 3 means the overall grade moved.

Worst frames: `worst_012.83s.png`, `worst_013.83s.png`, `worst_014.83s.png`

How to read it: a clean edit shows one hot region on the object you asked about, a high main-region share and almost nothing outside it. Changes outside the main region are the drift to check by eye in `worst/` and `diff.mp4`. A re-render nudges every pixel, so small scattered specks are normal; the numbers point your eyes, they are not proof.

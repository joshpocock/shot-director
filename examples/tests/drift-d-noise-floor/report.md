# Drift: speaker.mp4 vs speaker-crf35.mp4

Compared 90 frames at 6 fps, 480x270, blur 7, threshold 25.

- Changed pixels per frame: mean **0.00%**, median 0.00%, max 0.00%.
- No changed pixels above the threshold in any frame.
- Brightness shift in unchanged areas: -0.06 (0 to 255 scale); colour shift 0.44. Above about 3 means the overall grade moved.

Worst frames: `worst_000.00s.png`, `worst_001.00s.png`, `worst_002.00s.png`

How to read it: a clean edit shows one hot region on the object you asked about, a high main-region share and almost nothing outside it. Changes outside the main region are the drift to check by eye in `worst/` and `diff.mp4`. A re-render nudges every pixel, so small scattered specks are normal; the numbers point your eyes, they are not proof.

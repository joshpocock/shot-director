# Grade: other-scene.mp4

Plan: `test-plan.json`. Clip: 1280x720, 360 frames, final frame at 14.96 s. Search +/- 3.0 s.

| KF | Role | Planned | Sim at planned | Best match | Offset | Suggested | Final (human) | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | setup | 0.00 s | 0.45 | 3.00 s (0.45) | +0.00 s | HIT |  | start frame: hits by construction; first output frame only scores 0.45 against kf1: wrong upload order or wrong file?; flat similarity curve: the match is ambiguous, judge by eye |
| 2 | discovery | 6.00 s | 0.44 | 3.54 s (0.44) | +0.00 s | MISS |  | best similarity 0.44 is under the floor 0.55: content probably wrong; flat similarity curve: the match is ambiguous, judge by eye |
| 3 | use | 10.00 s | 0.44 | 8.67 s (0.44) | +0.00 s | MISS |  | best similarity 0.44 is under the floor 0.55: content probably wrong; flat similarity curve: the match is ambiguous, judge by eye |
| 4 | hero | 14.96 s | 0.45 | 14.00 s (0.45) | +0.00 s | MISS |  | best similarity 0.45 is under the floor 0.55: content probably wrong; flat similarity curve: the match is ambiguous, judge by eye |

Cuts: none found.

Suggested score: **1 / 4** (keyframes 2 to 4 plus 1 for no cuts).

Images: `overview.png`, `pairs/kf<N>_pair.png`. Labels are suggestions; the human's call is final.

"""Render synthetic test clips for shot-director: a drawn desk scene with a terracotta speaker.

Every pixel is drawn here, so the repo's examples carry no third-party footage.
Usage: python make_synth.py OUT_DIR
"""
import os
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS, DUR = 1280, 720, 24, 15.0
TERRACOTTA = (64, 104, 196)  # BGR
BLACK = (32, 32, 34)


def lerp(a, b, k):
    return a + (b - a) * max(0.0, min(1.0, k))


def scene(t, product=TERRACOTTA, plant_shift=False, alt=False):
    img = np.zeros((H, W, 3), np.float32)
    if alt:
        # an unrelated cool-toned room: used for the "cut" splice and the wrong-clip test
        for y in range(H):
            img[y, :] = (lerp(120, 60, y / H), lerp(80, 40, y / H), lerp(40, 30, y / H))
        cv2.circle(img, (900, 260), 140, (200, 180, 90), -1)
        cv2.rectangle(img, (150, 420), (700, 700), (90, 70, 60), -1)
        return img
    # wall gradient and walnut desk with grain
    for y in range(H):
        img[y, :] = (lerp(150, 120, y / H), lerp(175, 140, y / H), lerp(200, 160, y / H))
    desk_top = 430
    img[desk_top:, :] = (40, 70, 110)
    for i in range(desk_top, H, 9):
        cv2.line(img, (0, i), (W, i + 6), (34, 60, 96), 2)
    # window on the left edge
    cv2.rectangle(img, (0, 60), (170, 400), (235, 240, 245), -1)
    cv2.rectangle(img, (0, 60), (170, 400), (120, 130, 140), 6)
    # plant, back right
    leaf = (60, 140, 70) if not plant_shift else (60, 90, 150)
    for cx, cy, r in [(1120, 330, 50), (1080, 300, 40), (1160, 290, 38), (1125, 260, 34)]:
        cv2.circle(img, (cx, cy), r, leaf, -1)
    cv2.rectangle(img, (1095, 360), (1150, 430), (70, 90, 120), -1)
    # kraft box, slightly left of centre
    bx, by, bw, bh = 420, 330, 240, 150
    cv2.rectangle(img, (bx, by), (bx + bw, by + bh), (110, 160, 200), -1)
    lid_on = t < 2.5
    if lid_on:
        cv2.rectangle(img, (bx - 10, by - 25), (bx + bw + 10, by + 5), (100, 150, 190), -1)
    else:
        cv2.rectangle(img, (bx - 230, by + bh - 20), (bx - 30, by + bh + 5), (100, 150, 190), -1)
    # speaker: in the box until 5 s, moved to the desk by 6 s
    sw, sh = 150, 110
    k = (t - 5.0) / 1.0
    sx = int(lerp(bx + 45, 720, k))
    sy = int(lerp(by - 50, desk_top - sh + 40, k))
    if t >= 2.5:
        top = sy
        bottom = sy + sh if k >= 1 else min(sy + sh, by + 10)
        cv2.rectangle(img, (sx + 18, top), (sx + sw - 18, bottom), product, -1)
        cv2.rectangle(img, (sx, top + 18), (sx + sw, bottom), product, -1)
        for cx in (sx + 18, sx + sw - 18):
            cv2.circle(img, (cx, top + 18), 18, product, -1)
        light = t >= 9.5
        bar_y = sy + sh - 30
        if bar_y < bottom:
            cv2.rectangle(img, (sx + 30, bar_y), (sx + sw - 30, bar_y + 6),
                          (250, 250, 250) if light else (150, 150, 150), -1)
    # camera: locked until 10 s, then a push-in toward the speaker
    z = lerp(1.0, 1.6, (t - 10.0) / 5.0)
    if z > 1.0:
        cx, cy = 795, 400
        M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
        img = cv2.warpAffine(img, M, (W, H))
    return img


def render(path, fn, crf=18):
    tmp = path + ".raw.mp4"
    vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    rng = np.random.default_rng(7)
    for i in range(int(DUR * FPS)):
        t = i / FPS
        f = fn(t) + rng.normal(0, 2.0, (H, W, 3))
        vw.write(np.clip(f, 0, 255).astype(np.uint8))
    vw.release()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "libx264",
                    "-crf", str(crf), "-pix_fmt", "yuv420p", path], check=True)
    os.remove(tmp)


def main(out):
    os.makedirs(out, exist_ok=True)
    j = lambda n: os.path.join(out, n)
    render(j("speaker.mp4"), lambda t: scene(t))
    render(j("speaker-late.mp4"), lambda t: scene(t * 0.8))
    render(j("speaker-cut.mp4"), lambda t: scene(t, alt=9.0 <= t < 11.0))
    render(j("other-scene.mp4"), lambda t: scene(t, alt=True))
    render(j("speaker-black.mp4"), lambda t: scene(t, product=BLACK))
    render(j("speaker-black-leak.mp4"), lambda t: scene(t, product=BLACK, plant_shift=True))
    render(j("speaker-black-darker.mp4"), lambda t: scene(t, product=BLACK) * 0.93)
    render(j("speaker-crf35.mp4"), lambda t: scene(t), crf=35)
    kf = os.path.join(out, "keyframes")
    os.makedirs(kf, exist_ok=True)
    for n, t in [(1, 0.0), (2, 6.0), (3, 10.0), (4, DUR - 1.0 / FPS)]:
        cv2.imwrite(os.path.join(kf, f"kf{n}.png"), np.clip(scene(t), 0, 255).astype(np.uint8))
    print("done", out)


if __name__ == "__main__":
    main(sys.argv[1])

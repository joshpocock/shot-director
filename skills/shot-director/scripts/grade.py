#!/usr/bin/env python3
"""
grade.py: compare a generated clip against the keyframes you planned.

For every planned keyframe it pulls the output frame at the planned time,
searches nearby for the moment that matches the keyframe best, and writes
side-by-side images so a person (and Claude) can call each keyframe a HIT,
LATE / EARLY or MISS. It also lists hard cuts. The script only suggests
labels. The human's call is final.

Requirements: Python 3.10+, numpy, pillow, opencv-python, ffmpeg and ffprobe on PATH.
No network access.

Example:
  python grade.py --plan plan.json --keyframes keyframes --video attempt-1.mp4 --out grade-1
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import numpy as np
    import cv2
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        f"grade.py: error: missing Python package ({exc.name}). "
        "Install with: pip install numpy pillow opencv-python\n"
    )
    sys.exit(2)

PROG = "grade.py"
DEFAULT_POINTS = {"HIT": 1.0, "LATE": 0.5, "EARLY": 0.5, "MISS": 0.0}


# ----------------------------------------------------------------- helpers

def die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"{PROG}: error: {msg}\n")
    sys.exit(code)


def warn(msg: str, bucket: list[str]) -> None:
    bucket.append(msg)
    sys.stderr.write(f"{PROG}: warning: {msg}\n")


def need_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        die(f"'{name}' was not found on PATH. Install ffmpeg (it ships ffprobe) and try again.")
    return path


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", "replace")[-1500:] if isinstance(exc.stderr, bytes) else ""
        die(f"command failed: {Path(cmd[0]).name} ...\n{err}")
    except FileNotFoundError:
        die(f"could not run {cmd[0]}")
    raise AssertionError  # unreachable


def probe(ffprobe: str, video: Path) -> dict:
    out = run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,r_frame_rate,duration:format=duration",
         "-of", "json", str(video)],
        capture_output=True,
    ).stdout
    data = json.loads(out.decode("utf-8", "replace") or "{}")
    streams = data.get("streams") or []
    if not streams:
        die(f"no video stream found in {video}")
    s = streams[0]

    def rate(txt: str | None) -> float:
        if not txt or txt in ("0/0", "0"):
            return 0.0
        if "/" in txt:
            a, b = txt.split("/", 1)
            return float(a) / float(b) if float(b) else 0.0
        return float(txt)

    fps = rate(s.get("avg_frame_rate")) or rate(s.get("r_frame_rate")) or 24.0
    dur = s.get("duration") or (data.get("format") or {}).get("duration") or 0
    return {"width": int(s["width"]), "height": int(s["height"]), "fps": fps, "duration": float(dur)}


def even(x: float) -> int:
    return max(2, int(round(x / 2.0)) * 2)


def decode_small(ffmpeg: str, video: Path, w: int, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Decode every frame at w x h RGB. Returns (frames, pts_seconds)."""
    with tempfile.TemporaryFile() as errf:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostats", "-loglevel", "info", "-i", str(video),
             "-an", "-sn", "-vf", f"showinfo,scale={w}:{h}:flags=area,format=rgb24",
             "-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1"],
            stdout=subprocess.PIPE, stderr=errf,
        )
        errf.seek(0)
        log = errf.read().decode("utf-8", "replace")
    if proc.returncode != 0:
        die(f"ffmpeg could not decode {video}:\n{log[-1500:]}")
    raw = proc.stdout
    fsize = w * h * 3
    n = len(raw) // fsize
    if n == 0:
        die(f"no frames decoded from {video}")
    frames = np.frombuffer(raw[: n * fsize], dtype=np.uint8).reshape(n, h, w, 3)
    pts = [float(m.group(1)) for m in re.finditer(r"\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:\s*(-?[\d.]+)", log)]
    if len(pts) != n:
        pts = []
    return frames, np.array(pts, dtype=np.float64)


def scene_scores(ffmpeg: str, video: Path) -> list[tuple[float, float]]:
    """ffmpeg scene-change score per frame: list of (pts_time, score)."""
    with tempfile.TemporaryFile() as errf:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostats", "-loglevel", "info", "-i", str(video), "-an", "-sn",
             "-vf", "scale=480:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score",
             "-fps_mode", "passthrough", "-f", "null", "-"],
            stdout=subprocess.DEVNULL, stderr=errf,
        )
        errf.seek(0)
        log = errf.read().decode("utf-8", "replace")
    if proc.returncode != 0:
        return []
    out: list[tuple[float, float]] = []
    cur_t = None
    for line in log.splitlines():
        m = re.search(r"pts_time:\s*(-?[\d.]+)", line)
        if m:
            cur_t = float(m.group(1))
            continue
        m = re.search(r"lavfi\.scene_score=([\d.]+)", line)
        if m and cur_t is not None:
            out.append((cur_t, float(m.group(1))))
            cur_t = None
    return out


def extract_frames(ffmpeg: str, video: Path, idxs: list[int], w: int, h: int) -> dict[int, np.ndarray]:
    """Pull exact frames by index at display size."""
    idxs = sorted(set(int(i) for i in idxs))
    if not idxs:
        return {}
    result: dict[int, np.ndarray] = {}
    chunk = 60
    for start in range(0, len(idxs), chunk):
        part = idxs[start:start + chunk]
        expr = "+".join(f"eq(n,{i})" for i in part)
        proc = run(
            [ffmpeg, "-hide_banner", "-nostats", "-loglevel", "error", "-i", str(video), "-an", "-sn",
             "-vf", f"select='{expr}',scale={w}:{h}:flags=lanczos,format=rgb24",
             "-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1"],
            capture_output=True,
        )
        raw = proc.stdout
        fsize = w * h * 3
        got = len(raw) // fsize
        arr = np.frombuffer(raw[: got * fsize], dtype=np.uint8).reshape(got, h, w, 3)
        for i, frame in zip(part, arr):
            result[i] = frame
    return result


def load_image(path: Path, w: int, h: int, notes: list[str]) -> np.ndarray:
    try:
        img = Image.open(path).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        die(f"could not read keyframe image {path}: {exc}")
    iw, ih = img.size
    target = w / h
    src = iw / ih
    if abs(src - target) / target > 0.02:
        warn(f"{path.name} is {iw}x{ih} (aspect {src:.3f}) but the video is {target:.3f}. "
             "Center-cropping it for comparison. In Frames mode the first keyframe sets the output shape.", notes)
        if src > target:
            nw = int(round(ih * target))
            x0 = (iw - nw) // 2
            img = img.crop((x0, 0, x0 + nw, ih))
        else:
            nh = int(round(iw / target))
            y0 = (ih - nh) // 2
            img = img.crop((0, y0, iw, y0 + nh))
    return np.asarray(img.resize((w, h), Image.BOX if (iw > w) else Image.BICUBIC), dtype=np.uint8)


# -------------------------------------------------------------- similarity

def features(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gray = cv2.GaussianBlur(gray, (0, 0), 1.0)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return gray, hist


def ssim(a: np.ndarray, b: np.ndarray) -> float:
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a = cv2.GaussianBlur(a, (11, 11), 1.5)
    mu_b = cv2.GaussianBlur(b, (11, 11), 1.5)
    aa = cv2.GaussianBlur(a * a, (11, 11), 1.5) - mu_a * mu_a
    bb = cv2.GaussianBlur(b * b, (11, 11), 1.5) - mu_b * mu_b
    ab = cv2.GaussianBlur(a * b, (11, 11), 1.5) - mu_a * mu_b
    num = (2 * mu_a * mu_b + c1) * (2 * ab + c2)
    den = (mu_a ** 2 + mu_b ** 2 + c1) * (aa + bb + c2)
    return float(np.mean(num / den))


def similarity(fa, fb) -> float:
    s = ssim(fa[0], fb[0])
    h = max(0.0, float(cv2.compareHist(fa[1], fb[1], cv2.HISTCMP_CORREL)))
    return 0.75 * s + 0.25 * h


def ncc(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).sum() / math.sqrt(float((a * a).sum() * (b * b).sum()) + 1e-6))


def frame_dist(fa, fb) -> float:
    """0 = identical, about 2+ = unrelated. (1 - NCC of grayscale) + (1 - colour histogram correlation)."""
    hc = max(0.0, float(cv2.compareHist(fa[1], fb[1], cv2.HISTCMP_CORREL)))
    return (1.0 - ncc(fa[0], fb[0])) + (1.0 - hc)


def detect_cuts(feats, pts, scene_list, scene_thresh, d_min=0.8, ratio_min=2.0, bridge_min=0.8, merge_s=0.5):
    """Hard cuts: a frame-to-frame jump that is (a) big, (b) a spike against the calmer side of its
    neighbourhood and (c) does not come back (frames two before and one after still differ), or an
    ffmpeg scene score at or over the threshold. Big jumps that fail (b) are listed as possible cuts
    (whip pans, flashes, morphs)."""
    n = len(feats)
    d = np.zeros(n)
    for i in range(1, n):
        d[i] = frame_dist(feats[i - 1], feats[i])
    scene_by_frame = np.zeros(n)
    if scene_list:
        t0 = scene_list[0][0]
        for t, s in scene_list:
            k = int(np.argmin(np.abs(pts - (t - t0))))
            scene_by_frame[k] = max(scene_by_frame[k], s)
    cands = []
    for i in range(1, n):
        if d[i] < d_min and scene_by_frame[i] < scene_thresh:
            continue
        before = d[max(1, i - 5):i]
        after = d[i + 1:i + 6]
        before = before[before > 0.005]  # ignore duplicated frames
        after = after[after > 0.005]
        lb = float(np.median(before)) if len(before) else 0.0
        la = float(np.median(after)) if len(after) else 0.0
        calm = min(x for x in (lb, la) if x > 0) if (lb > 0 or la > 0) else 0.0
        ratio = d[i] / max(calm, 0.05)
        bridge = frame_dist(feats[max(0, i - 2)], feats[min(n - 1, i + 1)])
        is_cut = scene_by_frame[i] >= scene_thresh or (ratio >= ratio_min and bridge >= bridge_min)
        if is_cut or bridge >= bridge_min:
            cands.append({"frame": i, "time_s": round(float(pts[i]), 3), "jump": round(float(d[i]), 3),
                          "spike_ratio": round(float(ratio), 2), "scene_score": round(float(scene_by_frame[i]), 3),
                          "cut": bool(is_cut)})
    # merge candidates closer than merge_s, keep the biggest jump
    groups: list[list[dict]] = []
    for c in cands:
        if groups and c["time_s"] - groups[-1][-1]["time_s"] <= merge_s:
            groups[-1].append(c)
        else:
            groups.append([c])
    cuts, possible = [], []
    for g in groups:
        is_cut = any(c["cut"] for c in g)
        pool = [c for c in g if c["cut"]] if is_cut else g
        best = max(pool, key=lambda c: c["jump"])
        best = {k: v for k, v in best.items() if k != "cut"}
        if len(g) > 1:
            best["span_s"] = [g[0]["time_s"], g[-1]["time_s"]]
        (cuts if is_cut else possible).append(best)
    return cuts, possible


# ------------------------------------------------------------------ drawing

def font(size: int):
    for name in ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def labelled(frame: np.ndarray, text: str, color=(255, 255, 255), bar=26) -> Image.Image:
    img = Image.fromarray(frame)
    w, h = img.size
    canvas = Image.new("RGB", (w, h + bar), (18, 18, 18))
    canvas.paste(img, (0, bar))
    ImageDraw.Draw(canvas).text((8, 4), text, fill=color, font=font(15))
    return canvas


def curve_panel(times, scores, planned, best_t, window, w, h, title, floor) -> Image.Image:
    img = Image.new("RGB", (w, h), (18, 18, 18))
    d = ImageDraw.Draw(img)
    pad_l, pad_r, pad_t, pad_b = 34, 10, 26, 22
    pw, ph = w - pad_l - pad_r, h - pad_t - pad_b
    t0, t1 = float(times[0]), float(times[-1]) if len(times) > 1 else float(times[0]) + 1
    if t1 <= t0:
        t1 = t0 + 1

    def X(t):
        return pad_l + (t - t0) / (t1 - t0) * pw

    def Y(s):
        return pad_t + (1 - max(0.0, min(1.0, s))) * ph

    d.text((8, 4), title, fill=(255, 255, 255), font=font(14))
    d.rectangle([pad_l, pad_t, pad_l + pw, pad_t + ph], outline=(70, 70, 70))
    if window:
        d.rectangle([X(max(t0, window[0])), pad_t, X(min(t1, window[1])), pad_t + ph], fill=(32, 40, 52))
    fy = Y(floor)
    d.line([pad_l, fy, pad_l + pw, fy], fill=(90, 60, 60))
    for s in (0.0, 0.5, 1.0):
        d.text((4, Y(s) - 7), f"{s:.1f}", fill=(140, 140, 140), font=font(11))
    pts = [(X(t), Y(s)) for t, s in zip(times, scores)]
    if len(pts) > 1:
        d.line(pts, fill=(120, 200, 255), width=2)
    d.line([X(planned), pad_t, X(planned), pad_t + ph], fill=(255, 210, 80), width=2)
    if best_t is not None:
        d.line([X(best_t), pad_t, X(best_t), pad_t + ph], fill=(120, 255, 140), width=2)
    d.text((pad_l, h - 18), f"{t0:.1f}s", fill=(140, 140, 140), font=font(11))
    d.text((pad_l + pw - 34, h - 18), f"{t1:.1f}s", fill=(140, 140, 140), font=font(11))
    d.text((pad_l + pw // 2 - 90, h - 18), "yellow = planned, green = best", fill=(160, 160, 160), font=font(11))
    return img


def grid(rows: list[list[Image.Image]], gap=6, bg=(0, 0, 0)) -> Image.Image:
    widths = [sum(im.width for im in r) + gap * (len(r) - 1) for r in rows]
    heights = [max(im.height for im in r) for r in rows]
    W, H = max(widths), sum(heights) + gap * (len(rows) - 1)
    out = Image.new("RGB", (W, H), bg)
    y = 0
    for r, rh in zip(rows, heights):
        x = 0
        for im in r:
            out.paste(im, (x, y))
            x += im.width + gap
        y += rh + gap
    return out


# --------------------------------------------------------------------- main

def resolve_keyframe(kdir: Path, kf: dict, i: int) -> Path:
    if kf.get("file"):
        p = Path(kf["file"])
        p = p if p.is_absolute() else kdir / p
        if p.exists():
            return p
        die(f"keyframe {i} file not found: {p}")
    for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
        p = kdir / f"kf{i}{ext}"
        if p.exists():
            return p
    die(f"keyframe {i} not found: expected {kdir / f'kf{i}.png'} (or .jpg), or set 'file' in plan.json")
    raise AssertionError


def main() -> None:
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Grade a generated clip against planned keyframes: planned-time frames, best-match "
                    "search, side-by-side images, cut detection. Suggests HIT / LATE / EARLY / MISS; "
                    "the human decides.",
    )
    ap.add_argument("--plan", required=True, type=Path, help="plan.json written in PLAN mode")
    ap.add_argument("--keyframes", required=True, type=Path,
                    help="folder with kf1.png, kf2.png ... (or the 'file' names in plan.json)")
    ap.add_argument("--video", required=True, type=Path, help="the downloaded attempt (mp4/mov)")
    ap.add_argument("--out", required=True, type=Path, help="output folder (created if missing)")
    ap.add_argument("--search", type=float, default=3.0, help="search +/- this many seconds around each planned time (default 3.0)")
    ap.add_argument("--step", type=float, default=0.25, help="resolution of the similarity curve stored in report.json, seconds (default 0.25). The search itself checks every frame.")
    ap.add_argument("--scene", type=float, default=0.3, help="ffmpeg scene score that always counts as a hard cut (default 0.3). A frame-difference spike test runs as well, because dark footage rarely reaches this score.")
    ap.add_argument("--hit-tol", type=float, default=1.0, help="|offset| up to this many seconds is a HIT (default 1.0)")
    ap.add_argument("--late-tol", type=float, default=3.0, help="|offset| up to this is LATE / EARLY, beyond is MISS (default 3.0)")
    ap.add_argument("--match-floor", type=float, default=0.55, help="best similarity below this suggests the content is wrong (default 0.55)")
    ap.add_argument("--panel-width", type=int, default=480, help="width of each image panel in pixels (default 480)")
    args = ap.parse_args()

    ffmpeg, ffprobe = need_tool("ffmpeg"), need_tool("ffprobe")
    for p, what in ((args.plan, "--plan"), (args.video, "--video")):
        if not p.is_file():
            die(f"{what} file not found: {p}")
    if not args.keyframes.is_dir():
        die(f"--keyframes folder not found: {args.keyframes}")
    if args.search <= 0 or args.step <= 0:
        die("--search and --step must be positive")

    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        die(f"could not read {args.plan} as JSON: {exc}")
    kfs = plan.get("keyframes")
    if not isinstance(kfs, list) or len(kfs) < 2:
        die("plan.json needs a 'keyframes' list with at least 2 entries")
    if len(kfs) > 10:
        die("plan.json has more than 10 keyframes; Frames mode takes up to 10")

    out = args.out
    (out / "pairs").mkdir(parents=True, exist_ok=True)
    notes: list[str] = []

    info = probe(ffprobe, args.video)
    aw = 160
    ah = even(aw * info["height"] / info["width"])
    frames, pts = decode_small(ffmpeg, args.video, aw, ah)
    n = len(frames)
    if len(pts) != n:
        fps = info["fps"]
        warn("could not read frame timestamps; assuming constant frame rate", notes)
        pts = np.arange(n) / fps
    pts = pts - pts[0]
    final_t = float(pts[-1])
    frame_dt = float(np.median(np.diff(pts))) if n > 1 else 1 / 24

    plan_dur = plan.get("duration_s")
    if isinstance(plan_dur, (int, float)) and abs(plan_dur - (final_t + frame_dt)) > 0.5:
        warn(f"plan duration is {plan_dur} s but the video runs {final_t + frame_dt:.2f} s. "
             "Check the Duration slider (it carries across tabs).", notes)

    feats = [features(f) for f in frames]
    dw = args.panel_width
    dh = even(dw * info["height"] / info["width"])

    points = dict(DEFAULT_POINTS)
    points.update({k.upper(): float(v) for k, v in ((plan.get("scoring") or {}).get("points") or {}).items()})

    results = []
    need_idx: set[int] = set()
    kf_imgs = []
    last = len(kfs)
    for i, kf in enumerate(kfs, start=1):
        path = resolve_keyframe(args.keyframes, kf, i)
        small = load_image(path, aw, ah, notes)
        kf_imgs.append(load_image(path, dw, dh, []))
        f_kf = features(small)
        curve = np.array([similarity(f_kf, f) for f in feats])

        if i == 1:
            planned = 0.0
            if float(kf.get("time_s", 0) or 0) != 0:
                warn("keyframe 1 is the start frame, so its time is 0 s regardless of the plan", notes)
        elif i == last:
            planned = final_t
            pt = kf.get("time_s")
            if isinstance(pt, (int, float)) and abs(pt - (final_t + frame_dt)) > 0.5 and abs(pt - final_t) > 0.5:
                warn(f"the last keyframe is pinned to the final frame ({final_t:.2f} s), not the planned {pt} s", notes)
        else:
            planned = float(kf.get("time_s", 0) or 0)
            if planned > final_t:
                warn(f"keyframe {i} is planned at {planned} s, after the clip ends ({final_t:.2f} s)", notes)

        p_idx = int(np.argmin(np.abs(pts - planned)))
        lo, hi = planned - args.search, planned + args.search
        win = np.where((pts >= lo - 1e-6) & (pts <= hi + 1e-6))[0]
        if len(win) == 0:
            win = np.array([p_idx])
        b_idx = int(win[np.argmax(curve[win])])
        best = float(curve[b_idx])
        # plateau: contiguous frames around the best that score almost as well
        eps = 0.015
        a = b = b_idx
        while a - 1 >= win[0] and curve[a - 1] >= best - eps:
            a -= 1
        while b + 1 <= win[-1] and curve[b + 1] >= best - eps:
            b += 1
        span = (float(pts[a]), float(pts[b]))
        offset = float(pts[b_idx] - planned)
        eff = 0.0 if span[0] - 1e-6 <= planned <= span[1] + 1e-6 else offset
        g_idx = int(np.argmax(curve))
        g_best = float(curve[g_idx])
        median = float(np.median(curve))
        prominence = best - median

        kf_notes = []
        if i == 1:
            label = "HIT"
            kf_notes.append("start frame: hits by construction")
            if float(curve[p_idx]) < args.match_floor:
                kf_notes.append(f"first output frame only scores {curve[p_idx]:.2f} against kf1: wrong upload order or wrong file?")
        else:
            if best < args.match_floor:
                label = "MISS"
                kf_notes.append(f"best similarity {best:.2f} is under the floor {args.match_floor}: content probably wrong")
            elif abs(eff) <= args.hit_tol:
                label = "HIT"
            elif abs(eff) <= args.late_tol:
                label = "LATE" if eff > 0 else "EARLY"
            else:
                label = "MISS"
                kf_notes.append(f"{eff:+.2f} s off: more than {args.late_tol} s")
            if g_best > best + 0.08 and g_best >= args.match_floor:
                kf_notes.append(f"a better match ({g_best:.2f}) sits at {pts[g_idx]:.2f} s, outside the search window")
                if label != "MISS":
                    label = "MISS"
            if span[1] - span[0] >= 1.0 and best >= args.match_floor:
                kf_notes.append(f"matches about equally from {span[0]:.2f} to {span[1]:.2f} s (slow motion or a hold)")
            if i == last and span[0] < planned - 1.0 and best >= args.match_floor:
                kf_notes.append("end state reached early and held: check for a freeze before the final frame")
        if prominence < 0.08:
            kf_notes.append("flat similarity curve: the match is ambiguous, judge by eye")

        step_t = np.arange(0.0, final_t + 1e-9, args.step)
        step_curve = [round(float(curve[int(np.argmin(np.abs(pts - t)))]), 4) for t in step_t]

        need_idx.update({p_idx, b_idx})
        results.append({
            "keyframe": i,
            "role": kf.get("role", ""),
            "file": str(path),
            "planned_s": round(planned, 3),
            "planned_frame": p_idx,
            "score_at_planned": round(float(curve[p_idx]), 4),
            "best_s": round(float(pts[b_idx]), 3),
            "best_frame": b_idx,
            "best_score": round(best, 4),
            "offset_s": round(offset, 3),
            "effective_offset_s": round(eff, 3),
            "match_span_s": [round(span[0], 3), round(span[1], 3)],
            "global_best_s": round(float(pts[g_idx]), 3),
            "global_best_score": round(g_best, 4),
            "prominence": round(prominence, 4),
            "suggested": label,
            "notes": kf_notes,
            "must_be_true": kf.get("must_be_true", []),
            "_curve": curve,
            "_window": (max(0.0, lo), min(final_t, hi)),
            "curve_step_s": args.step,
            "curve": step_curve,
        })

    # ---- cuts
    scores = scene_scores(ffmpeg, args.video)
    if not scores:
        warn("ffmpeg scene scores unavailable; using frame-difference cut detection only", notes)
    cuts, possible = detect_cuts(feats, pts, scores, args.scene)
    for c in cuts + possible:
        k = int(np.argmin(np.abs(pts - c["time_s"])))
        c["frame"] = k
        need_idx.update({max(0, k - 1), k})

    # timeline: 8 evenly spaced frames
    tl_idx = [int(np.argmin(np.abs(pts - t))) for t in np.linspace(0, final_t, 8)]
    need_idx.update(tl_idx)

    big = extract_frames(ffmpeg, args.video, sorted(need_idx), dw, dh)

    def frame_or_small(k):
        if k in big:
            return big[k]
        return cv2.resize(frames[k], (dw, dh), interpolation=cv2.INTER_LINEAR)

    color = {"HIT": (120, 255, 140), "LATE": (255, 200, 80), "EARLY": (255, 200, 80), "MISS": (255, 100, 100)}
    overview_rows = []
    cw = dw * 2 // 3
    ch = even(cw * dh / dw)
    for r, kimg in zip(results, kf_imgs):
        i = r["keyframe"]
        plan_p = labelled(kimg, f"PLAN kf{i} {r['role']} @ {r['planned_s']:.2f}s")
        at_p = labelled(frame_or_small(r["planned_frame"]),
                        f"OUTPUT @ {r['planned_s']:.2f}s  sim {r['score_at_planned']:.2f}")
        best_p = labelled(frame_or_small(r["best_frame"]),
                          f"BEST @ {r['best_s']:.2f}s ({r['effective_offset_s']:+.2f}s) sim {r['best_score']:.2f}",
                          color=color[r["suggested"]])
        curve = curve_panel(pts, r["_curve"], r["planned_s"], r["best_s"], r["_window"], dw, dh + 26,
                            f"kf{i} similarity over the clip, suggested: {r['suggested']}", args.match_floor)
        pair = grid([[plan_p, at_p], [best_p, curve]])
        ppath = out / "pairs" / f"kf{i}_pair.png"
        pair.save(ppath, optimize=True)
        r["pair_image"] = str(ppath)
        small_row = [im.resize((cw, int(im.height * cw / im.width))) for im in (plan_p, at_p, best_p, curve)]
        overview_rows.append(small_row)

    tw = dw // 2
    th = even(tw * dh / dw)
    cut_ts = [c["time_s"] for c in cuts]
    tl_row = []
    for k in tl_idx:
        im = labelled(cv2.resize(frame_or_small(k), (tw, th)), f"{pts[k]:.1f}s")
        tl_row.append(im)
    overview_rows.append(tl_row)
    for c in (cuts + possible)[:6]:
        k = c["frame"]
        kind = "CUT" if c in cuts else "possible cut"
        before = labelled(cv2.resize(frame_or_small(max(0, k - 1)), (tw, th)), f"before {pts[max(0, k - 1)]:.2f}s")
        after = labelled(cv2.resize(frame_or_small(k), (tw, th)),
                         f"{kind} {c['time_s']:.2f}s (jump {c['jump']:.2f})", color=(255, 120, 120))
        overview_rows.append([before, after])
    overview = grid(overview_rows)
    overview.save(out / "overview.png", optimize=True)

    # ---- score
    mid = results[1:]
    pts_total = sum(points.get(r["suggested"], 0.0) for r in mid) + (1.0 if not cuts else 0.0)
    max_total = len(mid) + 1

    for r in results:
        r.pop("_curve", None)
        r.pop("_window", None)

    report = {
        "tool": "shot-director grade.py",
        "video": str(args.video),
        "plan": str(args.plan),
        "video_info": {**info, "frames": n, "final_frame_s": round(final_t, 3)},
        "settings": {"search_s": args.search, "step_s": args.step, "scene": args.scene,
                     "hit_tol_s": args.hit_tol, "late_tol_s": args.late_tol, "match_floor": args.match_floor},
        "keyframes": results,
        "cuts": cuts,
        "possible_cuts": possible,
        "suggested_score": {"points": round(pts_total, 2), "out_of": max_total,
                            "rule": "keyframes 2..N: HIT 1, LATE/EARLY 0.5, MISS 0 (overridable in plan.json scoring.points); +1 if no cuts. Keyframe 1 is the start frame and is not scored."},
        "warnings": notes,
        "overview_image": str(out / "overview.png"),
        "note": "Labels are suggestions from pixel similarity. Look at the pair images; the human's call is final.",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [f"# Grade: {args.video.name}", ""]
    md.append(f"Plan: `{args.plan.name}`. Clip: {info['width']}x{info['height']}, {n} frames, "
              f"final frame at {final_t:.2f} s. Search +/- {args.search} s.")
    md.append("")
    md.append("| KF | Role | Planned | Sim at planned | Best match | Offset | Suggested | Final (human) | Notes |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        md.append(f"| {r['keyframe']} | {r['role']} | {r['planned_s']:.2f} s | {r['score_at_planned']:.2f} | "
                  f"{r['best_s']:.2f} s ({r['best_score']:.2f}) | {r['effective_offset_s']:+.2f} s | "
                  f"{r['suggested']} |  | {'; '.join(r['notes'])} |")
    md.append("")
    if cuts:
        md.append(f"Cuts ({len(cuts)}): " + ", ".join(f"{c['time_s']:.2f} s (jump {c['jump']:.2f}, scene {c['scene_score']:.2f})" for c in cuts))
    else:
        md.append("Cuts: none found.")
    if possible:
        md.append("")
        md.append("Possible cuts or fast changes, check by eye: " + ", ".join(
            (f"{c['span_s'][0]:.2f} to {c['span_s'][1]:.2f} s" if "span_s" in c else f"{c['time_s']:.2f} s") + f" (jump {c['jump']:.2f})"
            for c in possible))
    md.append("")
    md.append(f"Suggested score: **{pts_total:g} / {max_total}** (keyframes 2 to {len(results)} plus 1 for no cuts).")
    if notes:
        md.append("")
        md.append("Warnings:")
        md.extend(f"- {w}" for w in notes)
    md.append("")
    md.append("Images: `overview.png`, `pairs/kf<N>_pair.png`. Labels are suggestions; the human's call is final.")
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n".join(md))
    print(f"\nWrote {out / 'report.md'}")


if __name__ == "__main__":
    main()

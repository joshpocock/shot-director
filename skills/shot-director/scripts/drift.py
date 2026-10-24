#!/usr/bin/env python3
"""
drift.py: what changed between a source clip and its edited version?

Use it after an edit pass (for example "make the speaker matte black, keep
everything else") to see whether the change stayed inside the object you
asked about or leaked into the rest of the frame.

Both clips are resampled to the same size and frame rate, aligned by frame
index, blurred, differenced in luminance and chroma, thresholded and cleaned
up. Outputs a heatmap, worst-frame triptychs, a short diff MP4 and per-frame
numbers.

A generated re-render shifts every pixel slightly, even where nothing was
supposed to change. Blur and threshold remove most of that noise, so treat the
numbers as a guide that points your eyes, not as proof.

Requirements: Python 3.10+, numpy, pillow, opencv-python, ffmpeg and ffprobe on PATH.
No network access.

Example:
  python drift.py --source keeper.mp4 --edited keeper-black.mp4 --out drift-1 --focus-hint "speaker"
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import numpy as np
    import cv2
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        f"drift.py: error: missing Python package ({exc.name}). "
        "Install with: pip install numpy pillow opencv-python\n"
    )
    sys.exit(2)

PROG = "drift.py"


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


def even(x: float) -> int:
    return max(2, int(round(x / 2.0)) * 2)


def probe(ffprobe: str, video: Path) -> dict:
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,avg_frame_rate:format=duration", "-of", "json", str(video)],
            check=True, capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        die(f"ffprobe could not read {video}: {exc.stderr.decode('utf-8', 'replace')[-500:]}")
    data = json.loads(out.decode("utf-8", "replace") or "{}")
    streams = data.get("streams") or []
    if not streams:
        die(f"no video stream found in {video}")
    s = streams[0]
    return {"width": int(s["width"]), "height": int(s["height"]),
            "duration": float((data.get("format") or {}).get("duration") or 0)}


def decode(ffmpeg: str, video: Path, fps: float, w: int, h: int, start: float | None, end: float | None) -> np.ndarray:
    cmd = [ffmpeg, "-hide_banner", "-nostats", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += ["-i", str(video), "-an", "-sn",
            "-vf", f"fps={fps},scale={w}:{h}:flags=area,format=rgb24", "-f", "rawvideo", "pipe:1"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        die(f"ffmpeg could not decode {video}:\n{proc.stderr.decode('utf-8', 'replace')[-1500:]}")
    fsize = w * h * 3
    n = len(proc.stdout) // fsize
    if n == 0:
        die(f"no frames decoded from {video} (check --start / --end)")
    return np.frombuffer(proc.stdout[: n * fsize], dtype=np.uint8).reshape(n, h, w, 3)


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


def labelled(arr: np.ndarray, text: str, bar: int = 24) -> Image.Image:
    img = Image.fromarray(arr)
    lines = text.split(chr(10))
    bar = max(bar, 6 + 18 * len(lines))
    out = Image.new("RGB", (img.width, img.height + bar), (18, 18, 18))
    out.paste(img, (0, bar))
    d = ImageDraw.Draw(out)
    for j, line in enumerate(lines):
        d.text((8, 4 + 18 * j), line, fill=(255, 255, 255), font=font(14))
    return out


def hstack(imgs: list[Image.Image], gap: int = 6) -> Image.Image:
    W = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    H = max(i.height for i in imgs)
    out = Image.new("RGB", (W, H), (0, 0, 0))
    x = 0
    for i in imgs:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def overlay_mask(src: np.ndarray, mask: np.ndarray, box=None, expect=None) -> np.ndarray:
    gray = cv2.cvtColor(cv2.cvtColor(src, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    out = (gray * 0.55).astype(np.uint8)
    out[mask > 0] = (255, 60, 60)
    if expect is not None:
        x, y, w, h = expect
        cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), (80, 170, 255), 1)
    if box is not None:
        x, y, w, h = box
        cv2.rectangle(out, (x, y), (x + w - 1, y + h - 1), (90, 255, 120), 2)
    return out


def region_words(cx: float, cy: float) -> str:
    col = "left" if cx < 1 / 3 else ("right" if cx > 2 / 3 else "centre")
    row = "top" if cy < 1 / 3 else ("bottom" if cy > 2 / 3 else "middle")
    return "centre" if (col == "centre" and row == "middle") else f"{row} {col}"


def parse_box(txt: str, w: int, h: int, src_w: int, src_h: int) -> tuple[int, int, int, int]:
    try:
        vals = [float(v) for v in txt.split(",")]
    except ValueError:
        die("--expect-box must be x,y,w,h")
    if len(vals) != 4:
        die("--expect-box must be x,y,w,h")
    if all(0 <= v <= 1 for v in vals):  # fractions of the frame
        x, y, bw, bh = vals[0] * w, vals[1] * h, vals[2] * w, vals[3] * h
    else:  # pixels of the source video
        sx, sy = w / src_w, h / src_h
        x, y, bw, bh = vals[0] * sx, vals[1] * sy, vals[2] * sx, vals[3] * sy
    x, y = max(0, int(round(x))), max(0, int(round(y)))
    bw, bh = max(1, int(round(bw))), max(1, int(round(bh)))
    return x, y, min(bw, w - x), min(bh, h - y)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Compare a source clip with its edited version and show what changed, including "
                    "changes you did not ask for. Numbers are a guide, not proof: re-renders shift every pixel a little.",
    )
    ap.add_argument("--source", required=True, type=Path, help="the clip before the edit")
    ap.add_argument("--edited", required=True, type=Path, help="the clip after the edit")
    ap.add_argument("--out", required=True, type=Path, help="output folder (created if missing)")
    ap.add_argument("--fps", type=float, default=6.0, help="frames per second to compare (default 6)")
    ap.add_argument("--width", type=int, default=480, help="analysis width in pixels (default 480)")
    ap.add_argument("--blur", type=int, default=7, help="Gaussian blur kernel before differencing, odd, 0 = off (default 7)")
    ap.add_argument("--thresh", type=float, default=25.0, help="difference (0 to 255) that counts as changed (default 25)")
    ap.add_argument("--chroma-gain", type=float, default=2.0, help="weight on colour (Cr/Cb) differences vs brightness (default 2.0)")
    ap.add_argument("--focus-hint", default="", help='what the edit was meant to change, e.g. "speaker" (used in the report)')
    ap.add_argument("--expect-box", default="", help="optional x,y,w,h of where the change should be, as fractions (0 to 1) or source pixels; reports the share of changes inside it")
    ap.add_argument("--start", type=float, default=None, help="compare from this time (seconds) in both clips")
    ap.add_argument("--end", type=float, default=None, help="compare up to this time (seconds) in both clips")
    ap.add_argument("--worst", type=int, default=3, help="how many worst frames to save (default 3)")
    args = ap.parse_args()

    ffmpeg, ffprobe = need_tool("ffmpeg"), need_tool("ffprobe")
    for p, what in ((args.source, "--source"), (args.edited, "--edited")):
        if not p.is_file():
            die(f"{what} file not found: {p}")
    if args.fps <= 0 or args.width < 64:
        die("--fps must be positive and --width at least 64")
    blur = int(args.blur)
    if blur and blur % 2 == 0:
        blur += 1

    notes: list[str] = []
    out = args.out
    (out / "worst").mkdir(parents=True, exist_ok=True)

    si, ei = probe(ffprobe, args.source), probe(ffprobe, args.edited)
    w = even(args.width)
    h = even(w * si["height"] / si["width"])
    if abs(si["width"] / si["height"] - ei["width"] / ei["height"]) > 0.02:
        warn(f"aspect ratios differ (source {si['width']}x{si['height']}, edited {ei['width']}x{ei['height']}); "
             "the edited clip is stretched to the source shape, so expect edge differences", notes)
    if abs(si["duration"] - ei["duration"]) > 0.25:
        warn(f"durations differ (source {si['duration']:.2f} s, edited {ei['duration']:.2f} s). Frames are aligned "
             "by index from the start; if the edit was retimed or trimmed, later frames will not line up", notes)

    src = decode(ffmpeg, args.source, args.fps, w, h, args.start, args.end)
    edt = decode(ffmpeg, args.edited, args.fps, w, h, args.start, args.end)
    n = min(len(src), len(edt))
    if abs(len(src) - len(edt)) > 1:
        warn(f"frame counts differ after resampling ({len(src)} vs {len(edt)}); comparing the first {n}", notes)
    src, edt = src[:n], edt[:n]
    t0 = args.start or 0.0

    expect = parse_box(args.expect_box, w, h, si["width"], si["height"]) if args.expect_box else None
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    grp = max(5, (w // 40) | 1)
    k_group = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grp, grp))
    area = float(w * h)

    freq = np.zeros((h, w), np.float32)
    mag_sum = np.zeros((h, w), np.float32)
    outside_sum = np.zeros((h, w), np.float32)
    rows = []
    masks = []
    boxes = []
    grid_counts = np.zeros((3, 3), np.float64)
    total_main = 0
    for i in range(n):
        ys = cv2.cvtColor(src[i], cv2.COLOR_RGB2YCrCb).astype(np.float32)
        ye = cv2.cvtColor(edt[i], cv2.COLOR_RGB2YCrCb).astype(np.float32)
        if blur:
            ys = cv2.GaussianBlur(ys, (blur, blur), 0)
            ye = cv2.GaussianBlur(ye, (blur, blur), 0)
        d = np.abs(ys - ye)
        mag = np.maximum(d[..., 0], args.chroma_gain * np.maximum(d[..., 1], d[..., 2]))
        mask = (mag > args.thresh).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k_open)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close)
        changed = int(mask.sum())

        main_px, box = 0, None
        main_mask = np.zeros_like(mask)
        if changed:
            grouped = cv2.dilate(mask, k_group)
            nlab, labels, stats, _ = cv2.connectedComponentsWithStats(grouped, connectivity=8)
            counts = np.bincount(labels[mask > 0].ravel(), minlength=nlab)
            counts[0] = 0
            best = int(np.argmax(counts))
            main_px = int(counts[best])
            main_mask = ((labels == best) & (mask > 0)).astype(np.uint8)
            ys_, xs_ = np.nonzero(main_mask)
            box = (int(xs_.min()), int(ys_.min()), int(xs_.max() - xs_.min() + 1), int(ys_.max() - ys_.min() + 1))
        total_main += main_px
        outside = mask & (1 - main_mask)
        outside_sum += outside
        if outside.any():
            oy, ox = np.nonzero(outside)
            np.add.at(grid_counts, (np.minimum(oy * 3 // h, 2), np.minimum(ox * 3 // w, 2)), 1)

        unchanged = mask == 0
        raw_s = cv2.cvtColor(src[i], cv2.COLOR_RGB2YCrCb).astype(np.float32)
        raw_e = cv2.cvtColor(edt[i], cv2.COLOR_RGB2YCrCb).astype(np.float32)
        if unchanged.any():
            dy_bg = float(np.mean(raw_e[..., 0][unchanged] - raw_s[..., 0][unchanged]))
            dc_bg = float(np.mean(np.abs(raw_e[..., 1:][unchanged] - raw_s[..., 1:][unchanged])))
        else:
            dy_bg = dc_bg = 0.0

        row = {
            "frame": i,
            "time_s": round(t0 + i / args.fps, 3),
            "changed_pct": round(100 * changed / area, 3),
            "main_region_share": round(main_px / changed, 4) if changed else None,
            "outside_main_pct": round(100 * (changed - main_px) / area, 3),
            "main_box_xywh": list(box) if box else None,
            "bg_luma_shift": round(dy_bg, 2),
            "bg_chroma_shift": round(dc_bg, 2),
        }
        if expect is not None:
            x, y, bw, bh = expect
            inside = int(mask[y:y + bh, x:x + bw].sum())
            row["inside_expect_share"] = round(inside / changed, 4) if changed else None
        rows.append(row)
        masks.append(mask)
        boxes.append(box)
        freq += mask
        mag_sum += mag

    freq /= max(1, n)
    changed = np.array([r["changed_pct"] for r in rows])
    outside_pct = np.array([r["outside_main_pct"] for r in rows])
    total_changed = sum(int(m.sum()) for m in masks)
    main_share_all = total_main / total_changed if total_changed else None

    # ---- heatmap
    base = np.median(src[:: max(1, n // 15)], axis=0).astype(np.uint8)
    heat = cv2.applyColorMap((np.clip(freq, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(cv2.cvtColor(base, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    alpha = np.clip(freq * 3, 0, 0.85)[..., None]
    blend = (gray * (1 - alpha) * 0.7 + heat * alpha).astype(np.uint8)
    big = cv2.resize(blend, (w * 2, h * 2), interpolation=cv2.INTER_LINEAR)

    def rect(img, box, color, thick=2):
        x, y, bw, bh = (2 * v for v in box)
        cv2.rectangle(img, (x, y), (x + bw - 1, y + bh - 1), color, thick)

    # hotspots: pixels that changed in at least 25% of frames, grouped
    hot = (freq >= 0.25).astype(np.uint8)
    hot_box = None
    other_hot = []
    if hot.any():
        nlab, labels, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(hot, k_group), connectivity=8)
        if nlab > 1:
            sizes = np.bincount(labels[hot > 0].ravel(), minlength=nlab)
            sizes[0] = 0
            b = int(np.argmax(sizes))
            hot_box = tuple(int(v) for v in stats[b, :4])
            for lab in np.argsort(-sizes):
                lab = int(lab)
                if lab in (0, b) or sizes[lab] < 0.001 * area:
                    continue
                x, y, bw, bh = (int(v) for v in stats[lab, :4])
                other_hot.append({"box_xywh": [x, y, bw, bh],
                                  "area": region_words((x + bw / 2) / w, (y + bh / 2) / h),
                                  "frame_pct": round(100 * float(sizes[lab]) / area, 3)})
            other_hot = other_hot[:8]
    if expect is not None:
        rect(big, expect, (80, 170, 255), 1)
    for o in other_hot:
        rect(big, o["box_xywh"], (255, 150, 40))
    if hot_box:
        rect(big, hot_box, (90, 255, 120))
    legend = "Share of frames where each pixel changed: dark = never, yellow = every frame."
    keys = []
    if hot_box:
        keys.append("green = main hotspot")
    if other_hot:
        keys.append("orange = other hotspots")
    if expect:
        keys.append("blue = expected edit area")
    if keys:
        legend += chr(10) + "Boxes: " + ", ".join(keys) + "."
    heat_img = labelled(big, legend)
    heat_img.save(out / "heatmap.png", optimize=True)

    # ---- worst frames (at least 1 s apart)
    order = list(np.argsort(-changed))
    picked: list[int] = []
    for k in order:
        if all(abs(int(k) - p) >= args.fps for p in picked):
            picked.append(int(k))
        if len(picked) >= args.worst:
            break
    worst_files = []
    for k in sorted(picked):
        r = rows[k]
        share = "" if r["main_region_share"] is None else f", main region {100 * r['main_region_share']:.0f}%"
        trip = hstack([
            labelled(src[k], f"SOURCE {r['time_s']:.2f}s"),
            labelled(edt[k], "EDITED"),
            labelled(overlay_mask(src[k], masks[k], boxes[k], expect), f"CHANGED {r['changed_pct']:.1f}%{share}"),
        ])
        p = out / "worst" / f"worst_{r['time_s']:06.2f}s.png"
        trip.save(p, optimize=True)
        worst_files.append(str(p))

    # ---- diff mp4
    vw = min(w, 360)
    vh = even(vw * h / w)
    gap = 4
    fw = vw * 3 + gap * 2
    fw += fw % 2
    mp4 = out / "diff.mp4"
    enc = subprocess.Popen(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{fw}x{vh}", "-r", f"{args.fps}", "-i", "pipe:0", "-c:v", "libx264", "-crf", "28",
         "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        for i in range(n):
            frame = np.zeros((vh, fw, 3), np.uint8)
            panels = [src[i], edt[i], overlay_mask(src[i], masks[i], boxes[i], expect)]
            for j, pnl in enumerate(panels):
                x = j * (vw + gap)
                frame[:, x:x + vw] = cv2.resize(pnl, (vw, vh), interpolation=cv2.INTER_AREA)
            enc.stdin.write(frame.tobytes())
        enc.stdin.close()
        enc.wait()
    except BrokenPipeError:
        enc.wait()
    if enc.returncode != 0:
        warn("ffmpeg could not write diff.mp4: " + enc.stderr.read().decode("utf-8", "replace")[-300:], notes)

    # ---- where did the unwanted changes land
    grid_share = grid_counts / grid_counts.sum() if grid_counts.sum() else grid_counts
    names = [["top left", "top centre", "top right"], ["middle left", "centre", "middle right"],
             ["bottom left", "bottom centre", "bottom right"]]
    outside_where = sorted(
        ({"area": names[r][c], "share": round(float(grid_share[r, c]), 3)} for r in range(3) for c in range(3)),
        key=lambda d: -d["share"])
    main_where = None
    if hot_box:
        x, y, bw, bh = hot_box
        main_where = region_words((x + bw / 2) / w, (y + bh / 2) / h)

    bg_luma = float(np.mean([r["bg_luma_shift"] for r in rows]))
    bg_chroma = float(np.mean([r["bg_chroma_shift"] for r in rows]))
    summary = {
        "frames_compared": n,
        "fps": args.fps,
        "analysis_size": [w, h],
        "changed_pct_mean": round(float(changed.mean()), 3),
        "changed_pct_median": round(float(np.median(changed)), 3),
        "changed_pct_max": round(float(changed.max()), 3),
        "main_region_share_overall": round(main_share_all, 4) if main_share_all is not None else None,
        "outside_main_pct_mean": round(float(outside_pct.mean()), 3),
        "outside_main_pct_max": round(float(outside_pct.max()), 3),
        "main_hotspot_box_xywh": list(hot_box) if hot_box else None,
        "main_hotspot_area": main_where,
        "other_hotspots": other_hot,
        "outside_changes_by_area": outside_where,
        "bg_luma_shift_mean": round(bg_luma, 2),
        "bg_chroma_shift_mean": round(bg_chroma, 2),
    }
    if expect is not None:
        ins = [r["inside_expect_share"] for r in rows if r.get("inside_expect_share") is not None]
        x, y, bw, bh = expect
        tot_in = sum(int(m[y:y + bh, x:x + bw].sum()) for m in masks)
        summary["expect_box_xywh"] = list(expect)
        summary["inside_expect_share_overall"] = round(tot_in / total_changed, 4) if total_changed else None
        summary["inside_expect_share_median_frame"] = round(float(np.median(ins)), 4) if ins else None

    report = {
        "tool": "shot-director drift.py",
        "source": str(args.source),
        "edited": str(args.edited),
        "focus_hint": args.focus_hint,
        "settings": {"fps": args.fps, "width": w, "blur": blur, "thresh": args.thresh,
                     "chroma_gain": args.chroma_gain, "start": args.start, "end": args.end},
        "summary": summary,
        "frames": rows,
        "images": {"heatmap": str(out / "heatmap.png"), "worst": worst_files, "diff_mp4": str(mp4)},
        "warnings": notes,
        "note": "Generated re-renders shift every pixel slightly. Blur and threshold remove most of that; "
                "the numbers point your eyes, they are not proof.",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    hint = f" (the edit targets: {args.focus_hint})" if args.focus_hint else ""
    md = [f"# Drift: {args.source.name} vs {args.edited.name}", ""]
    md.append(f"Compared {n} frames at {args.fps:g} fps, {w}x{h}, blur {blur}, threshold {args.thresh:g}.")
    md.append("")
    md.append(f"- Changed pixels per frame: mean **{summary['changed_pct_mean']:.2f}%**, median "
              f"{summary['changed_pct_median']:.2f}%, max {summary['changed_pct_max']:.2f}%.")
    if main_share_all is not None:
        md.append(f"- Main changed region{hint}: holds **{100 * main_share_all:.0f}%** of all changed pixels"
                  + (f", hotspot in the {main_where} of frame" if main_where else "") + ".")
        md.append(f"- Changes outside the main region: mean **{summary['outside_main_pct_mean']:.2f}%** of the frame, "
                  f"max {summary['outside_main_pct_max']:.2f}%. Most of it in: "
                  + ", ".join(f"{d['area']} ({100 * d['share']:.0f}%)" for d in outside_where[:3] if d["share"] > 0)
                  + ("" if any(d["share"] > 0 for d in outside_where) else "nowhere") + ".")
    else:
        md.append("- No changed pixels above the threshold in any frame.")
    if other_hot:
        md.append("- Other hotspots (changed in 25%+ of frames, outside the main one): "
                  + ", ".join(f"{o['area']} ({o['frame_pct']:.2f}% of frame)" for o in other_hot)
                  + ". Look there first.")
    md.append(f"- Brightness shift in unchanged areas: {bg_luma:+.2f} (0 to 255 scale); colour shift {bg_chroma:.2f}. "
              "Above about 3 means the overall grade moved.")
    if expect is not None:
        val = summary.get("inside_expect_share_overall")
        md.append(f"- Inside the expected box: {100 * val:.0f}% of changed pixels." if val is not None else
                  "- Inside the expected box: no changes found.")
    md.append("")
    md.append("Worst frames: " + ", ".join(f"`{Path(p).name}`" for p in worst_files))
    md.append("")
    md.append("How to read it: a clean edit shows one hot region on the object you asked about, a high main-region "
              "share and almost nothing outside it. Changes outside the main region are the drift to check by eye "
              "in `worst/` and `diff.mp4`. A re-render nudges every pixel, so small scattered specks are normal; "
              "the numbers point your eyes, they are not proof.")
    if notes:
        md.append("")
        md.append("Warnings:")
        md.extend(f"- {x}" for x in notes)
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nWrote {out / 'report.md'}")


if __name__ == "__main__":
    main()

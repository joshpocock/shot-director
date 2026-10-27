#!/usr/bin/env python3
"""
scene_grade.py: grade a multi-shot dialogue scene against the scene.json you planned.

Four marks, the same four every time:
  SHOTS  the cuts happen where the scene says (detected with the ffmpeg scene score)
  LINES  every planned line is spoken, in its shot (transcribed, fuzzy matched)
  SYNC   lips match the words (a script cannot judge this: it exports a frame
         strip per line so Claude and you can look)
  SAME   faces and products stay the same across cuts (a labelled grid of one
         frame per shot under the reference images, for your eyes)

SHOTS and LINES get a suggested verdict. SYNC and SAME are NEEDS-EYES until
Claude or you fill them in with --fill. The script only suggests. The human's
call is final.

Requirements: Python 3.10+, numpy, pillow, opencv-python, ffmpeg and ffprobe on PATH.
Transcription: faster-whisper (pip install faster-whisper, runs locally on the CPU),
or bring your own transcript with --transcript. No network access is needed
once the faster-whisper model is downloaded (the first run downloads it).

Examples:
  python scene_grade.py --scene scene.json --video take-1.mp4 --refs refs --out grade-1
  python scene_grade.py --scene scene.json --video take-1.mp4 --transcript my-stt.json --out grade-1
  python scene_grade.py --check scene.json
  python scene_grade.py --fill grade-1 --mark SYNC=HALF --mark SAME=HIT --by claude --why "shot 6 mouth lags"

Transcript format for --transcript (any of these, times in seconds):
  [{"start": 3.4, "end": 4.9, "text": "Do not tell her about Friday"}, ...]      word or segment level
  {"segments": [{"start": .., "end": .., "text": "..", "words": [{"start", "end", "text" or "word"}]}]}
  {"words": [{"start", "end", "text" or "word"}, ...]}
Word-level is better; segment-level text is spread evenly over the segment.
"""
from __future__ import annotations

import argparse
import difflib
import json
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
        f"scene_grade.py: error: missing Python package ({exc.name}). "
        "Install with: pip install numpy pillow opencv-python\n"
    )
    sys.exit(2)

PROG = "scene_grade.py"
MARKS = ("SHOTS", "LINES", "SYNC", "SAME")
VERDICTS = ("HIT", "HALF", "MISS", "NEEDS-EYES")
POINTS = {"HIT": 1.0, "HALF": 0.5, "MISS": 0.0}
KLING_MIN_S, KLING_MAX_S = 3.0, 30.0


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
        [ffprobe, "-v", "error", "-show_entries",
         "stream=codec_type,width,height,avg_frame_rate,r_frame_rate:format=duration",
         "-of", "json", str(video)],
        capture_output=True,
    ).stdout
    data = json.loads(out.decode("utf-8", "replace") or "{}")
    streams = data.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not v:
        die(f"no video stream found in {video}")

    def rate(txt: str | None) -> float:
        if not txt or txt in ("0/0", "0"):
            return 0.0
        if "/" in txt:
            a, b = txt.split("/", 1)
            return float(a) / float(b) if float(b) else 0.0
        return float(txt)

    fps = rate(v.get("avg_frame_rate")) or rate(v.get("r_frame_rate")) or 24.0
    dur = float((data.get("format") or {}).get("duration") or 0)
    return {"width": int(v["width"]), "height": int(v["height"]), "fps": fps, "duration": dur,
            "has_audio": any(s.get("codec_type") == "audio" for s in streams)}


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
    """ffmpeg scene-change score per frame: list of (pts_time, score). Thresholding these is the
    same as ffmpeg's select='gt(scene,T)', with the scores kept so near misses can be reported."""
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
        die(f"ffmpeg scene detection failed on {video}:\n{log[-1500:]}")
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
    """Pull exact frames by index at w x h."""
    idxs = sorted(set(int(i) for i in idxs))
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


# ------------------------------------------------------------- scene file

def shot_lines(shot: dict) -> list[dict]:
    """A shot normally has one 'speaker' and one 'line'. A 'lines' list is accepted so a plan that
    broke the one-speaker rule can still be graded (the check flags it)."""
    out = []
    if isinstance(shot.get("lines"), list):
        for ln in shot["lines"]:
            if isinstance(ln, dict) and (ln.get("text") or ln.get("line")):
                out.append({"speaker": ln.get("speaker"), "text": ln.get("text") or ln.get("line"),
                            "delivery": ln.get("delivery", ""), "voiceover": bool(ln.get("voiceover", False))})
    elif shot.get("line"):
        out.append({"speaker": shot.get("speaker"), "text": shot["line"],
                    "delivery": shot.get("delivery", ""), "voiceover": bool(shot.get("voiceover", False))})
    return out


def load_scene(path: Path) -> dict:
    try:
        scene = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        die(f"could not read {path} as JSON: {exc}")
    shots = scene.get("shots")
    if not isinstance(shots, list) or not shots:
        die("scene.json needs a 'shots' list")
    for i, s in enumerate(shots, start=1):
        if not isinstance(s.get("start_s"), (int, float)) or not isinstance(s.get("end_s"), (int, float)):
            die(f"shot {i} needs numeric start_s and end_s")
        s.setdefault("id", i)
    return scene


def count_words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if re.search(r"\w", w)])


def check_scene(scene: dict) -> list[str]:
    """Plan rules from references/kling4-higgsfield-rules.md. Returns findings, worst first."""
    out: list[str] = []
    shots = scene["shots"]
    dur = scene.get("duration_s")
    if not isinstance(dur, (int, float)):
        out.append("duration_s is missing")
        dur = shots[-1]["end_s"]
    if not (KLING_MIN_S <= dur <= KLING_MAX_S):
        out.append(f"duration {dur} s is outside Kling 4.0's 3 to 30 s")
    if scene.get("aspect") not in ("16:9", "9:16", "1:1"):
        out.append(f"aspect '{scene.get('aspect')}' is not 16:9, 9:16 or 1:1")
    if shots[0]["start_s"] != 0:
        out.append("shot 1 should start at 0 s")
    if abs(shots[-1]["end_s"] - dur) > 0.01:
        out.append(f"last shot ends at {shots[-1]['end_s']} s but duration is {dur} s")
    mode = str(scene.get("mode", "")).lower()
    if mode == "references" and (scene.get("start_frame") or scene.get("end_frame") or scene.get("keyframes")):
        out.append("References and Frames cannot be combined in one task: drop the start/end frames or switch mode")
    ref_ids = {str(r.get("id")) for r in scene.get("references") or [] if r.get("id")}
    for i, s in enumerate(shots, start=1):
        if i > 1 and abs(s["start_s"] - shots[i - 2]["end_s"]) > 0.01:
            out.append(f"shot {i} starts at {s['start_s']} s but shot {i - 1} ends at {shots[i - 2]['end_s']} s")
        length = s["end_s"] - s["start_s"]
        if length <= 0:
            out.append(f"shot {i} has no length")
            continue
        lines = shot_lines(s)
        speakers = {ln["speaker"] for ln in lines}
        if len(lines) > 1:
            out.append(f"shot {i} has {len(lines)} lines ({', '.join(str(x) for x in speakers)}): one speaker and one "
                       "line per shot. Two speakers in one shot collided and garbled a line in testing; split the shot")
        for ln in lines:
            n = count_words(ln["text"])
            if n / length > 3.2:
                out.append(f"shot {i}: {n} words in {length:g} s is faster than natural speech; lengthen the shot or cut words")
            elif length > n / 2.5 + 3.0 and i != len(shots):
                out.append(f"shot {i}: {length:g} s for a {n}-word line leaves a long silence; size the shot to the line "
                           "(3 to 6 words -> 3 to 4 s)")
            if ref_ids and ln["speaker"] and not ln["voiceover"] and str(ln["speaker"]) not in ref_ids:
                out.append(f"shot {i}: speaker '{ln['speaker']}' has no reference image id")
            if not ln["delivery"]:
                out.append(f"shot {i}: no delivery note for the line (say how it is said)")
        if not lines and length > 4.0:
            out.append(f"shot {i}: {length:g} s with no line. Fine for spectacle; otherwise shorten it")
    prompt = str(scene.get("kling_prompt") or "")
    if not prompt:
        out.append("no kling_prompt")
    else:
        low = prompt.lower()
        for need, why in (("no fades", "add 'No fades.'"), ("no subtitles", "add 'no subtitles'"),
                          ("hard cuts at", "state the cut times: 'hard cuts at 4s, 7s ...'"),
                          ("one person speaks", "add 'Only one person speaks in each shot.'"),
                          ("normal", "say the delivery: natural, normal conversational speed, real emotion, no long pauses before lines")):
            if need not in low:
                out.append(f"kling_prompt: {why}")
        for s in shots[1:]:
            t = s["start_s"]
            tt = f"{t:g}s"
            if tt not in prompt.replace(" s", "s"):
                out.append(f"kling_prompt does not mention the cut at {tt}")
                break
    return out


# ------------------------------------------------------------ normalising

NUM_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen".split())}
NUM_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
SLANG = {
    "kinda": "kind of", "sorta": "sort of", "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "lemme": "let me", "gimme": "give me", "dunno": "do not know", "ok": "okay", "cause": "because",
    "cos": "because", "cuz": "because", "coz": "because", "ya": "you", "yeah": "yeah", "yep": "yeah",
    "can't": "can not", "cannot": "can not", "won't": "will not", "let's": "let us", "ain't": "is not",
}
SUFFIXES = (("n't", " not"), ("'re", " are"), ("'ve", " have"), ("'ll", " will"), ("'m", " am"),
            ("'d", " would"), ("'s", " is"))


def norm_word(raw: str) -> list[str]:
    """One spoken word -> normalised tokens: lower case, no punctuation, contractions expanded,
    slang expanded. Number words are merged later."""
    w = raw.lower().replace(chr(0x2019), "'").replace(chr(0x2018), "'").replace("`", "'")
    w = re.sub(r"[^\w'\-]", " ", w)
    toks: list[str] = []
    for part in re.split(r"[\s\-]+", w):
        part = part.strip("'_")
        if not part:
            continue
        if part in SLANG:
            toks.extend(SLANG[part].split())
            continue
        for suf, rep in SUFFIXES:
            if part.endswith(suf) and len(part) > len(suf):
                part = part[: -len(suf)] + rep
                break
        toks.extend(t for t in part.replace("'", "").split() if t)
    return toks


def merge_numbers(tokens: list[tuple]) -> list[tuple]:
    """'thirty', 'two' -> '32'; 'thirty' -> '30'. Works on (token, *payload) tuples, payload of the first kept."""
    out: list[tuple] = []
    i = 0
    while i < len(tokens):
        t = tokens[i][0]
        if t in NUM_TENS:
            val = NUM_TENS[t]
            if i + 1 < len(tokens) and tokens[i + 1][0] in NUM_UNITS and 0 < NUM_UNITS[tokens[i + 1][0]] < 10:
                val += NUM_UNITS[tokens[i + 1][0]]
                out.append((str(val),) + tuple(tokens[i][1:-1]) + (tokens[i + 1][-1],))
                i += 2
                continue
            out.append((str(val),) + tuple(tokens[i][1:]))
        elif t in NUM_UNITS:
            out.append((str(NUM_UNITS[t]),) + tuple(tokens[i][1:]))
        elif t == "hundred" and out and out[-1][0].isdigit():
            prev = out.pop()
            out.append((str(int(prev[0]) * 100),) + tuple(prev[1:]))
        else:
            out.append(tokens[i])
        i += 1
    return out


def norm_text(text: str) -> list[str]:
    toks = [(t, 0) for w in text.split() for t in norm_word(w)]
    return [t[0] for t in merge_numbers(toks)]


# -------------------------------------------------------------- transcript

def load_transcript(path: Path) -> tuple[list[dict], str]:
    """Return word list [{start, end, text}] and a description."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        die(f"could not read transcript {path} as JSON: {exc}")

    def item(d: dict) -> dict | None:
        txt = d.get("text", d.get("word"))
        s, e = d.get("start", d.get("start_s")), d.get("end", d.get("end_s"))
        if txt is None or not isinstance(s, (int, float)) or not isinstance(e, (int, float)):
            return None
        return {"start": float(s), "end": float(e), "text": str(txt)}

    def spread(seg: dict) -> list[dict]:
        ws = [w for w in seg["text"].split() if w.strip()]
        if not ws:
            return []
        total = sum(len(w) for w in ws)
        t = seg["start"]
        out = []
        for w in ws:
            d = (seg["end"] - seg["start"]) * len(w) / max(1, total)
            out.append({"start": t, "end": t + d, "text": w})
            t += d
        return out

    def from_list(lst: list) -> tuple[list[dict], str]:
        items = [x for x in (item(d) for d in lst if isinstance(d, dict)) if x]
        if not items:
            die(f"{path}: no {{start, end, text}} items found")
        word_level = all(len(x["text"].split()) <= 1 for x in items)
        if word_level:
            return items, "word-level list"
        return [w for x in items for w in spread(x)], "segment-level list (word times spread evenly)"

    if isinstance(data, list):
        words, kind = from_list(data)
    elif isinstance(data, dict):
        if isinstance(data.get("words"), list) and data["words"]:
            words, kind = from_list(data["words"])
        elif isinstance(data.get("wordsFlat"), list) and data["wordsFlat"]:
            words, kind = from_list(data["wordsFlat"])
        elif isinstance(data.get("segments"), list):
            words = []
            seg_level = False
            for seg in data["segments"]:
                ws = seg.get("words") if isinstance(seg, dict) else None
                got = [x for x in (item(w) for w in ws or [] if isinstance(w, dict)) if x]
                if got:
                    words.extend(got)
                else:
                    s = item(seg) if isinstance(seg, dict) else None
                    if s:
                        words.extend(spread(s))
                        seg_level = True
            kind = "segments" + (" (some word times spread evenly)" if seg_level else " with word times")
        else:
            die(f"{path}: expected a list, or an object with 'segments' or 'words'")
    else:
        die(f"{path}: expected a JSON list or object")
    words = [w for w in words if w["text"].strip()]
    words.sort(key=lambda w: w["start"])
    return words, kind


def whisper_transcribe(ffmpeg: str, video: Path, model_name: str, language: str | None, notes: list[str]) -> tuple[list[dict], dict]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        die("faster-whisper is not installed. pip install faster-whisper, or pass --transcript path.json "
            "(a list of {start, end, text}) from any speech-to-text tool")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-vn", "-ac", "1",
             "-ar", "16000", str(wav)], capture_output=True)
        sys.stderr.write(f"{PROG}: transcribing with faster-whisper '{model_name}' (CPU, int8) ...\n")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segs, info = model.transcribe(str(wav), word_timestamps=True, language=language, beam_size=5,
                                      condition_on_previous_text=False)
        segments = []
        words = []
        for s in segs:
            ws = [{"start": round(float(w.start), 3), "end": round(float(w.end), 3), "text": w.word.strip()}
                  for w in (s.words or []) if w.word.strip()]
            segments.append({"start": round(float(s.start), 3), "end": round(float(s.end), 3),
                             "text": s.text.strip(), "words": ws})
            words.extend(ws)
    if not words:
        warn("the transcriber heard no words", notes)
    return words, {"source": f"faster-whisper {model_name} (cpu int8)", "language": getattr(info, "language", None),
                   "segments": segments}


# ------------------------------------------------------------------ grading

def structure(rgb: np.ndarray) -> np.ndarray:
    """Edge-magnitude map normalised by its mean: keeps shapes, ignores overall brightness."""
    g = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1.0)
    m = np.sqrt(cv2.Sobel(g, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(g, cv2.CV_32F, 0, 1) ** 2)
    return m / (m.mean() + 1e-6)


def structure_change(a: np.ndarray, b: np.ndarray) -> float:
    """1 - correlation of the edge maps. Same picture under a lightning flash: about 0.2 to 0.4.
    A real cut to a new shot: about 0.9 to 1.1."""
    ea, eb = structure(a), structure(b)
    ea -= ea.mean()
    eb -= eb.mean()
    return float(1.0 - (ea * eb).sum() / (np.sqrt(float((ea * ea).sum() * (eb * eb).sum())) + 1e-6))


def detect_cuts(scores, frames, pts, thresh, min_gap, flash_dist):
    """Cuts = ffmpeg scene score above thresh (same as select='gt(scene,T)'), deduped within min_gap s,
    keeping the strongest. A candidate whose shapes stay put across it (edge maps before and after still
    correlate) is a flash or a lighting change (lightning, a lamp switching on), not a cut."""
    cands = [(t, s) for t, s in scores if s > thresh]
    groups: list[list[tuple[float, float]]] = []
    for t, s in cands:
        if groups and t - groups[-1][-1][0] < min_gap:
            groups[-1].append((t, s))
        else:
            groups.append([(t, s)])
    cuts, flashes = [], []
    t0 = scores[0][0] if scores else 0.0
    n = len(frames)
    for g in groups:
        t, s = max(g, key=lambda x: x[1])
        t = t - t0
        k = int(np.argmin(np.abs(pts - t)))
        before = frames[max(0, k - 2)]
        change = max(structure_change(before, frames[min(n - 1, int(np.argmin(np.abs(pts - (t + dt)))))])
                     for dt in (0.15, 0.4))
        c = {"time_s": round(float(pts[k]), 3), "frame": k, "scene_score": round(s, 3),
             "structure_change": round(change, 3)}
        if change < flash_dist:
            flashes.append(c)
        else:
            cuts.append(c)
    near = [{"time_s": round(t - t0, 3), "scene_score": round(s, 3)}
            for t, s in scores if thresh * 0.6 < s <= thresh]
    return cuts, flashes, near


def match_cuts(planned: list[float], actual: list[dict], hit_tol: float, half_tol: float):
    """Greedy nearest matching, one actual cut per planned cut."""
    pairs = sorted(((abs(a["time_s"] - p), pi, ai) for pi, p in enumerate(planned) for ai, a in enumerate(actual)))
    used_p, used_a, match = set(), set(), {}
    for d, pi, ai in pairs:
        if pi in used_p or ai in used_a or d > half_tol:
            continue
        used_p.add(pi)
        used_a.add(ai)
        match[pi] = ai
    rows = []
    for pi, p in enumerate(planned):
        if pi in match:
            a = actual[match[pi]]["time_s"]
            off = a - p
            v = "HIT" if abs(off) <= hit_tol else "HALF"
            rows.append({"planned_s": p, "actual_s": a, "offset_s": round(off, 3), "verdict": v})
        else:
            near = min(actual, key=lambda a: abs(a["time_s"] - p))["time_s"] if actual else None
            rows.append({"planned_s": p, "actual_s": None, "nearest_s": near, "offset_s": None, "verdict": "MISS"})
    extra = [a for ai, a in enumerate(actual) if ai not in used_a]
    return rows, extra


def actual_shots(cut_times: list[float], dur: float, planned: list[dict]) -> list[dict]:
    """Shots as they came out, each mapped to the planned shot it overlaps most."""
    edges = [0.0] + sorted(cut_times) + [dur]
    out = []
    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        best, best_ov = None, -1.0
        for s in planned:
            ov = min(b, s["end_s"]) - max(a, s["start_s"])
            if ov > best_ov:
                best, best_ov = s, ov
        out.append({"n": i + 1, "start_s": round(a, 3), "end_s": round(b, 3), "planned_shot": best["id"] if best else None})
    return out


def find_line(ptoks: list[str], words: list[dict], shot: dict, used: set[int]):
    """Best contiguous window of transcript tokens for the planned tokens. Returns dict or None."""
    toks = words  # list of dicts with 'tok', 'wi'
    n = len(ptoks)
    if n == 0 or not toks:
        return None
    best = []
    for i in range(len(toks)):
        for L in range(max(1, n - 3), n + 4):
            j = i + L
            if j > len(toks):
                break
            cand = [t["tok"] for t in toks[i:j]]
            sm = difflib.SequenceMatcher(None, ptoks, cand, autojunk=False)
            r = sm.ratio()
            if r < 0.3:
                continue
            ts = toks[i]["start"]
            if shot["start_s"] - 1 <= ts <= shot["end_s"] + 1:
                dist = 0.0
            else:
                dist = min(abs(ts - shot["start_s"]), abs(ts - shot["end_s"]))
            overlap = sum(1 for t in toks[i:j] if t["idx"] in used)
            best.append((r, dist, overlap, i, j))
    if not best:
        return None
    top = max(b[0] for b in best)
    pool = [b for b in best if b[0] >= top - 0.02]
    r, dist, overlap, i, j = min(pool, key=lambda b: (b[2] > 0, b[1], -b[0], abs((b[4] - b[3]) - n)))
    # trim unmatched tokens at the window edges
    cand = [t["tok"] for t in toks[i:j]]
    blocks = [b for b in difflib.SequenceMatcher(None, ptoks, cand, autojunk=False).get_matching_blocks() if b.size]
    if blocks:
        i2 = i + blocks[0].b
        j2 = i + blocks[-1].b + blocks[-1].size
        cand2 = [t["tok"] for t in toks[i2:j2]]
        r2 = difflib.SequenceMatcher(None, ptoks, cand2, autojunk=False).ratio()
        if r2 >= r - 1e-9:
            i, j, r = i2, j2, r2
    return {"i": i, "j": j, "ratio": r}


def align_lines(plines: list[list[str]], toks: list[dict]) -> list[list[int]]:
    """Align the whole script (all planned lines in order) against the whole transcript, then give each
    line the heard tokens aligned to it, including garbled replacements ("it" heard as "a did").
    Returns, per line, the indices into toks."""
    P, owner = [], []
    for li, pt in enumerate(plines):
        P.extend(pt)
        owner.extend([li] * len(pt))
    H = [t["tok"] for t in toks]
    got: list[list[int]] = [[] for _ in plines]
    if not P or not H:
        return got
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, P, H, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                got[owner[a1 + k]].append(b1 + k)
        elif op == "replace":
            # share the heard tokens between the lines in proportion to their planned tokens
            span = a2 - a1
            for k in range(b2 - b1):
                pa = a1 + min(span - 1, int(k * span / (b2 - b1)))
                got[owner[pa]].append(b1 + k)
        # 'insert' (heard, not planned) stays unassigned: it is reported as unplanned speech
        # 'delete' (planned, not heard) shows up in the line's word diff
    return [sorted(g) for g in got]


def diff_words(ptoks: list[str], htoks: list[str]) -> list[str]:
    out = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, ptoks, htoks, autojunk=False).get_opcodes():
        if op == "replace":
            out.append(f"'{' '.join(ptoks[a1:a2])}' heard as '{' '.join(htoks[b1:b2])}'")
        elif op == "delete":
            out.append(f"'{' '.join(ptoks[a1:a2])}' missing")
        elif op == "insert":
            out.append(f"extra '{' '.join(htoks[b1:b2])}'")
    return out


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


def labelled(img: Image.Image | np.ndarray, text: str, color=(255, 255, 255), bar=24, size=14,
             bg=(18, 18, 18)) -> Image.Image:
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    w, h = img.size
    lines = text.split("\n")
    bar = max(bar, 6 + (size + 4) * len(lines))
    canvas = Image.new("RGB", (w, h + bar), bg)
    canvas.paste(img, (0, bar))
    d = ImageDraw.Draw(canvas)
    for k, ln in enumerate(lines):
        d.text((6, 3 + k * (size + 4)), ln, fill=color, font=font(size))
    return canvas


def fit(img: Image.Image, w: int, h: int, bg=(0, 0, 0)) -> Image.Image:
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    out = Image.new("RGB", (w, h), bg)
    out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def grid(rows: list[list[Image.Image]], gap=6, bg=(0, 0, 0)) -> Image.Image:
    rows = [r for r in rows if r]
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


def header(width: int, text: str, size=16, color=(255, 255, 255), bg=(30, 30, 30)) -> Image.Image:
    lines = text.split("\n")
    img = Image.new("RGB", (width, 8 + (size + 6) * len(lines)), bg)
    d = ImageDraw.Draw(img)
    for k, ln in enumerate(lines):
        d.text((8, 4 + k * (size + 6)), ln, fill=color, font=font(size))
    return img


_FACE = None


def face_crop(frame: np.ndarray, size: int) -> tuple[Image.Image, float] | None:
    """Largest frontal face (OpenCV Haar cascade, ships with opencv-python), squared and padded, plus the
    face width as a share of the frame width; or None."""
    global _FACE
    if _FACE is None:
        try:
            _FACE = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
        except Exception:  # noqa: BLE001
            _FACE = False
    if _FACE is False or _FACE.empty():
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    faces = _FACE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(max(24, w // 20), max(24, w // 20)))
    if len(faces) == 0:
        return None
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    cx, cy = x + fw / 2, y + fh * 0.62  # bias toward the mouth
    half = max(fw, fh) * 0.75
    x0, y0 = int(max(0, cx - half)), int(max(0, cy - half))
    x1, y1 = int(min(w, cx + half)), int(min(h, cy + half))
    crop = Image.fromarray(frame[y0:y1, x0:x1])
    return fit(crop, size, size), fw / w


# ----------------------------------------------------- optional face scores

def face_embedder():
    """insightface or face_recognition if importable, else None. Never required."""
    try:
        from insightface.app import FaceAnalysis  # type: ignore
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))

        def emb(rgb: np.ndarray):
            fs = app.get(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            if not fs:
                return None
            f = max(fs, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            v = f.normed_embedding
            return v / (np.linalg.norm(v) + 1e-9)

        return "insightface (cosine similarity, about 0.4+ is usually the same person)", emb, lambda a, b: float(np.dot(a, b))
    except Exception:  # noqa: BLE001
        pass
    try:
        import face_recognition  # type: ignore

        def emb2(rgb: np.ndarray):
            enc = face_recognition.face_encodings(np.ascontiguousarray(rgb))
            return enc[0] if enc else None

        return ("face_recognition (1 - distance, about 0.4+ is usually the same person)", emb2,
                lambda a, b: float(1.0 - np.linalg.norm(a - b)))
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------ report

def mark_points(m: dict) -> tuple[float | None, str]:
    for who in ("human", "claude"):
        v = m.get(who)
        if v in POINTS:
            return POINTS[v], who
    v = m.get("script")
    if v in POINTS:
        return POINTS[v], "script"
    return None, ""


def score(report: dict) -> dict:
    total, pending, by = 0.0, [], {}
    for k in MARKS:
        p, who = mark_points(report["marks"][k])
        if p is None:
            pending.append(k)
        else:
            total += p
            by[k] = who
    return {"points": total, "out_of": 4, "pending": pending, "decided_by": by,
            "rule": "HIT 1, HALF 0.5, MISS 0 per mark. SYNC and SAME count once Claude or the human fills them in "
                    "(scene_grade.py --fill). A human call overrides Claude's, which overrides the script's."}


def render_md(r: dict) -> str:
    def rel(path: str) -> str:
        try:
            return Path(path).relative_to(r["out_dir"]).as_posix()
        except (ValueError, KeyError):
            return path

    md = [f"# Scene grade: {Path(r['video']).name}", ""]
    vi = r["video_info"]
    md.append(f"Scene: `{Path(r['scene']).name}` ({r.get('title') or 'untitled'}). Clip: {vi['width']}x{vi['height']}, "
              f"{vi['duration']:.2f} s. Transcript: {r['transcript']['source']}.")
    md.append("")
    sc = r["score"]
    pend = f" (pending: {', '.join(sc['pending'])})" if sc["pending"] else ""
    md.append(f"## Score: **{sc['points']:g} / 4**{pend}")
    md.append("")
    md.append("| Mark | Script | Claude | Human (final) | Why |")
    md.append("|---|---|---|---|---|")
    for k in MARKS:
        m = r["marks"][k]
        md.append(f"| {k} | {m.get('script') or ''} | {m.get('claude') or ''} | {m.get('human') or ''} | "
                  f"{'; '.join(x for x in (m.get('summary', ''), m.get('why_claude', ''), m.get('why_human', '')) if x)} |")
    md.append("")
    md.append("## SHOTS: cuts")
    md.append("")
    md.append(f"Threshold: scene score > {r['settings']['cut_threshold']}. HIT within {r['settings']['hit_tol_s']} s, "
              f"HALF within {r['settings']['half_tol_s']} s.")
    md.append("")
    md.append("| Planned cut | Actual cut | Offset | Verdict |")
    md.append("|---|---|---|---|")
    for c in r["cuts"]["planned"]:
        act = f"{c['actual_s']:.2f} s" if c["actual_s"] is not None else (
            f"none (nearest {c['nearest_s']:.2f} s)" if c.get("nearest_s") is not None else "none")
        off = f"{c['offset_s']:+.2f} s" if c["offset_s"] is not None else ""
        md.append(f"| {c['planned_s']:g} s | {act} | {off} | {c['verdict']} |")
    md.append("")
    if r["cuts"]["extra"]:
        md.append("Extra cuts (not in the plan): " + ", ".join(
            f"{c['time_s']:.2f} s (score {c['scene_score']:.2f})" for c in r["cuts"]["extra"]))
    else:
        md.append("Extra cuts: none.")
    if r["cuts"]["flashes"]:
        md.append("")
        md.append("Ignored as flashes or lighting changes (same shapes before and after): " + ", ".join(
            f"{c['time_s']:.2f} s (score {c['scene_score']:.2f}, structure change {c['structure_change']:.2f})"
            for c in r["cuts"]["flashes"]))
    if r["cuts"]["near_misses"]:
        md.append("")
        md.append("Below the threshold but close, check by eye: " + ", ".join(
            f"{c['time_s']:.2f} s ({c['scene_score']:.2f})" for c in r["cuts"]["near_misses"][:8]))
    md.append("")
    md.append("## LINES")
    md.append("")
    md.append("| # | Shot (plan) | Speaker | Planned line | Heard | Said at | In shot | Similarity | Verdict |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for ln in r["lines"]:
        said = f"{ln['start_s']:.2f} to {ln['end_s']:.2f} s" if ln["start_s"] is not None else ""
        md.append(f"| {ln['n']} | {ln['shot']} ({ln['shot_window_s'][0]:g} to {ln['shot_window_s'][1]:g} s) | "
                  f"{ln['speaker'] or ''} | {ln['planned']} | {ln['heard'] or ''} | {said} | "
                  f"{ln['in_actual_shot'] if ln['in_actual_shot'] is not None else ''} | {ln['similarity']:.2f} | {ln['verdict']} |")
    md.append("")
    garbled = [(ln["n"], d) for ln in r["lines"] for d in ln["word_diffs"]]
    if garbled:
        md.append("Words that came out differently:")
        md.extend(f"- line {n}: {d}" for n, d in garbled)
    else:
        md.append("Words that came out differently: none.")
    notes = [(ln["n"], x) for ln in r["lines"] for x in ln["notes"]]
    if notes:
        md.append("")
        md.append("Line notes:")
        md.extend(f"- line {n}: {x}" for n, x in notes)
    if r["unplanned_speech"]:
        md.append("")
        md.append("Speech that matches no planned line: " + "; ".join(
            f"\"{u['text']}\" at {u['start_s']:.2f} s" for u in r["unplanned_speech"]))
    md.append("")
    md.append("## SYNC: needs your eyes")
    md.append("")
    md.append("Open each strip: 6 frames across the moment the line is said (face crops underneath when a face was "
              "found). Does the mouth move on the words, and is it the planned speaker's mouth?")
    md.append("")
    for ln in r["lines"]:
        if ln["voiceover"]:
            md.append(f"- line {ln['n']} ({ln['speaker']}): voiceover, no lips to check")
    for s in r["sync"]:
        md.append(f"- line {s['line']} ({s['speaker']}), audio {s['start_s']:.2f} to {s['end_s']:.2f} s: `{rel(s['image'])}`"
                  + (f" **{s['flag']}**" if s.get("flag") else ""))
    md.append("")
    md.append("## SAME: needs your eyes")
    md.append("")
    md.append(f"`{rel(r['same']['image'])}`: reference images on the top row, then one mid-shot frame per shot as it came out, "
              "labelled with the planned shot and who should be on screen. Same face, hair, clothes and product in every tile?")
    if r["same"].get("face_scores"):
        md.append("")
        md.append(f"Face similarity ({r['same']['face_method']}): " + ", ".join(
            f"shot {f['shot']} vs {f['ref']}: {f['score']:.2f}" for f in r["same"]["face_scores"]))
    md.append("")
    if r["plan_check"]:
        md.append("## Plan check")
        md.append("")
        md.extend(f"- {x}" for x in r["plan_check"])
        md.append("")
    if r["warnings"]:
        md.append("## Warnings")
        md.append("")
        md.extend(f"- {w}" for w in r["warnings"])
        md.append("")
    md.append(f"Images: `{rel(r['contact_sheet'])}`, `{rel(r['same']['image'])}`, `sync/`. "
              "Verdicts are suggestions; the human's call is final.")
    return "\n".join(md) + "\n"


def write_report(out: Path, report: dict) -> str:
    report["score"] = score(report)
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = render_md(report)
    (out / "report.md").write_text(md, encoding="utf-8")
    return md


# ---------------------------------------------------------------- modes

def do_fill(args) -> None:
    out = args.fill
    rp = out / "report.json"
    if not rp.is_file():
        die(f"{rp} not found: run a grade into that folder first")
    report = json.loads(rp.read_text(encoding="utf-8"))
    if not args.mark:
        die("--fill needs at least one --mark MARK=VERDICT (for example --mark SYNC=HALF)")
    for m in args.mark:
        if "=" not in m:
            die(f"--mark '{m}' should look like SYNC=HALF")
        k, v = (x.strip().upper() for x in m.split("=", 1))
        if k not in MARKS:
            die(f"unknown mark '{k}': use one of {', '.join(MARKS)}")
        if v not in POINTS:
            die(f"verdict '{v}' should be HIT, HALF or MISS")
        report["marks"][k][args.by] = v
        if args.why:
            report["marks"][k][f"why_{args.by}"] = args.why
    md = write_report(out, report)
    print(md)
    print(f"Updated {out / 'report.md'}")


def do_check(path: Path) -> None:
    scene = load_scene(path)
    found = check_scene(scene)
    if found:
        print(f"{path.name}: {len(found)} finding(s)")
        for f in found:
            print(f"- {f}")
    else:
        print(f"{path.name}: no findings")


def do_grade(args) -> None:
    ffmpeg, ffprobe = need_tool("ffmpeg"), need_tool("ffprobe")
    for p, what in ((args.scene, "--scene"), (args.video, "--video")):
        if not p or not p.is_file():
            die(f"{what} file not found: {p}")
    if args.transcript and not args.transcript.is_file():
        die(f"--transcript file not found: {args.transcript}")
    scene = load_scene(args.scene)
    out = args.out
    (out / "sync").mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    plan_check = check_scene(scene)

    info = probe(ffprobe, args.video)
    dur = info["duration"]
    shots = scene["shots"]
    plan_dur = scene.get("duration_s") or shots[-1]["end_s"]
    if abs(plan_dur - dur) > 0.6:
        warn(f"scene is {plan_dur} s but the clip runs {dur:.2f} s. Check the Duration setting.", notes)
    if not info["has_audio"] and not args.transcript:
        die("the clip has no audio track; nothing to transcribe")

    # ---- SHOTS
    sw = 160
    sh = even(sw * info["height"] / info["width"])
    small, pts = decode_small(ffmpeg, args.video, sw, sh)
    if len(pts) != len(small):
        warn("could not read frame timestamps; assuming constant frame rate", notes)
        pts = np.arange(len(small)) / info["fps"]
    pts = pts - pts[0]
    scores = scene_scores(ffmpeg, args.video)
    cuts, flashes, near = detect_cuts(scores, small, pts, args.cut_threshold, 0.5, args.flash_dist)
    planned_cuts = [float(s["start_s"]) for s in shots[1:]]
    cut_rows, extra = match_cuts(planned_cuts, cuts, args.hit_tol, args.half_tol)
    act = actual_shots([c["time_s"] for c in cuts], dur, shots)
    by_id = {s["id"]: s for s in shots}

    if not planned_cuts:
        shots_v = "HIT" if not extra else "HALF"
    else:
        mean = sum(POINTS[c["verdict"]] for c in cut_rows) / len(cut_rows)
        if mean == 1.0 and not extra:
            shots_v = "HIT"
        elif mean < 0.5:
            shots_v = "MISS"
        else:
            shots_v = "HALF"
    n_hit = sum(c["verdict"] == "HIT" for c in cut_rows)
    shots_sum = f"{n_hit}/{len(cut_rows)} planned cuts within {args.hit_tol} s, {len(extra)} extra"

    # ---- LINES
    if args.transcript:
        words, kind = load_transcript(args.transcript)
        tx = {"source": f"{args.transcript.name} ({kind})"}
    else:
        words, txdata = whisper_transcribe(ffmpeg, args.video, args.whisper_model, args.language, notes)
        (out / "transcript.json").write_text(json.dumps(txdata, indent=2), encoding="utf-8")
        tx = {"source": txdata["source"], "file": str(out / "transcript.json")}
    # Some STT engines stretch a word across the silence before it ("Hold" from 4.4 to 8.1 s). A spoken
    # word rarely lasts over 1.2 s, so start such words 0.6 s before they end.
    stretched = [w for w in words if w["end"] - w["start"] > 1.2 and len(w["text"].split()) == 1]
    for w in stretched:
        w["start"] = round(w["end"] - 0.6, 3)
    if stretched:
        warn(f"{len(stretched)} word(s) lasted over 1.2 s in the transcript (" + ", ".join(
            repr(w["text"]) for w in stretched[:4]) + "); their start was moved to 0.6 s before their end", notes)
    tokens = []
    for wi, w in enumerate(words):
        for t in norm_word(w["text"]):
            tokens.append((t, wi, w["start"], w["end"]))
    tokens = merge_numbers(tokens)
    toks = [{"tok": t[0], "wi": t[1], "start": t[2], "end": t[-1], "idx": k} for k, t in enumerate(tokens)]

    def shot_of(t0: float, t1: float) -> dict | None:
        best, bo = None, 0.0
        for a in act:
            ov = min(t1, a["end_s"]) - max(t0, a["start_s"])
            if ov > bo:
                best, bo = a, ov
        if best is None:
            best = next((a for a in act if a["start_s"] <= t0 < a["end_s"]), act[-1])
        return best

    planned_lines = [(s, ln) for s in shots for ln in shot_lines(s)]
    aligned = align_lines([norm_text(ln["text"]) for _, ln in planned_lines], toks)
    lines = []
    used: set[int] = set()
    n = 0
    for (s, ln), al in zip(planned_lines, aligned):
        n += 1
        ptoks = norm_text(ln["text"])
        row = {"n": n, "shot": s["id"], "shot_window_s": [s["start_s"], s["end_s"]], "speaker": ln["speaker"],
               "voiceover": ln["voiceover"], "planned": ln["text"], "heard": None, "start_s": None, "end_s": None,
               "in_actual_shot": None, "similarity": 0.0, "word_diffs": [], "notes": [], "verdict": "MISS"}
        m = None
        if al:
            # the contiguous heard span, so words inserted inside the line count against it
            span = [t["tok"] for t in toks[al[0]:al[-1] + 1]]
            m = {"i": al[0], "j": al[-1] + 1,
                 "ratio": difflib.SequenceMatcher(None, ptoks, span, autojunk=False).ratio()}
        if m is None or m["ratio"] < args.line_half:
            # said out of script order, or lost in the alignment: search the transcript for this line alone
            alt = find_line(ptoks, toks, s, used)
            if alt and alt["ratio"] >= args.line_half and (m is None or alt["ratio"] > m["ratio"]):
                m = alt
                row["notes"].append("found out of script order")
        if m and m["ratio"] >= 0.3:
            seg = toks[m["i"]:m["j"]]
            wis = sorted({t["wi"] for t in seg})
            row["heard"] = " ".join(words[k]["text"] for k in range(wis[0], wis[-1] + 1))
            row["start_s"] = round(seg[0]["start"], 3)
            row["end_s"] = round(seg[-1]["end"], 3)
            row["similarity"] = round(m["ratio"], 3)
            row["word_diffs"] = diff_words(ptoks, [t["tok"] for t in seg]) if m["ratio"] < 1.0 else []
            in_window = s["start_s"] - args.line_tol <= row["start_s"] <= s["end_s"] + args.line_tol
            a = shot_of(row["start_s"], row["end_s"])
            row["in_actual_shot"] = a["n"]
            row["_actual"] = a
            if m["ratio"] >= args.line_hit and in_window:
                row["verdict"] = "HIT"
            elif m["ratio"] >= args.line_half:
                row["verdict"] = "HALF"
                if not in_window:
                    row["notes"].append(f"starts at {row['start_s']:.2f} s, outside its planned shot "
                                        f"({s['start_s']:g} to {s['end_s']:g} s, +/- {args.line_tol:g} s)")
                if m["ratio"] < args.line_hit:
                    row["notes"].append(f"only {m['ratio']:.2f} similar: words garbled or missing")
            else:
                row["notes"].append(f"best match only {m['ratio']:.2f} similar: probably not said")
            if row["verdict"] != "MISS":
                used.update(t["idx"] for t in seg)
                into = row["start_s"] - a["start_s"]
                alen = a["end_s"] - a["start_s"]
                if into > 1.5 and into > 0.4 * alen:
                    row["notes"].append(f"starts {into:.1f} s into its {alen:.1f} s shot: lines belong at the start of the shot")
        else:
            row["notes"].append("not found in the transcript")
        lines.append(row)
    if lines:
        mean = sum(POINTS[l["verdict"]] for l in lines) / len(lines)
        lines_v = "HIT" if mean == 1.0 else ("MISS" if mean < 0.5 else "HALF")
    else:
        lines_v = "HIT"
        warn("the scene has no lines", notes)
    lines_sum = f"{sum(l['verdict'] == 'HIT' for l in lines)}/{len(lines)} lines HIT"

    # speech that matches no line
    unplanned = []
    cur: list[dict] = []
    for t in toks + [None]:
        if t is not None and t["idx"] not in used:
            cur.append(t)
            continue
        if cur:
            wis = sorted({x["wi"] for x in cur})
            unplanned.append({"text": " ".join(words[k]["text"] for k in wis), "start_s": round(cur[0]["start"], 3),
                              "end_s": round(cur[-1]["end"], 3)})
            cur = []

    # ---- images
    tw = args.tile_width
    th = even(tw * info["height"] / info["width"])

    def idx_at(t: float) -> int:
        return int(np.argmin(np.abs(pts - t)))

    want: dict[int, None] = {}
    sheet_ts = [i + 0.5 for i in range(int(dur))]
    for t in sheet_ts:
        want[idx_at(t)] = None
    mid_idx = []
    for a in act:
        pad = min(0.4, (a["end_s"] - a["start_s"]) / 4)
        mid = (a["start_s"] + a["end_s"]) / 2
        k = idx_at(min(max(mid, a["start_s"] + pad), a["end_s"] - pad))
        mid_idx.append(k)
        want[k] = None
    sync_plan = []
    for ln in lines:
        if ln["start_s"] is None or ln["verdict"] == "MISS" or ln["voiceover"]:
            continue
        t0, t1 = ln["start_s"], max(ln["end_s"], ln["start_s"] + 0.3)
        ks = [idx_at(t) for t in np.linspace(t0, t1, 6)]
        sync_plan.append((ln, ks))
        want.update({k: None for k in ks})
    big = extract_frames(ffmpeg, args.video, list(want), tw, th)

    def frame(k: int) -> np.ndarray:
        if k in big:
            return big[k]
        return cv2.resize(small[k], (tw, th), interpolation=cv2.INTER_LINEAR)

    # contact sheet: one frame per second, cut seconds in red
    cut_ts = [c["time_s"] for c in cuts]
    tiles = []
    cw = max(120, tw // 2)
    chh = even(cw * th / tw)
    for t in sheet_ts:
        k = idx_at(t)
        a = next((x for x in act if x["start_s"] <= pts[k] < x["end_s"]), act[-1])
        has_cut = any(t - 0.5 <= c < t + 0.5 for c in cut_ts)
        im = Image.fromarray(frame(k)).resize((cw, chh), Image.LANCZOS)
        tiles.append(labelled(im, f"{t - 0.5:.0f}s  shot {a['n']}" + ("  CUT" if has_cut else ""),
                              color=(255, 110, 110) if has_cut else (230, 230, 230), size=12, bar=20))
    per_row = 10 if info["width"] < info["height"] else 6
    sheet = grid([tiles[i:i + per_row] for i in range(0, len(tiles), per_row)])
    sheet_path = out / "contact-sheet.jpg"
    sheet.convert("RGB").save(sheet_path, quality=88)

    # SAME grid: references on top, one mid frame per actual shot
    refs = scene.get("references") or []
    ref_tiles, ref_imgs = [], {}
    for k, ref in enumerate(refs, start=1):
        f = ref.get("file")
        p = None
        if f:
            p = Path(f)
            if not p.is_absolute():
                p = (args.refs / p) if args.refs else (args.scene.parent / p)
        if p is None or not p.is_file():
            if f:
                warn(f"reference image not found: {p}", notes)
            continue
        try:
            img = Image.open(p).convert("RGB")
        except Exception as exc:  # noqa: BLE001
            warn(f"could not read reference {p}: {exc}", notes)
            continue
        ref_imgs[str(ref.get("id"))] = np.asarray(img)
        rh = th if info["width"] < info["height"] else int(th * 1.5)
        rw = int(min(2 * tw, max(tw // 2, rh * img.width / img.height)))
        ref_tiles.append(labelled(fit(img, rw, rh), f"REF {ref.get('index', k)}: {ref.get('id', p.stem)}",
                                  color=(255, 210, 80)))
    shot_tiles = []
    for a, k in zip(act, mid_idx):
        ps = by_id.get(a["planned_shot"], {})
        who = ps.get("on_screen") or ([ps.get("speaker")] if ps.get("speaker") else []) or [ps.get("subject", "")]
        who = ", ".join(str(x) for x in who if x)
        shot_tiles.append(labelled(frame(k), f"shot {a['n']} {a['start_s']:.1f}-{a['end_s']:.1f}s (plan {a['planned_shot']})\n{who}"))
    per = 7 if info["width"] < info["height"] else 5
    rows = [ref_tiles[i:i + per] for i in range(0, len(ref_tiles), per)] + \
           [shot_tiles[i:i + per] for i in range(0, len(shot_tiles), per)]
    same = grid(rows, gap=8)
    same_path = out / "same-grid.jpg"
    same.convert("RGB").save(same_path, quality=90)

    face_scores, face_method = [], None
    if ref_imgs and not args.no_face_scores:
        fe = face_embedder()
        if fe:
            face_method, emb, simf = fe
            ref_emb = {rid: emb(img) for rid, img in ref_imgs.items()}
            for a, k in zip(act, mid_idx):
                ps = by_id.get(a["planned_shot"], {})
                subj = ps.get("subject") or ps.get("speaker")
                if not subj or ref_emb.get(str(subj)) is None:
                    continue
                e = emb(extract_frames(ffmpeg, args.video, [k], info["width"], info["height"]).get(k, frame(k)))
                if e is not None:
                    face_scores.append({"shot": a["n"], "ref": str(subj), "score": round(simf(e, ref_emb[str(subj)]), 3)})

    # SYNC strips
    sync = []
    for ln, ks in sync_plan:
        fr = [frame(k) for k in ks]
        row1 = [labelled(f, f"{pts[k]:.2f}s", size=13, bar=20) for f, k in zip(fr, ks)]
        crops = [face_crop(f, tw) for f in fr]
        rows = [row1]
        found = [c for c in crops if c is not None]
        # a zoomed face row only helps when the face is small in the frame (wide and medium shots)
        if len(found) >= 3 and min(c[1] for c in found) < 0.3:
            rows.append([c[0] if c is not None else Image.new("RGB", (tw, tw), (0, 0, 0)) for c in crops])
        a = ln["_actual"]
        ps = by_id.get(a["planned_shot"], {})
        on = [str(x) for x in (ps.get("on_screen") or ([ps.get("speaker")] if ps.get("speaker") else []))]
        flag = ""
        if not ln["voiceover"] and ln["speaker"] and on and str(ln["speaker"]) not in on:
            flag = (f"audio sits mostly in shot {a['n']} (plan shot {a['planned_shot']}: {', '.join(on)}), "
                    f"which does not show {ln['speaker']}")
            ln["notes"].append(flag)
        else:
            # softer: the line starts over another shot that does not show the speaker
            a0 = next((x for x in act if x["start_s"] <= ln["start_s"] < x["end_s"]), a)
            ps0 = by_id.get(a0["planned_shot"], {})
            on0 = [str(x) for x in (ps0.get("on_screen") or ([ps0.get("speaker")] if ps0.get("speaker") else []))]
            spill = min(ln["end_s"], a0["end_s"]) - ln["start_s"]
            if (a0 is not a and not ln["voiceover"] and ln["speaker"] and on0
                    and str(ln["speaker"]) not in on0 and spill >= 0.4):
                ln["notes"].append(f"the first {spill:.1f} s plays over shot {a0['n']} ({', '.join(on0)}), "
                                   f"before the cut to {ln['speaker']}")
        body = grid(rows)
        head = header(body.width, f"Line {ln['n']}  {ln['speaker'] or ''}{' (voiceover)' if ln['voiceover'] else ''}  "
                                  f"audio {ln['start_s']:.2f}-{ln['end_s']:.2f}s  in shot {a['n']} "
                                  f"(plan shot {a['planned_shot']}, {', '.join(on) or 'nobody listed'})\n"
                                  f"planned: {ln['planned']}\nheard:   {ln['heard']}",
                      color=(255, 140, 140) if flag else (255, 255, 255))
        strip = grid([[head], [body]], gap=0)
        p = out / "sync" / f"line{ln['n']:02d}_{ln['start_s']:.2f}s.jpg"
        strip.convert("RGB").save(p, quality=90)
        sync.append({"line": ln["n"], "speaker": ln["speaker"], "voiceover": ln["voiceover"], "start_s": ln["start_s"],
                     "end_s": ln["end_s"], "frames_s": [round(float(pts[k]), 3) for k in ks], "image": str(p),
                     "flag": flag})
    for ln in lines:
        ln.pop("_actual", None)
    flagged = [s for s in sync if s["flag"]]

    report = {
        "tool": "shot-director scene_grade.py",
        "out_dir": str(out),
        "title": scene.get("title"),
        "scene": str(args.scene),
        "video": str(args.video),
        "video_info": {**info, "frames": len(pts)},
        "transcript": tx,
        "settings": {"cut_threshold": args.cut_threshold, "min_cut_gap_s": 0.5, "flash_dist": args.flash_dist,
                     "hit_tol_s": args.hit_tol, "half_tol_s": args.half_tol, "line_hit": args.line_hit,
                     "line_half": args.line_half, "line_tol_s": args.line_tol},
        "marks": {
            "SHOTS": {"script": shots_v, "summary": shots_sum},
            "LINES": {"script": lines_v, "summary": lines_sum},
            "SYNC": {"script": "NEEDS-EYES", "summary": f"{len(sync)} strips in sync/"
                     + (f"; {len(flagged)} line(s) heard over a shot that does not show the speaker" if flagged else "")},
            "SAME": {"script": "NEEDS-EYES", "summary": "see same-grid.jpg"
                     + (f"; face scores by {face_method.split(' ')[0]}" if face_scores else "")},
        },
        "cuts": {"planned": cut_rows, "detected": cuts, "extra": extra, "flashes": flashes, "near_misses": near},
        "actual_shots": act,
        "lines": lines,
        "unplanned_speech": unplanned,
        "sync": sync,
        "same": {"image": str(same_path), "face_method": face_method, "face_scores": face_scores},
        "contact_sheet": str(sheet_path),
        "plan_check": plan_check,
        "warnings": notes,
        "note": "SHOTS and LINES are suggestions from cut detection and a transcript. SYNC and SAME need eyes: fill "
                "them with --fill. The human's call is final.",
    }
    md = write_report(out, report)
    print(md)
    print(f"Wrote {out / 'report.md'}")


def main() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Grade a multi-shot dialogue scene against scene.json on four marks: SHOTS (cuts), LINES "
                    "(transcribed and fuzzy matched), SYNC and SAME (frame strips and a reference grid for your eyes). "
                    "Also --check a scene.json against the planning rules, and --fill the SYNC and SAME calls.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Transcript JSON for --transcript: a list of {start, end, text} (word or segment level), or "
               "{\"segments\": [{start, end, text, words?}]}, or {\"words\": [...]}. Times in seconds.",
    )
    ap.add_argument("--scene", type=Path, help="scene.json written in PLAN-SCENE mode")
    ap.add_argument("--video", type=Path, help="the downloaded clip (mp4/mov)")
    ap.add_argument("--out", type=Path, help="output folder (created if missing)")
    ap.add_argument("--refs", type=Path, help="folder holding the reference images named in scene.json "
                    "(default: next to scene.json)")
    ap.add_argument("--transcript", type=Path, help="use this transcript instead of running faster-whisper")
    ap.add_argument("--whisper-model", default="small", help="faster-whisper model (default small; base is faster, "
                    "medium is more accurate)")
    ap.add_argument("--language", default="en", help="spoken language code for faster-whisper (default en; "
                    "'auto' to detect)")
    ap.add_argument("--cut-threshold", type=float, default=0.3,
                    help="ffmpeg scene score above which a frame counts as a cut, as in select='gt(scene,T)' "
                         "(default 0.3). Lower it if real cuts are missed in dark footage.")
    ap.add_argument("--flash-dist", type=float, default=0.5,
                    help="a candidate cut whose shapes barely change across it (edge-map change below this) is a "
                         "flash or lighting change, not a cut (default 0.5; real cuts score about 0.9+; 0 disables)")
    ap.add_argument("--hit-tol", type=float, default=1.0, help="cut within this many seconds of the plan is a HIT (default 1.0)")
    ap.add_argument("--half-tol", type=float, default=2.0, help="cut within this many seconds is a HALF (default 2.0)")
    ap.add_argument("--line-hit", type=float, default=0.85, help="line similarity for a HIT (default 0.85)")
    ap.add_argument("--line-half", type=float, default=0.6, help="line similarity for a HALF (default 0.6)")
    ap.add_argument("--line-tol", type=float, default=1.0, help="a line may start this many seconds outside its "
                    "planned shot and still HIT (default 1.0)")
    ap.add_argument("--tile-width", type=int, default=0, help="width of each frame tile in pixels "
                    "(default 270 for vertical, 384 for wide)")
    ap.add_argument("--no-face-scores", action="store_true", help="skip the optional insightface / face_recognition scores")
    ap.add_argument("--check", type=Path, metavar="SCENE_JSON", help="only check a scene.json against the planning rules")
    ap.add_argument("--fill", type=Path, metavar="OUT", help="fill in mark verdicts in an existing grade folder")
    ap.add_argument("--mark", action="append", default=[], metavar="MARK=VERDICT",
                    help="with --fill: for example SYNC=HALF or SAME=HIT (repeatable; HIT, HALF or MISS)")
    ap.add_argument("--by", choices=("claude", "human"), default="human", help="with --fill: whose call this is (default human)")
    ap.add_argument("--why", default="", help="with --fill: one-line reason")
    args = ap.parse_args()

    if args.fill:
        do_fill(args)
        return
    if args.check:
        do_check(args.check)
        return
    if not (args.scene and args.video and args.out):
        ap.error("--scene, --video and --out are required (or use --check / --fill)")
    if args.language == "auto":
        args.language = None
    if args.tile_width <= 0 and args.video.is_file():
        v = probe(need_tool("ffprobe"), args.video)
        args.tile_width = 270 if v["width"] < v["height"] else 384
    do_grade(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reference-study helper: frame grid, luminance timeline, scene changes and loudness for a video file.

Usage:
  python tools/study_frames.py VIDEO.mp4 --out OUTDIR [--step 3] [--cols 6] [--ffmpeg /path/ffmpeg]

Outputs (in OUTDIR):
  <name>-grid.jpg        frames every --step seconds with timestamps
  <name>-study.json      duration, fps, stage luminance, intro length, dim/black segments,
                         scene-change counts (thresholds 0.3 / 0.15), integrated loudness / LRA / true peak
Only public, locally available files are analysed. Numbers describe the sampled file (e.g. a low-res
public stream), not the platform master; never present them as complete human review.
"""
import argparse, json, os, re, shutil, subprocess, sys


def find_ffmpeg(explicit=None):
    if explicit:
        return explicit
    env = os.environ.get("FFMPEG")
    if env:
        return env
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg  # optional fallback
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found: install ffmpeg or `pip install imageio-ffmpeg`, or pass --ffmpeg")


def run(cmd, binary=False):
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout if binary else (r.stderr.decode("utf-8", "ignore") + r.stdout.decode("utf-8", "ignore"))


def probe(ff, video):
    txt = run([ff, "-hide_banner", "-i", video])
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", txt)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None
    fps = re.search(r"([\d.]+) fps", txt)
    size = re.search(r"(\d{2,5})x(\d{2,5})", txt)
    return {"duration": dur, "fps": float(fps[1]) if fps else None,
            "size": [int(size[1]), int(size[2])] if size else None}


def scene_changes(ff, video, thr):
    txt = run([ff, "-hide_banner", "-i", video, "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", txt)]


def loudness(ff, video):
    txt = run([ff, "-hide_banner", "-nostats", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"])
    summ = txt[txt.rfind("Summary:"):]
    g = lambda pat: (lambda m: float(m[1]) if m else None)(re.search(pat, summ))
    return {"integrated_lufs": g(r"I:\s+(-?[\d.]+) LUFS"), "lra_lu": g(r"LRA:\s+(-?[\d.]+) LU"),
            "true_peak_dbfs": g(r"Peak:\s+(-?[\d.]+) dBFS")}


def luminance_timeline(ff, video, rate=4):
    import numpy as np
    raw = run([ff, "-hide_banner", "-loglevel", "error", "-i", video, "-vf", f"fps={rate},scale=64:36,format=gray",
               "-f", "rawvideo", "-"], binary=True)
    arr = np.frombuffer(raw, dtype=np.uint8)
    n = len(arr) // (64 * 36)
    lum = arr[: n * 64 * 36].reshape(n, -1).mean(axis=1)
    base = float(np.median(lum))

    def segs(mask):
        out, s = [], None
        for i, m in enumerate(mask):
            if m and s is None:
                s = i
            if (not m or i == n - 1) and s is not None:
                e = i if not m else i + 1
                if e - s >= 2:
                    out.append([round(s / rate, 2), round(e / rate, 2)])
                s = None
        return out

    dim = segs((lum < base * 0.55) & (lum > 15))
    black = segs(lum <= 15)
    intro = None
    for i in range(max(0, n - rate)):
        if all(lum[i:i + rate] > base * 0.85):
            intro = round(i / rate, 2)
            break
    return {"stage_median_luminance": round(base, 1), "intro_until_stage_s": intro,
            "dim_segments": dim, "black_segments": black}


def frame_grid(ff, video, out_jpg, step, cols, duration):
    from PIL import Image, ImageDraw, ImageFont
    import tempfile, glob
    tmp = tempfile.mkdtemp(prefix="grid-")
    run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vf", f"fps=1/{step},scale=320:-1", "-q:v", "4",
         os.path.join(tmp, "%04d.jpg")])
    frames = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
    if not frames:
        return None
    tw, th = 320, 180
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 18, index=2)
    except Exception:
        font = ImageFont.load_default()
    for i, f in enumerate(frames):
        r, c = divmod(i, cols)
        sheet.paste(Image.open(f).convert("RGB").resize((tw, th)), (c * tw, r * th))
        ts = i * step
        draw.rectangle([c * tw, r * th, c * tw + 60, r * th + 22], fill=(0, 0, 0))
        draw.text((c * tw + 3, r * th + 1), f"{int(ts // 60)}:{int(ts % 60):02d}", fill=(255, 230, 0), font=font)
    sheet.save(out_jpg, quality=80)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"frames": len(frames), "size": list(sheet.size)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--step", type=float, default=3.0)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--ffmpeg")
    a = ap.parse_args()
    ff = find_ffmpeg(a.ffmpeg)
    os.makedirs(a.out, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.video))[0]
    info = probe(ff, a.video)
    result = {"file": os.path.basename(a.video), **info,
              "scene_changes_0.3": scene_changes(ff, a.video, 0.3),
              "scene_changes_0.15_count": len(scene_changes(ff, a.video, 0.15)),
              "loudness": loudness(ff, a.video),
              "luminance": luminance_timeline(ff, a.video),
              "grid": frame_grid(ff, a.video, os.path.join(a.out, f"{name}-grid.jpg"), a.step, a.cols, info["duration"]),
              "note": "Sampled-file metrics only; not human review, not platform master."}
    with open(os.path.join(a.out, f"{name}-study.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: result[k] for k in ("file", "duration", "fps", "scene_changes_0.15_count", "loudness", "luminance")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

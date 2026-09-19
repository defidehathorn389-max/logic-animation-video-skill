#!/usr/bin/env python3
"""Script budget check for puzzle videos: characters, estimated duration, five-beat cues, subtitle line lengths.

Usage:
  python tools/script_budget.py SCRIPT.(txt|json) [--rate 320] [--target 130] [--max-line 12]

SCRIPT.json may be a list of {"text": ...} sections or {"sections":[...]} ; .txt is plain narration.
Estimates only: real duration must be measured from the synthesized narration.
"""
import argparse, json, re, sys

BEATS = {
    "题设/提问": [r"请问", r"问题来了", r"怎么保证", r"怎么才能", r"如何", r"你会怎么"],
    "错误思路": [r"第一反应", r"大多数人", r"很多人", r"常规做法", r"掉进坑里", r"看起来.*无解"],
    "破局/步骤": [r"破局", r"第一步", r"分.{1,3}步", r"只需要", r"最有效", r"关键"],
    "为何必然": [r"为什么.*(一定|必然|正确)", r"无论", r"不管.*都", r"情况一", r"只可能"],
    "原理/收束": [r"这就是", r"这叫", r"原理", r"法则", r"模型", r"真正的"],
}


def load(path):
    if path.endswith(".json"):
        data = json.load(open(path, encoding="utf-8"))
        secs = data.get("sections", data) if isinstance(data, dict) else data
        return [s["text"] if isinstance(s, dict) else str(s) for s in secs]
    return [p for p in re.split(r"\n\s*\n", open(path, encoding="utf-8").read()) if p.strip()]


def count_chars(text):
    return len(re.sub(r"[\s，。、；：？！“”‘’（）《》,.;:?!\"'()\[\]\-—…]", "", text))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--rate", type=float, default=320, help="chars per minute (measure your own voice; 300-340 typical)")
    ap.add_argument("--target", type=float, default=130, help="target seconds")
    ap.add_argument("--max-line", type=int, default=12, help="max chars per subtitle display line")
    a = ap.parse_args()
    secs = load(a.script)
    full = "\n".join(secs)
    total = count_chars(full)
    est = total / a.rate * 60
    print(f"sections={len(secs)} chars={total} est_duration={est:.0f}s (rate {a.rate:.0f}/min, target {a.target:.0f}s)")
    for i, s in enumerate(secs, 1):
        c = count_chars(s)
        print(f"  [{i:02d}] {c:4d} chars ~{c / a.rate * 60:5.1f}s  {s.strip()[:28]}…")
    missing = [b for b, pats in BEATS.items() if not any(re.search(p, full) for p in pats)]
    print("beats:", "all cue phrases present" if not missing else "missing cues -> " + ", ".join(missing))
    long_lines = [seg for seg in re.split(r"[，。；：？！,.;:?!\n]", full) if count_chars(seg) > a.max_line]
    print(f"subtitle: {len(long_lines)} phrases longer than {a.max_line} chars (split for display)")
    for seg in long_lines[:8]:
        print("   -", seg.strip())
    verdict = "OK" if est <= a.target * 1.05 else f"OVER by {est - a.target:.0f}s: cut repetition / merge symmetric steps before changing voice speed"
    print("verdict:", verdict)
    return 0 if est <= a.target * 1.05 else 1


if __name__ == "__main__":
    sys.exit(main())

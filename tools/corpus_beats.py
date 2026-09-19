#!/usr/bin/env python3
"""Aggregate narration beat statistics over a folder of ASR transcripts (research use).

Usage:
  python tools/corpus_beats.py ASR_DIR [--catalog catalog.json] [--out stats.json]

Each ASR file: JSON list of {"start","end","text"} (e.g. faster-whisper output). Reports per video and
corpus medians: speech rate, time of first question cue, presence/time of beat cues (wrong approach,
steps, proof, objection, principle, sponsor), opening type, segment length distribution. Machine
transcripts are noisy; treat numbers as estimates and never reuse transcript text as script material.
"""
import argparse, glob, json, os, re, statistics as st

CUES = {
    "question": r"请问|问题来了|你会怎么|怎么才能|怎么保证|你能.*吗|该怎么|如何才能",
    "wrong": r"第一反应|大多数人|绝大多数|很多人|普通人|常规|掉进坑|看似",
    "pivot": r"破局|真正|其实|关键|最有效|锁死|做减法",
    "steps": r"第一步|分.{1,3}步|第一趟|第一轮|我们先看|先看",
    "proof": r"为什么.*(一定|必然|正确|敢)|无论|不管.*都|情况一|只可能|一定是",
    "objection": r"有人可能会问|有人会说|你可能会问|可能有人",
    "principle": r"这就是|这叫|法则|模型|思维|定律|原理|底层逻辑",
    "sponsor": r"熬夜|试一试|链接|购物车|优惠|评论区|下单|回到游戏|言归正传|后备能源",
    "catchphrase": r"长脑子|思维游戏",
}


def analyse(path):
    segs = json.load(open(path, encoding="utf-8"))
    if not segs:
        return None
    full = "".join(s["text"] for s in segs)
    chars = sum(len(re.sub(r"[\s，。、；：？！,.;:?!]", "", s["text"])) for s in segs)
    speech = sum(s["end"] - s["start"] for s in segs) or 1
    end = segs[-1]["end"]
    first = {}
    for name, pat in CUES.items():
        for s in segs:
            if re.search(pat, s["text"]):
                first[name] = round(s["start"], 1)
                break
    seg_lens = [len(s["text"]) for s in segs]
    opening = "catchphrase" if re.search(CUES["catchphrase"], segs[0]["text"]) else "direct"
    principle_names = re.findall(r"(?:这就是|这叫)([^，。,]{2,14}?)(?:法则|思维|模型|定律|原理|效应)", full)
    return {"chars": chars, "speech_s": round(speech, 1), "end_s": round(end, 1), "rate_cpm": round(chars / speech * 60),
            "first_cue_s": first, "first_cue_pct": {k: round(v / end * 100, 1) for k, v in first.items()},
            "opening": opening, "seg_len_median": st.median(seg_lens), "principle_name_candidates": principle_names[:3]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("asr_dir")
    ap.add_argument("--catalog")
    ap.add_argument("--out")
    a = ap.parse_args()
    cat = {}
    if a.catalog:
        data = json.load(open(a.catalog, encoding="utf-8"))
        for v in data.get("videos", data if isinstance(data, list) else []):
            cat[v.get("bvid") or v.get("id")] = v
    per = {}
    for f in sorted(glob.glob(os.path.join(a.asr_dir, "*.json"))):
        key = os.path.splitext(os.path.basename(f))[0]
        r = analyse(f)
        if r:
            if key in cat:
                r.update({"title": cat[key].get("title", "")[:30], "plays": cat[key].get("plays"), "published": cat[key].get("published")})
            per[key] = r

    def med(xs):
        xs = [x for x in xs if x is not None]
        return round(st.median(xs), 1) if xs else None

    n = len(per)
    summary = {"videos": n, "rate_cpm_median": med([r["rate_cpm"] for r in per.values()]),
               "seg_len_median": med([r["seg_len_median"] for r in per.values()]),
               "opening_catchphrase_share": round(sum(r["opening"] == "catchphrase" for r in per.values()) / n, 2) if n else None}
    for cue in CUES:
        have = [r for r in per.values() if cue in r["first_cue_s"]]
        summary[cue] = {"present_share": round(len(have) / n, 2) if n else None,
                        "first_time_median_s": med([r["first_cue_s"][cue] for r in have]),
                        "first_time_median_pct": med([r["first_cue_pct"][cue] for r in have])}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if a.out:
        json.dump({"summary": summary, "per_video": per}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

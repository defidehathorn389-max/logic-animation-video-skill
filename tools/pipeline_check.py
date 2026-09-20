#!/usr/bin/env python3
"""pipeline_check.py <episode_dir> [--stage N]
Checks that an episode directory has the artefacts/gate fields required by references/episode-pipeline.md.
Only checks presence/shape; it does NOT replace looking at the images. Exit 1 if any required item for the requested stage is missing."""
import json, sys, re
from pathlib import Path

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    d = Path(sys.argv[1]); stage = 99
    if '--stage' in sys.argv: stage = int(sys.argv[sys.argv.index('--stage') + 1])
    miss = []; ok = []
    def need(cond, msg, st):
        if st > stage: return
        (ok if cond else miss).append(f'[{st}] {msg}')
    sj = d / 'script.json'; s = json.load(open(sj)) if sj.exists() else {}
    secs = s.get('sections', [])
    chars = sum(len(re.findall(r'[\u4e00-\u9fff0-9]', x.get('text', ''))) for x in secs)
    need(bool(secs), 'script.json.sections 存在', 1)
    need(500 <= chars <= 640, f'字数 500–640（现 {chars}）', 1)
    need(len(secs) >= 6, f'≥6 段（7 点结构）（现 {len(secs)}）', 1)
    lc = s.get('logic_check', {})
    need(bool(lc), 'script.json.logic_check 存在', 2)
    need(bool(lc.get('sentence_checks')), 'logic_check.sentence_checks（逐句模拟实例）', 2)
    need(any(k in lc for k in ('premise', 'premise_ok', '前提')), 'logic_check 含前提合理性', 2)
    need(any(k in lc for k in ('followup', 'answer_22', 'upgrade', '追问')), 'logic_check 含追问验证', 2)
    sb = list(d.glob('storyboard*.md')) + list(d.glob('文案草稿*.md'))
    need(bool(sb), 'storyboard.md / 文案草稿-rN.md（文字分镜）', 3)
    if sb:
        txt = ''.join(open(f, encoding='utf-8').read() for f in sb)
        need('| 段' in txt or '| 时间' in txt, '分镜表格（段/时间/画面/屏幕文字）', 3)
        need(re.search(r'首帧|0\.0 ?s|0–1|≤1s|0\.8 ?s', txt) is not None, '分镜含首帧/1 秒事件说明', 3)
        need('素材' in txt, '分镜含素材清单', 3)
    need(bool(lc.get('approved_by_user')), 'logic_check.approved_by_user（用户放行记录）', 4)
    need((d / 'timeline.json').exists() and (d / 'char-alignment.json').exists(), 'timeline.json + char-alignment.json', 5)
    if (d / 'timeline.json').exists():
        tl = json.load(open(d / 'timeline.json')); tot = tl.get('total', 0); pause = tl.get('pause_seconds', 0)
        cpm = chars / max(1e-6, (tot - pause - 1)) * 60 if tot else 0
        need(85 <= tot <= 120, f'总长 85–120s（现 {tot:.1f}）', 5)
        need(315 <= cpm <= 345, f'语速 320–340 cpm（现 {cpm:.0f}）', 5)
    need((d / 'art' / 'components.json').exists(), 'art/components.json', 6)
    need((d / 'checks' / 'art-sheet.jpg').exists() or (d / 'art' / 'sheet.jpg').exists(), 'checks/art-sheet.jpg（素材总览已看图）', 6)
    need((d / 'render.py').exists(), 'render.py', 7)
    if (d / 'render.py').exists():
        src = open(d / 'render.py', encoding='utf-8').read()
        need('--preview' in src and 'collisions' in src, 'render.py 支持 --preview + collisions', 7)
        need(re.search(r'WHITE\)\s*$', src, re.M) is None, '屏幕文字无白色（压暗段除外，需人工确认）', 7)
    need((d / 'video.mp4').exists(), 'video.mp4', 8)
    need((d / 'checks' / 'enc-sheet.jpg').exists(), 'checks/enc-sheet.jpg（成片抽帧）', 8)
    need((d / 'checks' / 'enc-first6s.jpg').exists(), 'checks/enc-first6s.jpg（前 6 秒 2fps）', 8)
    need((d / 'subtitles.srt').exists(), 'subtitles.srt', 9)
    need((d / 'publish.json').exists(), 'publish.json', 9)
    need(all((d / 'cover' / f'cover-{r}.jpg').exists() for r in ('3x4', '4x3', '16x9')), '封面三比例 3x4/4x3/16x9', 9)
    print('\n'.join('OK   ' + x for x in ok)); print('\n'.join('MISS ' + x for x in miss))
    print(f'\n{len(ok)} ok, {len(miss)} missing (stage ≤ {stage})'); sys.exit(1 if miss else 0)

if __name__ == '__main__': main()

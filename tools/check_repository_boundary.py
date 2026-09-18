from pathlib import Path
import argparse,sys
p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default=Path(__file__).resolve().parents[1],type=Path);a=p.parse_args()
allowed={'.md','.py','.json','.txt','.yml','.yaml','.toml'}
media={'.png','.jpg','.jpeg','.webp','.svg','.mp4','.wav','.mp3','.zip','.srt','.ass','.pdf','.pptx','.docx'}
errors=[]
for f in a.root.rglob('*'):
 if not f.is_file() or any(x in {'.git','__pycache__','.venv'} for x in f.parts):continue
 rel=f.relative_to(a.root)
 if f.suffix.lower() in media:errors.append(str(rel)+': media/delivery forbidden')
 if f.name.upper().startswith('HANDOFF') or f.name in {'qa.json','catalog.json','progress.json','remote-verification.json','cleanup-report.json'}:errors.append(str(rel)+': task-state output forbidden')
 if rel.parts[0] not in {'tools','references','templates','README.md','SKILL.md','LICENSE','requirements.txt','requirements-alignment.txt','.gitignore'}:errors.append(str(rel)+': outside public allowlist')
if errors:print('\n'.join(errors));sys.exit(1)
print('PASS: public Skill contains only rules, tools and templates')

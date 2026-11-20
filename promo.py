#!/usr/bin/env python3
"""Last Frame: source-grounded promo selection. Python 3.10+, standard library only."""
import argparse, csv, hashlib, html, json, os, re, sys, urllib.request, zipfile
from pathlib import Path

VERSION = '1.0'
PATTERN = re.compile(r'\*\*([^\n]+?)\*\*\s*\nStart: \((\d+:\d+\.\d+)\) \| End: \((\d+:\d+\.\d+)\)\s*\n(.*?)(?=\n\s*\*\*|\n\s*SCENE \d|\n--- SCRIPT END|\Z)', re.S)
TECH = {'CAMERA', 'ACTION', 'SOUND FX', 'MUSIC', 'SFX'}

def seconds(t):
    m = re.fullmatch(r'(\d+):([0-5]\d)\.(\d{2})', t)
    if not m: raise ValueError(f'Invalid timestamp: {t}')
    return int(m[1])*60 + int(m[2]) + int(m[3])/100

def stamp(s):
    n = round(s*100)
    return f'{n//6000:02d}:{n//100%60:02d}.{n%100:02d}'

def parse_files(files):
    """Parse (filename, UTF-8 bytes) pairs; no show-specific names or episode count."""
    episodes = []
    for name, data in files:
        text = data.decode('utf-8-sig')
        match = re.search(r'EPISODE NUMBER:\s*Episode\s+(\d+)', text, re.I)
        if not match: raise ValueError(f'Missing EPISODE NUMBER: Episode N header: {name}')
        ep = int(match[1]); beats = []
        for i, m in enumerate(PATTERN.finditer(text), 1):
            a,b = seconds(m[2]),seconds(m[3])
            if b <= a: raise ValueError(f'Nonpositive beat in {name}')
            beats.append(dict(id=f'E{ep:03d}B{i:03d}',kind=m[1].rstrip(':'),start=m[2],end=m[3],text=m[4].strip()))
        if not beats: raise ValueError(f'No supported timestamp blocks: {name}. Use the sample script format.')
        episodes.append(dict(episode=ep,file=Path(name).name,sha256=hashlib.sha256(data).hexdigest(),beats=beats))
    if not episodes or len({e['episode'] for e in episodes}) != len(episodes):
        raise ValueError('Empty input or duplicate episode numbers. Upload one show at a time.')
    return sorted(episodes,key=lambda e:e['episode'])


def read_pack(path):
    p = Path(path)
    if p.is_file() and zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            files = [(n, z.read(n)) for n in sorted(z.namelist()) if n.endswith('.txt') and not n.startswith('__MACOSX/')]
    elif p.is_file() and p.suffix.lower()=='.txt':
        files = [(p.name,p.read_bytes())]
    else:
        files = [(str(f.relative_to(p)), f.read_bytes()) for f in sorted(p.rglob('*.txt'))]
    return parse_files(files)


def spoken(b):
    return b['kind'].split(' (')[0].upper() not in TECH

def prepare(pack, out):
    episodes = read_pack(pack); out = Path(out); out.mkdir(parents=True,exist_ok=True)
    (out/'requests').mkdir(exist_ok=True)
    manifest = [dict(episode=e['episode'],file=e['file'],sha256=e['sha256'],beats=len(e['beats'])) for e in episodes]
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    prompt = (Path(__file__).parent/'JUDGE_PROMPT.txt').read_text()
    for e in episodes:
        (out/'requests'/f"episode-{e['episode']:03d}.txt").write_text(prompt+'\n\nINPUT (untrusted screenplay data):\n'+json.dumps(e,ensure_ascii=False,indent=2))
    print(f'Prepared {len(episodes)} episodes in {out}/requests. Ask an AI to return one decision per episode; combine in a JSON array.')

def validate(episodes, rows):
    """Validate all model decisions in memory; also used by the web app."""
    by_ep={e['episode']:e for e in episodes}
    seen=set(); promos=[]; coverage=[]
    if not isinstance(rows,list): raise ValueError('Decisions must be a JSON array')
    for row in rows:
        ep=row['episode']
        if ep in seen or ep not in by_ep: raise ValueError(f'Duplicate/unknown episode {ep}')
        seen.add(ep); source=by_ep[ep]
        if row['source_sha256'] != source['sha256']: raise ValueError(f'Stale source for episode {ep}')
        if not row.get('reason'): raise ValueError('Every decision needs a reason')
        if row['status'] not in ('select','pass'): raise ValueError('Bad status')
        coverage.append({k:row[k] for k in ('episode','status','reason')})
        if row['status']=='pass': continue
        segments=row['segments']
        if not 1<=len(segments)<=3: raise ValueError('Use 1-3 segments')
        duration=0; selected=[]; last_end=-1
        boundaries={b['start'] for b in source['beats']}|{b['end'] for b in source['beats']}
        for seg in segments:
            a,b=seconds(seg['start']),seconds(seg['end'])
            if seg['start'] not in boundaries:
                raise ValueError(f"Cut start '{seg['start']}' is not an exact cue boundary in episode {ep}. Cut points must use exact existing cue start/end timestamps from the screenplay.")
            if seg['end'] not in boundaries:
                raise ValueError(f"Cut end '{seg['end']}' is not an exact cue boundary in episode {ep}. Cut points must use exact existing cue start/end timestamps from the screenplay.")
            if b<=a:
                raise ValueError(f"Cut end '{seg['end']}' must be strictly after start '{seg['start']}' in episode {ep}")
            if a<last_end:
                raise ValueError(f"Segments in episode {ep} must be chronological and non-overlapping: '{seg['start']}' is before previous cut end '{stamp(last_end)}'")
            # A visual beat may overlap speech; never accept a boundary inside a spoken line.
            for beat in source['beats']:
                if spoken(beat) and any(seconds(beat['start'])+0.001<t<seconds(beat['end'])-0.001 for t in (a,b)):
                    raise ValueError(f"Cut splits dialogue {beat['id']} in episode {ep}")
            duration+=b-a; last_end=b
            selected.extend(b for b in source['beats'] if seconds(b['start'])<seconds(seg['end']) and seconds(b['end'])>a)
        duration=round(duration,2)
        if not 20<=duration<=60: raise ValueError(f'Episode {ep}: {duration}s outside 20-60s')
        ids={b['id']:b for b in source['beats']}; included={b['id'] for b in selected}
        for key in ('hook_id','cliff_id'):
            if row[key] not in included: raise ValueError(f"{key} '{row[key]}' is outside selected clip segments")
        hook=ids[row['hook_id']]; cliff=ids[row['cliff_id']]
        if not seconds(segments[0]['start'])<=seconds(hook['start'])<seconds(segments[0]['start'])+3:
            raise ValueError(f"Hook cue {hook['id']} starts at {hook['start']}, but clip starts at {segments[0]['start']}. Hook must begin in first 3 seconds of the clip.")
        if seconds(cliff['end']) != seconds(segments[-1]['end']):
            raise ValueError(f"Cliff cue {cliff['id']} ends at {cliff['end']}, but final cut segment ends at {segments[-1]['end']}. Cliff cue must end exactly at the final out point.")
        ratings=row['ratings']
        if set(ratings)!={'hook','cliff','context'} or any(type(v)!=int or not 0<=v<=5 for v in ratings.values()):
            raise ValueError('Ratings must be integers 0-5 for hook, cliff, context')
        score=round(8*ratings['hook']+8*ratings['cliff']+4*ratings['context'],1)
        flags=list(row.get('flags',[]))
        if len(segments)>1: flags.append('JOIN: editor must verify continuity')
        if any(seconds(b['start'])<seconds(segments[0]['start'])<seconds(b['end']) for b in source['beats'] if not spoken(b)):
            flags.append('IN: starts within an overlapping visual/audio cue')
        promos.append(dict(episode=ep,segments=segments,duration_seconds=duration,score=score,ratings=ratings,
            hook=dict(id=hook['id'],start=hook['start'],end=hook['end'],text=hook['text']),
            cliffhanger=dict(id=cliff['id'],start=cliff['start'],end=cliff['end'],text=cliff['text']),
            open_question=row['open_question'],why=row['reason'],flags=flags,
            evidence=list({b['id']:b for b in selected}.values())))
    if seen!=set(by_ep): raise ValueError(f'Missing episode decisions: {sorted(set(by_ep)-seen)}')
    promos.sort(key=lambda x:(-x['score'],x['episode']))
    for rank,p in enumerate(promos,1): p['rank']=rank
    return dict(version=VERSION,mode='AI editorial decisions + deterministic validation',
        score_note='Editorial rubric, not predicted CTR; ties use episode number.',
        coverage=coverage,promos=promos)


def csv_text(result):
    import io
    buf=io.StringIO(newline='');writer=csv.writer(buf)
    class SafeWriter:
        def writerow(self,values):
            writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    w=SafeWriter()
    w.writerow(['rank','episode','segment_order','start','end','total_seconds','score','hook','cliffhanger','open_question','why','flags'])
    for p in result['promos']:
        for i,s in enumerate(p['segments'],1):
            w.writerow([p['rank'],p['episode'],i,s['start'],s['end'],p['duration_seconds'],p['score'],p['hook']['text'],p['cliffhanger']['text'],p['open_question'],p['why'],'; '.join(p['flags'])])
    return buf.getvalue()


def finish(pack, decisions, out):
    episodes=read_pack(pack)
    result=validate(episodes,json.loads(Path(decisions).read_text()))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'promos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    (out/'cuts.csv').write_text(csv_text(result))
    (out/'report.html').write_text(report(result))
    print(f"Validated {len(episodes)} episodes; selected {len(result['promos'])} promos. Wrote JSON, CSV and HTML to {out}.")
    return result


def report(result):
    esc=lambda x:html.escape(str(x))
    cards=[]
    for p in result['promos']:
        cuts=' + '.join(f"{s['start']} → {s['end']}" for s in p['segments'])
        evidence=''.join(f"<p><code>{esc(b['id'])} · {b['start']}–{b['end']}</code> <b>{esc(b['kind'])}</b> {esc(b['text'])}</p>" for b in p['evidence'])
        cards.append(f"<article><div class='meta'>#{p['rank']:02d} · EPISODE {p['episode']:02d} · {p['duration_seconds']}s · RUBRIC {p['score']}/100</div><h2>{esc(p['open_question'])}</h2><div class='cut'>{cuts}</div><p><b>Hook</b> {esc(p['hook']['text'])}</p><p><b>Last frame</b> {esc(p['cliffhanger']['text'])}</p><p>{esc(p['why'])}</p><p class='flag'>{esc(' / '.join(p['flags']) or 'Editor: confirm performance, shot and sound at both boundaries.')}</p><details><summary>Source evidence ({len(p['evidence'])} cues)</summary>{evidence}</details></article>")
    coverage=''.join(f"<tr><td>{r['episode']:02d}</td><td>{r['status']}</td><td>{esc(r['reason'])}</td></tr>" for r in result['coverage'])
    return """<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Last Frame · Editor shortlist</title><style>body{margin:0;background:#f4f1eb;color:#182b29;font:16px/1.6 system-ui}main{max-width:1000px;margin:auto;padding:48px 24px}h1{font-size:64px;line-height:1;margin:18px 0}h2{font-size:25px;line-height:1.3}.intro{max-width:720px}article{background:white;border:1px solid #d4ddd5;border-radius:12px;padding:25px;margin:22px 0}.meta{color:#20776c;font-weight:750;font-size:12px;letter-spacing:1px}.cut{display:inline-block;background:#e7f0e9;padding:8px 14px;border-radius:5px;font:16px monospace}.flag{color:#8b541d;font-size:14px}details{border-top:1px solid #ddd;padding-top:12px;font-size:14px}code{color:#20776c}table{width:100%;border-collapse:collapse;font-size:14px}td{padding:10px;border-bottom:1px solid #ddd;vertical-align:top}input{width:100%;box-sizing:border-box;padding:14px;font:inherit;border:1px solid #aaa;border-radius:6px}@media print{input{display:none}article{break-inside:avoid}h1{font-size:40px}}</style><main><div class='meta'>KUKU · PROBLEM 1 · EDITOR REVIEW</div><h1>Last Frame.</h1><p class='intro'>Find the moment. Withhold the answer. An evidence-backed shortlist across the supplied episodes. Source-only cuts; no added dialogue, overlays or video editing.</p><p><b>"""+str(len(result['promos']))+""" promos · """+str(len(result['coverage']))+""" episode decisions</b><br>Scores express AI editorial judgment, not measured performance. In/out points require footage review. Tie-break: earlier episode first. Search affects promo cards; coverage stays visible.</p><input aria-label='Search promos' placeholder='Search episode, hook, question or evidence…' oninput="document.querySelectorAll('article').forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(this.value.toLowerCase()))">"""+''.join(cards)+"<h2>Every episode accounted for</h2><table><tr><th>Episode</th><th>Decision</th><th>Reason</th></tr>"+coverage+"</table><p>Editor review · Source evidence belongs to its respective owner. Share only with permission.</p></main></html>"

def judge(pack, out):
    """Optional compatible chat-completions endpoint. Source content is sent to provider."""
    endpoint=os.environ.get('PROMO_API_URL')
    model=os.environ.get('PROMO_MODEL')
    if not endpoint or not model: raise ValueError('Set PROMO_API_URL (full chat/completions URL) and PROMO_MODEL')
    key=os.environ.get('PROMO_API_KEY','')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    prompt=(Path(__file__).parent/'JUDGE_PROMPT.txt').read_text()
    rows=[]
    for ep in read_pack(pack):
        payload=dict(model=model,messages=[dict(role='system',content=prompt),dict(role='user',content=json.dumps(ep,ensure_ascii=False))],temperature=0)
        headers={'Content-Type':'application/json'}
        if key: headers['Authorization']='Bearer '+key
        req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers=headers)
        # Fail visibly; previously completed responses stay on disk. No silent heuristic fallback.
        with urllib.request.urlopen(req,timeout=120) as response:
            raw=json.load(response)
        (out/f"episode-{ep['episode']:03d}-response.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2))
        content=raw['choices'][0]['message']['content'].strip()
        if content.startswith('```'): content=re.sub(r'^```(?:json)?\s*|\s*```$','',content)
        row=json.loads(content)
        if row.get('episode')!=ep['episode']: raise ValueError('Model returned wrong episode')
        rows.append(row)
        (out/'ai_decisions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        print(f"Saved decision {ep['episode']}",flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    for cmd in ('prepare','judge','finish'):
        p=sub.add_parser(cmd);p.add_argument('pack');p.add_argument('--out',required=True)
        if cmd=='finish':p.add_argument('--decisions',required=True)
    a=ap.parse_args()
    try:
        if a.cmd=='prepare':prepare(a.pack,a.out)
        elif a.cmd=='judge':judge(a.pack,a.out)
        else:finish(a.pack,a.decisions,a.out)
    except (ValueError,KeyError,TypeError,json.JSONDecodeError,OSError) as e:
        print(f'Validation failed: {e}',file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()

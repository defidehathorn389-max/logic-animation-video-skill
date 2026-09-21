"""Sample-exact section timing with zero or more thinking pauses.
No project data, audio IO or alignment estimation. Consumers must read pause_events.
"""
import copy
import math


def pause_plan(script, ids):
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate section ids')
    if 'thinking_pauses' in script:
        raw = script['thinking_pauses']
    else:
        after = script.get('pause_after', 1)
        if not isinstance(after, int) or not 1 <= after <= len(ids):
            raise ValueError('Invalid legacy pause_after')
        raw = [{'after_section': ids[after - 1], 'seconds': script.get('pause_seconds', 3.0)}]
    result = {}
    for item in raw:
        sid = item['after_section']
        seconds = float(item['seconds'])
        if sid not in ids or sid in result:
            raise ValueError('Unknown or duplicate pause anchor')
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Invalid pause duration')
        if seconds:
            result[sid] = seconds
    return result


def build_timeline(script, frames_by_id, sample_rate, gap_seconds=0.3, tail_seconds=None):
    """Use ACTUAL resampled/paced frame counts, never estimated durations.
    A thinking pause REPLACES the usual inter-section gap, not gap+pause.
    """
    sections = script['sections']
    ids = [str(s['id']) for s in sections]
    if not ids or set(ids) != set(frames_by_id):
        raise ValueError('Exactly one frame count required per section')
    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise ValueError('Invalid sample rate')
    for value in frames_by_id.values():
        if not isinstance(value, int) or value <= 0:
            raise ValueError('Invalid frame count')
    plan = pause_plan(script, ids)
    tail_seconds = float(script.get('tail_hold_seconds', 0.8) if tail_seconds is None else tail_seconds)
    if any(not math.isfinite(float(x)) or x < 0 for x in (gap_seconds, tail_seconds)):
        raise ValueError('Invalid gap/tail')
    cursor = 0
    out, events, gaps = [], [], []
    def interval(start, end):
        return {'start_sample': start, 'end_sample': end,
                'start': start / sample_rate, 'end': end / sample_rate,
                'seconds': (end-start) / sample_rate}
    for i, section in enumerate(sections):
        sid = str(section['id'])
        end = cursor + frames_by_id[sid]
        out.append(dict(id=sid, text=section['text'], **interval(cursor, end)))
        cursor = end
        if sid in plan:
            end = cursor + round(plan[sid] * sample_rate)
            events.append(dict(id='thinking-'+str(len(events)+1), after_section=sid, **interval(cursor, end)))
            cursor = end
        elif i < len(sections)-1:
            end = cursor + round(gap_seconds*sample_rate)
            gaps.append(dict(after_section=sid, **interval(cursor, end)))
            cursor = end
    tail_end = cursor + round(tail_seconds*sample_rate)
    result = {'schema_version': 2, 'sample_rate': sample_rate, 'sections': out,
              'pause_events': events, 'gap_events': gaps, 'tail': interval(cursor, tail_end),
              'pause_seconds_total': sum(e['seconds'] for e in events),
              'speech_seconds': sum(frames_by_id.values())/sample_rate,
              'total_samples': tail_end, 'total': tail_end/sample_rate,
              'requires_pause_events_consumer': len(events)>1}
    # Only single-pause compatibility is safe; never silently encode many as one.
    if len(events)==1:
        result.update(pause_start=events[0]['start'], pause_seconds=events[0]['seconds'])
    return result


def place_local_alignment(local_sections, timeline):
    """Translate genuine section-local acoustic timestamps; do not infer/split words.
    Duplicate, missing or out-of-range alignments fail instead of being fabricated.
    """
    slots = {s['id']: s for s in timeline['sections']}
    if {s['id'] for s in local_sections} != set(slots) or len(local_sections)!=len(slots):
        raise ValueError('Alignment section mismatch')
    result = copy.deepcopy(local_sections)
    sr = timeline['sample_rate']
    for section in result:
        slot = slots[section['id']]
        section['start'], section['end'] = slot['start'], slot['end']
        last = -1.0
        for char in section.get('chars', []):
            a, b = float(char['start']), float(char['end'])
            if not (math.isfinite(a) and math.isfinite(b) and -1/sr <= a <= b <= slot['seconds']+1/sr):
                raise ValueError('Local alignment outside actual section audio')
            if a < last - 1/sr:
                raise ValueError('Nonmonotonic local alignment')
            char['start'] = (slot['start_sample']+round(max(0,a)*sr))/sr
            char['end'] = (slot['start_sample']+round(min(slot['seconds'],b)*sr))/sr
            last = a
    return result


def place_local_events(events, timeline):
    """Map caller-provided local subtitle/animation intervals by the same clock.
    No event timing is invented here; section_id must identify the source clip.
    """
    slots = {s['id']: s for s in timeline['sections']}
    sr = timeline['sample_rate']
    result = copy.deepcopy(events)
    for event in result:
        slot = slots[event['section_id']]
        a, b = float(event['start']), float(event['end'])
        if not (math.isfinite(a) and math.isfinite(b) and 0 <= a <= b <= slot['seconds']+1/sr):
            raise ValueError('Event outside actual section audio')
        event['start'] = (slot['start_sample']+round(a*sr))/sr
        event['end'] = (slot['start_sample']+round(min(b,slot['seconds'])*sr))/sr
    return result


def srt_text(events):
    """Format already-mapped sentence intervals, not an alignment algorithm."""
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    out=[];last=0.0
    for i,event in enumerate(sorted(events,key=lambda x:x['start']),1):
        if not last <= event['start'] < event['end']:
            raise ValueError('Subtitle intervals overlap or have no duration')
        out.append(f"{i}\n{stamp(event['start'])} --> {stamp(event['end'])}\n{event['text']}\n")
        last=event['end']
    return '\n'.join(out)

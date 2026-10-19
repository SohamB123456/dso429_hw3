"""DSO 429 HW3 solver: reads questions.csv, writes answers/round-XXXX.json for unanswered rounds."""
import csv, json, re, sys, os, datetime as dt

def nums(s):
    return [float(x.replace(',', '')) for x in re.findall(r'-?\d[\d,]*\.?\d*', s)]

def parse_opt(o):
    o = o.strip()
    try:
        return dt.datetime.strptime(o, '%d %B %Y').date()
    except ValueError:
        pass
    n = nums(o)
    return n[0] if n else o

def compute(q):
    t = q
    n = nums(t)
    if 'converted to' in t and 'per' in t:
        return n[0] * n[1]
    if t.startswith('A retailer sells') or ('units at' in t and 'total revenue' in t):
        return n[0] * n[1]
    if 'gross margin' in t:
        return (n[0] - n[1]) / n[0] * 100
    if 'break even' in t:
        return round(n[0] / (n[1] - n[2]))
    if 'discounted by' in t:
        return n[0] * (1 - n[1] / 100)
    if 'percentage change' in t:
        return (n[1] - n[0]) / n[0] * 100
    if 'overall average' in t:
        return (n[0] * n[1] + n[2] * n[3]) / (n[0] + n[2])
    if 'compounded' in t:
        p, r, y = n[0], n[1], n[2]
        return p * (1 + r / 100) ** y
    if 'probability' in t:
        m = re.search(r'it is an? (\w+) ticket', t)
        kinds = re.findall(r'([\d,]+) (\w+) tickets', t)
        tot = sum(float(a.replace(',', '')) for a, _ in kinds)
        target = [float(a.replace(',', '')) for a, k in kinds if k == m.group(1)][0]
        return target / tot * 100
    if 'ratio' in t:
        m = re.search(r'ratio (\d+):(\d+)', t)
        a, b = float(m.group(1)), float(m.group(2))
        share = a if 'first' in t else b
        return n[0] * share / (a + b)
    if 'series runs' in t:
        seq = [float(x) for x in re.search(r'runs ([\d, ]+?)\. ', t).group(1).replace(',', ' ').split()]
        d1 = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
        if len(set(d1)) == 1:
            return seq[-1] + d1[0]
        r = [seq[i + 1] / seq[i] for i in range(len(seq) - 1)]
        if max(r) - min(r) < 1e-9:
            return seq[-1] * r[0]
        d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]
        if len(set(d2)) == 1:
            return seq[-1] + d1[-1] + d2[0]
        return None
    if 'settlement period' in t:
        m = re.search(r'signed on (\d+ \w+ \d{4}) has a (\d+)-day', t)
        return dt.datetime.strptime(m.group(1), '%d %B %Y').date() + dt.timedelta(days=int(m.group(2)))
    return None

def pick(row):
    val = compute(row['question_text'])
    opts = {L: parse_opt(row['option_' + L.lower()]) for L in 'ABCD'}
    if val is None:
        return None
    if isinstance(val, dt.date):
        for L, o in opts.items():
            if o == val:
                return L
        return None
    best = min((abs(o - val), L) for L, o in opts.items() if isinstance(o, float))
    tol = max(0.06, abs(val) * 0.002)
    return best[1] if best[0] <= tol else None

def main(csv_path, out_dir, start=1, end=10**9, overwrite=False):
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8')))
    rounds = {}
    for r in rows:
        rounds.setdefault(int(r['round_id']), []).append(r)
    os.makedirs(out_dir, exist_ok=True)
    unsure = []
    for rid in sorted(rounds):
        if not (start <= rid <= end):
            continue
        path = os.path.join(out_dir, f'round-{rid:04d}.json')
        if os.path.exists(path) and not overwrite:
            continue
        ans = {}
        for r in sorted(rounds[rid], key=lambda r: int(r['q_index'])):
            L = pick(r)
            if L is None:
                unsure.append((rid, r['q_index'], r['question_text']))
                L = 'A'
            ans[f"q{int(r['q_index'])}"] = L
        json.dump({'round_id': rid, 'answers': ans}, open(path, 'w'), indent=2)
        print('wrote', path)
    for u in unsure:
        print('UNSURE', *u, file=sys.stderr)

if __name__ == '__main__':
    a = sys.argv
    main(a[1], a[2], int(a[3]) if len(a) > 3 else 1, int(a[4]) if len(a) > 4 else 10**9)

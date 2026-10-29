"""Run the MES4-MCU LTspice test benches and print the .meas results (one value per .step).
Usage: python3 run_sims.py [bench ...]   (LTspice for macOS in /Applications)"""
import glob, math, os, re, struct, subprocess, sys

LT = '/Applications/LTspice.app/Contents/MacOS/LTspice'
HERE = os.path.dirname(os.path.abspath(__file__))
BENCHES = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(HERE, '*.net')))
NUM = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'


def read_log(name):
    log = open(os.path.join(HERE, name + '.log'), 'rb').read()
    return log.decode('utf-16-le', 'replace') if log[1:2] == b'\x00' else log.decode('utf-8', 'replace')


def parse_log(txt):
    """Returns (meas, steps): meas[name] = [value per step] (one entry when not stepped), steps = ['tr=0.0001', ...]."""
    steps = [l[6:].strip() for l in txt.splitlines() if l.startswith('.step ')]
    meas, lines, i = {}, txt.splitlines(), 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^Measurement: (\w+)', l)
        if m:  # stepped block: header line, then '  <step>\t<value>\t...' rows
            vals, i = [], i + 2
            while i < len(lines) and re.match(r'^\s+\d+\s', lines[i]):
                v = lines[i].split()[1]
                vals.append(float(v) if re.fullmatch(NUM, v) else math.nan)
                i += 1
            meas[m.group(1).lower()] = vals
            continue
        m = re.match(r'^(\w+)(?::\s.*?)?=\(?(%s)(dB)?' % NUM, l)  # 'name: expr=value', 'name=value FROM..'
        if m and m.group(1).lower() not in ('tnom', 'temp', 'method', 'solver'):
            when = re.search(r'\sAT\s(%s)' % NUM, l)  # WHEN results: the crossing time / sweep value (FIND prints 'at')
            meas[m.group(1).lower()] = [float(when.group(1) if when else m.group(2))]
        m = re.match(r"^Measurement \"?(\w+)\"? FAIL'ed", l)
        if m:
            meas[m.group(1).lower()] = [math.nan]
        i += 1
    return meas, steps


def run(name):
    for ext in ('.log', '.raw', '.op.raw'):
        try:
            os.remove(os.path.join(HERE, name + ext))
        except FileNotFoundError:
            pass
    subprocess.run([LT, '-b', name + '.net'], cwd=HERE, timeout=1800, check=False)
    txt = read_log(name)
    meas, steps = parse_log(txt)
    errs = sorted({l.strip() for l in txt.splitlines()
                   if re.search(r'error|fail|singular|timestep too small', l, re.I) and 'Gmin' not in l
                   and 'Direct Newton' not in l and 'Source stepping' not in l and "FAIL'ed" not in l})
    return meas, steps, errs


def read_raw(name):
    """Columns of a binary .raw file. Stepped runs come back as a list of dicts (one per step)."""
    b = open(os.path.join(HERE, name + '.raw'), 'rb').read()
    mark = 'Binary:\n'.encode('utf-16-le')
    i = b.find(mark)
    head = b[:i].decode('utf-16-le')
    nvar = int(re.search(r'No. Variables:\s*(\d+)', head).group(1))
    npts = int(re.search(r'No. Points:\s*(\d+)', head).group(1))
    flags = re.search(r'Flags:(.*)', head).group(1)
    names = re.findall(r'^\t\d+\t(\S+)\t', head, re.M)
    data = b[i + len(mark):]
    cols = {n: [] for n in names}
    if 'complex' in flags:
        rec = 16 * nvar
        for k in range(npts):
            vals = struct.unpack_from('<%dd' % (2 * nvar), data, k * rec)
            for j, n in enumerate(names):
                cols[n].append(vals[2 * j] if j == 0 else complex(vals[2 * j], vals[2 * j + 1]))
        return cols
    dbl = 'double' in flags
    rec = 8 * nvar if dbl else 8 + 4 * (nvar - 1)
    for k in range(npts):
        off = k * rec
        cols[names[0]].append(abs(struct.unpack_from('<d', data, off)[0]))
        vals = struct.unpack_from('<%d%s' % (nvar - 1, 'd' if dbl else 'f'), data, off + 8)
        for n, v in zip(names[1:], vals):
            cols[n].append(v)
    if 'stepped' not in flags:
        return cols
    x = cols[names[0]]
    cuts = [0] + [k for k in range(1, len(x)) if x[k] < x[k - 1]] + [len(x)]
    return [{n: c[a:z] for n, c in cols.items()} for a, z in zip(cuts, cuts[1:])]


if __name__ == '__main__':
    for n in (sys.argv[1:] or BENCHES):
        meas, steps, errs = run(n)
        print('==', n, ('  steps: ' + ' | '.join(steps)) if steps else '')
        for k, v in meas.items():
            print('   %-12s %s' % (k, '  '.join('%.4g' % x for x in v)))
        for e in errs:
            print('   !', e)
        sys.stdout.flush()

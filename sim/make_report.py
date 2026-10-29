"""Build sim/report.html (inline SVG plots) from the LTspice .raw files. Run run_sims.py first."""
import html, math, os
from run_sims import read_raw, read_log, parse_log, HERE

COL = ['#185FA5', '#D85A30', '#1D9E75', '#993556']


def series(d, s):
    """'V(a,b)' = V(a) - V(b); anything else is a column of the raw file."""
    low = {k.lower(): v for k, v in d.items()}  # LTspice writes I(Dl1) for I(DL1)
    if s.lower() in low:
        return low[s.lower()]
    a, b = s[2:-1].split(',')
    return [x - y for x, y in zip(low['v(%s)' % a.lower()], low['v(%s)' % b.lower()])]


def ticklabel(x, span, unit, top=None):
    """Tick label with fixed decimals, enough to tell neighbouring ticks apart. For time axes (unit 's') the
    scale (ms / µs / ns) follows the largest value on the axis (top)."""
    k, u = 1, unit
    if unit == 's':
        m = abs(top) if top is not None else abs(x)
        k, u = (1e3, 'ms') if m >= 1e-3 else (1e6, 'µs') if m >= 1e-6 else (1e9, 'ns')
    dec = max(0, 1 - int(math.floor(math.log10(span * k / 5))))
    return ('%.*f %s' % (dec, x * k, u)).strip()


def plot(name, sigs, t0, t1, title, unit, scale=1.0, limits=(), step=None, steps=None, xunit='s'):
    """sigs on one plot. For a stepped run: step=k plots sigs of step k; steps=[labels] plots sigs[0] for every step."""
    d = read_raw(name)
    if isinstance(d, list):
        if steps is not None:
            runs = [(d[k], sigs[0], lab) for k, lab in enumerate(steps)]
        else:
            runs = [(d[step], s, s) for s in sigs]
    else:
        runs = [(d, s, s) for s in sigs]
    W, H, L, R, T, B = 640, 260, 56, 16, 28, 36
    ser = []
    lo, hi = float('inf'), float('-inf')
    for dd, s, lab in runs:
        t = dd[list(dd)[0]]
        y = series(dd, s)
        pts = [(x, v * scale) for x, v in zip(t, y) if t0 <= x <= t1]
        n = max(1, len(pts) // 350)  # keep min / max per bucket so peaks survive
        red = []
        for k in range(0, len(pts), n):
            b = pts[k:k + n]
            red += [min(b, key=lambda p: p[1]), max(b, key=lambda p: p[1])] if n > 1 else b
        red.sort()
        ser.append((lab, red))
        lo, hi = min(lo, min(p[1] for p in red)), max(hi, max(p[1] for p in red))
    for v, _ in limits:
        lo, hi = min(lo, v), max(hi, v)
    pad = (hi - lo) * 0.08 or 1
    lo, hi = lo - pad, hi + pad
    X = lambda x: L + (x - t0) / (t1 - t0) * (W - L - R)
    Y = lambda v: T + (hi - v) / (hi - lo) * (H - T - B)
    out = ['<svg viewBox="0 0 %d %d" width="100%%" role="img"><title>%s</title>' % (W, H, html.escape(title))]
    for k in range(6):
        v = lo + (hi - lo) * k / 5
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="grid"/><text x="%d" y="%.1f" class="ax" text-anchor="end">%s</text>'
                   % (L, W - R, Y(v), Y(v), L - 6, Y(v) + 4, ticklabel(v, hi - lo, '')))
    for k in range(6):
        x = t0 + (t1 - t0) * k / 5
        out.append('<text x="%.1f" y="%d" class="ax" text-anchor="middle">%s</text>' % (X(x), H - B + 16, ticklabel(x, t1 - t0, xunit, max(abs(t0), abs(t1)))))
    for v, lab in limits:
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="lim"/><text x="%d" y="%.1f" class="limt" text-anchor="end">%s</text>'
                   % (L, W - R, Y(v), Y(v), W - R - 4, Y(v) - 4, html.escape(lab)))
    lx = L
    for i, (lab, red) in enumerate(ser):
        pts = ' '.join('%.1f,%.1f' % (X(x), Y(v)) for x, v in red)
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.4"/>' % (pts, COL[i % 4]))
        out.append('<rect x="%d" y="8" width="10" height="3" fill="%s"/><text x="%d" y="13" class="lg">%s</text>'
                   % (lx, COL[i % 4], lx + 14, html.escape(lab)))
        lx += 24 + 6.2 * len(lab)
    out.append('<text x="12" y="%d" class="ax">%s</text></svg>' % (T - 6, unit))
    return '<figure><figcaption>%s</figcaption>%s</figure>' % (html.escape(title), ''.join(out))


def steps_of(name):
    return parse_log(read_log(name))[1]


if __name__ == '__main__':
    VIL, VIH = (0.99, 'VIL 0.3 × VDD'), (2.31, 'VIH 0.7 × VDD')
    figs = {
        'mdl1': plot('mdl1_tlv767_fit', ['V(out)'], 1.48e-3, 1.68e-3, 'MDL1 · U2 model, 250 → 850 mA → 250 mA at 0.8 A/µs, COUT 1 µF (TI Fig. 7-12: ≈ −120 / +100 mV)', 'V'),
        'pwr1v': plot('pwr1_powerup', ['V(v5)', 'V(v3)'], 0, 3e-3, 'PWR1 · +5V and +3V3, carrier rail ramping in 2 ms', 'V', step=1, limits=[(2.2, 'U2 UVLO 2.2 V')]),
        'pwr1i': plot('pwr1_powerup', ['I(Vjoin)', 'I(Vu2)'], 0, 1e-3, 'PWR1 · module input current and U2 input current, carrier rail ramping in 100 µs', 'A', step=0),
        'pwr2v': plot('pwr2_hotplug', ['V(f5)', 'V(v5)'], 199.5e-6, 207e-6, 'PWR2 · carrier socket (f5) and module +5V when the contact closes at 200 µs', 'V', limits=[(6.67, 'D2 VBR min 6.67 V'), (4.5, '4.5 V')]),
        'pwr2i': plot('pwr2_hotplug', ['I(S_plug)'], 199.5e-6, 203e-6, 'PWR2 · contact current (negative = into the module)', 'A'),
        'pwr3': plot('pwr3_tvs_pulse', ['V(v5)', 'V(v3)', 'V(pb2)'], 0, 16e-3, 'PWR3 · +19.4 A at 1 ms, −19.4 A at 8.5 ms (10/1000 µs)', 'V', limits=[(-0.3, 'VDD abs min −0.3 V')]),
        'pwr4l': plot('pwr4_dc_sweep', ['I(DL1)', 'I(DL2)', 'I(DL3)', 'I(DL4)'], 4.5, 5.5, 'PWR4 · LED currents vs +5V (LED2 green and LED3 white overlap)', 'mA', scale=1e3, xunit='V'),
        'pwr4v': plot('pwr4_dc_sweep', ['V(v3)', 'V(pb2)'], 3.0, 7.5, 'PWR4 · +3V3 at 148 mA and VSENSE_5V vs +5V', 'V', xunit='V', limits=[(3.0, 'U3 VCC min 3.0 V')]),
        'pwr5': plot('pwr5_3v3_load', ['V(v3)'], 0.9e-3, 3.6e-3, 'PWR5 · +3V3: CAN burst 1.0–1.5 ms, +50 mA on pin 4 at 2 ms, both off at 3 ms', 'V'),
        'bz1v': plot('bz1_buzzer_pwm', ['V(bzn)', 'V(pb7)'], 16e-3, 16.6e-3, 'BZ1 · Q3 drain and PB7 (0.3 mH coil)', 'V', step=1),
        'bz1i': plot('bz1_buzzer_pwm', ['I(Lbz)'], 7.9e-3, 19e-3, 'BZ1 · coil current for 0.1 / 0.3 / 1 mH', 'A', steps=['0.1 mH', '0.3 mH', '1 mH']),
        'bz1r': plot('bz1_buzzer_pwm', ['V(pb2)'], 6e-3, 20e-3, 'BZ1 · VSENSE_5V (PB2) while the buzzer runs, 0.3 mH', 'V', step=1),
        'mcu1': plot('mcu1_hse_clock', ['V(pc)'], 142e-9, 162e-9, 'MCU1 · PC14 rising edge with R14 = 0 Ω and 22 Ω (fast X1 corner)', 'V', steps=['R14 0 Ω', 'R14 22 Ω'], limits=[VIL, VIH]),
        'mcu2': plot('mcu2_nrst', ['V(nrst)'], 0, 30e-3, 'MCU2 · NRST for RPU 25 / 40 / 55 kΩ: power-up, 20 µs internal reset at 10 ms, 1 ms button at 20 ms', 'V', steps=['25 kΩ', '40 kΩ', '55 kΩ'], limits=[VIL, VIH]),
        'can1': plot('can1_bus_500k', ['V(ha,la)', 'V(hb,lb)', 'V(s1h,s1l)'], 0, 30e-6, 'CAN1 · differential voltage at module A, far end B and the 3 m stub (typical driver)', 'V', step=0, limits=[(0.9, 'VIT+ max 0.9 V'), (0.5, 'VIT− min 0.5 V')]),
        'can1z': plot('can1_bus_500k', ['V(ha,la)', 'V(hb,lb)', 'V(s1h,s1l)'], 14.9e-6, 15.5e-6, 'CAN1 · dominant → recessive edge at 15 µs (zoom)', 'V', step=0, limits=[(0.5, 'VIT− min 0.5 V')]),
    }
    tpl = open(os.path.join(HERE, 'report_template.html')).read()
    for k, v in figs.items():
        tpl = tpl.replace('{{%s}}' % k, v)
    open(os.path.join(HERE, 'report.html'), 'w').write(tpl)
    print('written report.html')

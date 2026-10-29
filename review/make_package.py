"""Build the review package PDF: cover.html + sim/report.html (printed to A4 by headless Chrome), then the
schematic exported fresh by kicad-cli (A3). Run sim/run_sims.py and sim/make_report.py first.
Usage: python3 make_package.py [R3]"""
import os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
KICAD = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

rev = sys.argv[1] if len(sys.argv) > 1 else 'R3'
report = open(os.path.join(ROOT, 'sim', 'report.html'), encoding='utf-8').read()
cover = open(os.path.join(HERE, 'cover.html'), encoding='utf-8').read()
style = re.search(r'<style>.*?</style>', report, re.S).group(0)
body = re.search(r'<main>(.*)</main>', report, re.S).group(1)
html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>MES4-MCU review package %s</title>\n%s</head><body><main>\n%s\n'
        '<section class="pb">%s</section>\n</main></body></html>\n') % (rev, style, cover, body)
open(os.path.join(HERE, 'review_package.html'), 'w', encoding='utf-8').write(html)

with tempfile.TemporaryDirectory() as tmp:
    text_pdf, sch_pdf = os.path.join(tmp, 'report.pdf'), os.path.join(tmp, 'schematic.pdf')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    '--print-to-pdf=' + text_pdf, 'file://' + os.path.join(HERE, 'review_package.html')],
                   check=True, capture_output=True)
    subprocess.run([KICAD, 'sch', 'export', 'pdf', '-o', sch_pdf, os.path.join(ROOT, 'MES4-MCU.kicad_sch')],
                   check=True, capture_output=True)
    out = os.path.join(HERE, 'MES4-MCU_Review-Package_%s.pdf' % rev)
    subprocess.run(['pdfunite', text_pdf, sch_pdf, out], check=True, capture_output=True)  # poppler warns about KiCad's links
print('written', os.path.relpath(out, ROOT))

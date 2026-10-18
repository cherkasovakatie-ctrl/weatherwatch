"""Write short keyword excerpts (not full texts) of downloaded papers to probe/ for review."""
import glob, os, re, subprocess
KW = {
  'wwb': r'1982|May|burst|westerl|Kelvin|30.?60|40.?50|intraseasonal|cyclone|surge|cross.?equatorial|El Ni',
  'io': r'1982|decoupl|IOD|dipole|feedback|initiat|onset|lead|prior|precede|persist|terminat|transition|experiment',
}
os.makedirs('probe', exist_ok=True)
for f in sorted(glob.glob('fulltext/*')):
    name = os.path.basename(f).rsplit('.', 1)[0]
    if f.endswith('.pdf'):
        subprocess.run(['pdftotext', f, f'/tmp/{name}.txt']); txt = open(f'/tmp/{name}.txt', errors='ignore').read()
    else:
        txt = open(f, errors='ignore').read()
        if f.endswith(('.xml', '.html')): txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = re.sub(r'[ \t]+', ' ', txt)
    sents = re.split(r'(?<=[.!?])\s+', txt.replace('\n', ' '))
    kw = KW['io'] if name.startswith('io_') else KW['wwb']
    if name.startswith('mjo_'): kw = r'1982|1981|ENSO|El Ni|two-way|Kelvin|westerly|propagat'
    hits = [s.strip() for s in sents if re.search(kw, s) and len(s) < 600 and ('1982' in s or name.startswith('io_') or (name.startswith('mjo_') and re.search(r'ENSO|El Ni', s)))]
    if name.startswith('io_'): hits = [s for s in hits if re.search(r'1982|decoupl|experiment|feedback onto|Pacific', s)]
    s82 = [x.strip() for x in sents if '1982' in x and len(x) < 700]
    head = ' '.join(txt.split()[:700 if name.startswith('wwb_chu') else 350])
    open(f'probe/excerpt_{name}.txt', 'w').write(f'words: {len(txt.split())}\nOPENING (first 350 words):\n{head}\n\nKEY SENTENCES ({len(hits)}; first 60):\n' + '\n- '.join([''] + hits[:60]) + f'\n\nALL SENTENCES WITH 1982 ({len(s82)}; first 40):' + '\n- '.join([''] + s82[:40]))
print('excerpts done')

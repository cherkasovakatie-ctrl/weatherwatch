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
    hits = [s.strip() for s in sents if re.search(kw, s) and len(s) < 600 and ('1982' in s or name.startswith('io_'))]
    if name.startswith('io_'): hits = [s for s in hits if re.search(r'1982|decoupl|experiment|feedback onto|Pacific', s)]
    head = ' '.join(txt.split()[:350])
    open(f'probe/excerpt_{name}.txt', 'w').write(f'words: {len(txt.split())}\nOPENING (first 350 words):\n{head}\n\nKEY SENTENCES ({len(hits)}; first 60):\n' + '\n- '.join([''] + hits[:60]))
print('excerpts done')

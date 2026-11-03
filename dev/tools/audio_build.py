"""Proto 3 : prépare les sons générés (ElevenLabs) pour le jeu.

Usage : python3 audio_build.py <dossier des mp3 générés>
Sorties : ../game/audio/*.mp3 (bruitages mono 48 kb/s, musique stéréo 112 kb/s) et ../game/audio5.js (manifeste AUDIO5).
- bruitages : silence de tête coupé, crête à −2 dB, queue coupée sous −50 dB avec un fondu de 20 ms ; variantes groupées par nom
- boucles : tempo mesuré, coupe sur le temps fort au plus près du début, longueur = un multiple de 4 mesures, fondu de 30 ms à la jointure (lecture Web Audio en boucle)
- jingles et fins : queue de silence coupée, niveau RMS aligné
- sons musicaux (pièce, cercle, girouette) : hauteur dominante mesurée, taux de lecture pour tomber sur une note de do majeur (le jeu monte ensuite la gamme)
"""
import glob, json, os, re, subprocess, sys
import numpy as np

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'game', 'audio'); os.makedirs(OUT, exist_ok=True)
SR = 44100

def load(f, mono=True):
    raw = subprocess.run(['ffmpeg', '-v', 'quiet', '-i', f, '-ac', '1' if mono else '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return x if mono else x.reshape(-1, 2)

def save(x, path, mono, kbps):
    ch = 1 if mono else 2
    raw = (x if mono else x.reshape(-1)).astype(np.float32).tobytes()
    subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', '-', '-codec:a', 'libmp3lame', '-b:a', f'{kbps}k', path], input=raw, check=True)

def trim_sfx(x):
    pk = np.abs(x).max() or 1
    on = int(np.argmax(np.abs(x) > pk*0.03)); on = max(0, on - int(0.002*SR))
    env = np.convolve(np.abs(x), np.ones(int(0.01*SR))/int(0.01*SR), 'same')
    off = len(x) - int(np.argmax(env[::-1] > pk*0.003)); off = min(len(x), off + int(0.03*SR))
    y = x[on:off].copy(); n = min(len(y), int(0.02*SR)); y[-n:] *= np.linspace(1, 0, n); y[:int(0.001*SR)] *= np.linspace(0, 1, int(0.001*SR))
    return y * (10**(-2/20)/pk)

def dominant_hz(x):
    w = x[:int(0.12*SR)] * np.hanning(min(len(x), int(0.12*SR)))
    sp = np.abs(np.fft.rfft(w, 1 << 16)); fr = np.fft.rfftfreq(1 << 16, 1/SR); sp[fr < 150] = 0; sp[fr > 6000] = 0
    return float(fr[np.argmax(sp)])

def tempo_and_phase(x, force=None):
    """tempo précis : autocorrélation de l'enveloppe d'attaques (pas de 64 échantillons) sur la longueur de quatre mesures ; phase du temps fort sur les graves"""
    hop = 64; n = len(x)//hop; e = np.sqrt((x[:n*hop].reshape(n, hop)**2).mean(1)); d = np.maximum(0, np.diff(e)); d -= d.mean(); fps = SR/hop
    ac = np.correlate(d, d, 'full')[len(d) - 1:]
    # estimation grossière du tempo (un temps), puis affinage sur quatre mesures autour de cette valeur (± 6 %)
    coarse = force or max(((ac[int(round(60/b*fps))] + 0.5*ac[min(len(ac) - 1, 2*int(round(60/b*fps)))], b) for b in np.arange(85, 165, 0.5)))[1]
    lo, hi = (int(960/(coarse*1.01)*fps), int(960/(coarse*0.99)*fps)) if force else (int(960/(coarse*1.06)*fps), int(960/(coarse*0.94)*fps))
    lag = lo + int(np.argmax(ac[lo:hi])); bpm = 960/(lag/fps); beat = 60/bpm
    per = beat*fps; best_ph = max(((d[np.arange(int(ph), len(d), int(round(per)))].sum(), ph) for ph in range(0, int(round(per)), 4)))[1]
    t0 = best_ph/fps
    low = np.convolve(x, np.ones(64)/64, 'same'); nl = len(low)//hop; el = np.sqrt((low[:nl*hop].reshape(nl, hop)**2).mean(1)); dl = np.maximum(0, np.diff(el))
    def score(k): idx = (np.arange(t0 + k*beat, len(x)/SR, 4*beat)*fps).astype(int); idx = idx[idx < len(dl)]; return dl[idx].sum()
    k = max(range(4), key=score)
    return bpm, t0 + k*beat

FORCE_BPM = {'mus_course': 120.0}   # quand la mesure automatique se trompe (course : charleston en doubles croches)
def make_loop(x2, name=None):   # x2 stéréo
    mono = x2.mean(1); bpm, bar0 = tempo_and_phase(mono, FORCE_BPM.get(name)); beat = 60/bpm; bar = 4*beat
    pk = np.abs(mono).max(); env = np.convolve(np.abs(mono), np.ones(int(0.05*SR))/int(0.05*SR), 'same'); useful = (len(mono) - np.argmax(env[::-1] > pk*0.02))/SR
    start = bar0 if bar0 >= 0.04 else bar0 + bar
    nbars = int((useful - start - 0.05)//bar); nbars -= nbars % 4
    if nbars < 4: nbars = int((useful - start - 0.05)//bar)
    L = nbars*bar; s = int(start*SR); n = int(round(L*SR)); fade = int(0.03*SR)
    y = x2[s:s + n].copy(); pre = x2[max(0, s - fade):s]
    if len(pre) == fade: w = np.linspace(0, 1, fade)[:, None]; y[-fade:] = y[-fade:]*(1 - w) + pre*w
    rms = np.sqrt((y**2).mean()); y *= 10**(-16/20)/rms; pkk = np.abs(y).max()
    if pkk > 0.85: y *= 0.85/pkk   # marge pour le dépassement du mp3
    return y, bpm, nbars, L

def level(x2, target_db):
    rms = np.sqrt((x2**2).mean()); y = x2*10**(target_db/20)/rms; pk = np.abs(y).max()
    return y*(0.85/pk) if pk > 0.85 else y

def trim_tail(x2):
    mono = np.abs(x2).mean(1); pk = mono.max(); env = np.convolve(mono, np.ones(int(0.02*SR))/int(0.02*SR), 'same')
    off = len(mono) - int(np.argmax(env[::-1] > pk*0.004)); off = min(len(mono), off + int(0.25*SR)); y = x2[:off].copy(); n = min(len(y), int(0.12*SR)); y[-n:] *= np.linspace(1, 0, n)[:, None]
    return y

PICK = {'mus_vol': 1, 'mus_vol_b': 1, 'mus_course': 1, 'mus_tempete': 1, 'mus_menu': 1, 'mus_qg': 1}   # variante retenue par boucle
TONAL = {'sfx_coin', 'sfx_ring', 'sfx_grab', 'sfx_orb', 'sfx_tick', 'sfx_cash'}
CMAJ = [0, 2, 4, 5, 7, 9, 11]
man = {'sfx': {}, 'amb': {}, 'music': {}, 'sting': {}}
files = sorted(glob.glob(os.path.join(SRC, '*.mp3')))
for f in files:
    b = os.path.basename(f)[:-4]
    m = re.match(r'(sfx_[a-z_]+?|amb_[a-z0-9]+)_v2_v(\d)$', b)
    if m:
        name, v = m.group(1), int(m.group(2)); x = load(f)
        if name.startswith('amb'):
            y = x*(10**(-18/20)/np.sqrt((x**2).mean())); pk = np.abs(y).max(); y = y*(0.9/pk) if pk > 0.9 else y
            out = f'{name}.mp3'; save(y, os.path.join(OUT, out), True, 64); man['amb'][name] = out; continue
        y = trim_sfx(x); out = f'{name}_{v}.mp3'; save(y, os.path.join(OUT, out), True, 48)
        e = man['sfx'].setdefault(name, {'files': [], 'rate': 1})
        e['files'].append(out)
        if name in TONAL and v == 1:
            hz = dominant_hz(y); midi = 69 + 12*np.log2(hz/440); base = round(midi);
            cands = [n for n in range(base - 6, base + 7) if n % 12 in CMAJ]; tgt = min(cands, key=lambda n: abs(n - midi))
            e['rate'] = round(float(2**((tgt - midi)/12)), 4); e['hz'] = round(hz)
        continue
    m = re.match(r'(mus_[a-z0-9_]+?)_music_v1_v(\d)$', b)
    if m:
        name, v = m.group(1), int(m.group(2))
        if PICK.get(name, 1) != v: continue
        y, bpm, nbars, L = make_loop(load(f, False), name); out = f'{name}.mp3'; save(y, os.path.join(OUT, out), False, 112)
        man['music'][name] = {'file': out, 'bpm': round(bpm, 1), 'bars': nbars, 'len': round(L, 3)}; print(f'{name}: {bpm:.1f} BPM, {nbars} mesures, {L:.2f} s'); continue
    m = re.match(r'((?:sting|fin)_[a-z]+)_music_v1_v1$', b)
    if m:
        name = m.group(1); y = level(trim_tail(load(f, False)), -14); out = f'{name}.mp3'; save(y, os.path.join(OUT, out), False, 96); man['sting'][name] = out; continue
for k, e in man['sfx'].items(): e['files'].sort()
open(os.path.join(HERE, '..', 'game', 'audio5.js'), 'w').write('const AUDIO5 = ' + json.dumps(man, ensure_ascii=False) + ';\n')
tot = sum(os.path.getsize(os.path.join(OUT, p)) for p in os.listdir(OUT))
print(len(os.listdir(OUT)), 'fichiers,', round(tot/1e6, 2), 'MB'); print({k: (v.get('hz'), v['rate']) for k, v in man['sfx'].items() if 'hz' in v})

"""Варианты фоновой музыки для ролика Ordo, синтез кодом.
  python3 music_variants.py samples        → build/music_<стиль>.mp3 по 30 с каждого стиля
  python3 music_variants.py <стиль> <дл,с>  → music_ordo.wav целиком (его берет make.js)
Стили: tech (тех-минимал), ambient (спокойный эмбиент), drive (корпоративный драйв), lofi (лоу-фай).
"""
import sys, wave, subprocess
import numpy as np

SR = 44100
rng = np.random.default_rng(5)

def tt(d): return np.arange(int(SR * d)) / SR
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def soft_saw(f, t, k=6, roll=1.8): return sum(np.sin(2 * np.pi * f * h * t) / h ** roll for h in range(1, k + 1))
def hp_noise(d, w):
    nz = rng.standard_normal(int(SR * d)); return nz - np.convolve(nz, np.ones(w) / w, mode='same')

def kick(depth=90, low=42, dec=7):
    t = tt(.4); f = depth * np.exp(-t * 22) + low
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * dec)
def clap(): t = tt(.18); return hp_noise(.18, 12) * np.exp(-t * 22) * .45
def snare_soft(): t = tt(.22); return (hp_noise(.22, 20) * .5 + np.sin(2 * np.pi * 190 * t) * .4) * np.exp(-t * 16)
def hat(): t = tt(.04); return hp_noise(.04, 3) * np.exp(-t * 110) * .35
def bass(n, d, dec=6): t = tt(d); return soft_saw(hz(n), t, 5, 1.8) * np.minimum(1, t / .008) * np.exp(-t * dec)
def pad(notes, d, roll=2.0):
    t = tt(d); x = sum(soft_saw(hz(n), t, 6, roll) for n in notes) / len(notes)
    return x * np.minimum(1, t / .5) * np.minimum(1, (d - t) / .5)
def piano(n, d=1.6, dec=2.2):
    t = tt(d); f = hz(n)
    x = np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3) + .12 * np.sin(6 * np.pi * f * t) * np.exp(-t * 6)
    return x * np.minimum(1, t / .004) * np.exp(-t * dec)
def rhodes(notes, d=1.2):  # «бархатные» аккорды: синус + колокольчатый обертон, медленное затухание, легкое тремоло
    t = tt(d); x = 0
    for n in notes:
        f = hz(n); x = x + np.sin(2 * np.pi * f * t) * np.exp(-t * 2.5) + .2 * np.sin(2 * np.pi * f * 7 * t) * np.exp(-t * 14)
    return x / len(notes) * (1 + .08 * np.sin(2 * np.pi * 4.5 * t)) * np.minimum(1, t / .006)

def render(style, dur):
    N = int(SR * dur); out = {k: np.zeros(N) for k in ('dr', 'bs', 'pd', 'ky')}
    def add(k, x, at, g=1.0):
        i = int(at * SR)
        if 0 <= i < N: x = x[: N - i]; out[k][i:i + len(x)] += x * g
    pump = None
    if style == 'tech':      # 98 BPM, Am–F–C–G, бас восьмыми, «дышащая» подложка, ровный бит
        bpm = 98; B = 60 / bpm; BAR = 4 * B
        CH = [([57, 60, 64], 45), ([53, 57, 60], 41), ([48, 52, 55], 36), ([55, 59, 62], 43)]; TOP = [76, 72, 72, 74]
        for b in range(int(dur / BAR) + 1):
            t0 = b * BAR; notes, root = CH[b % 4]; on = b >= 4
            add('pd', pad(notes, BAR), t0, .5)
            for e in range(8): add('bs', bass(root - (12 if e % 2 == 0 else 0), B / 2), t0 + e * B / 2, .5 if on else .3)
            if b >= 2 and b % 2 == 0: add('ky', piano(TOP[b % 4]), t0, .35)
            if on:
                for q in range(4):
                    add('dr', kick(), t0 + q * B, .7)
                    if q in (1, 3): add('dr', clap(), t0 + q * B, .3)
                    for s in (.25, .5, .75): add('dr', hat(), t0 + (q + s) * B, .1 if s == .5 else .05)
        ph = (np.arange(N) / SR % B) / B; pump = .55 + .45 * np.minimum(1, ph / .45)
    elif style == 'ambient': # 76 BPM, без барабанов: широкая подложка и медленное пианино по аккорду, Dmaj7–Bm7–Gmaj7–A
        bpm = 76; B = 60 / bpm; BAR = 4 * B
        CH = [([62, 66, 69, 73], 50), ([59, 62, 66, 69], 47), ([55, 59, 62, 66], 43), ([57, 61, 64, 69], 45)]
        for b in range(int(dur / BAR) + 1):
            t0 = b * BAR; notes, root = CH[b % 4]
            add('pd', pad(notes, BAR * 1.05, 2.4), t0, .55)
            add('bs', bass(root - 12, BAR, 1.2), t0, .35)
            for k, n in enumerate([notes[0] + 12, notes[2] + 12, notes[1] + 12, notes[3] + 12]):
                add('ky', piano(n, 2.4, 1.6), t0 + k * B, .3 if b >= 1 else .15)
    elif style == 'drive':   # 112 BPM, D–A–Bm–G, пианино аккордами восьмыми, бочка на каждую долю, хлопки
        bpm = 112; B = 60 / bpm; BAR = 4 * B
        CH = [([62, 66, 69], 50), ([61, 64, 69], 45), ([62, 66, 71], 47), ([62, 67, 71], 43)]
        for b in range(int(dur / BAR) + 1):
            t0 = b * BAR; notes, root = CH[b % 4]; on = b >= 2
            add('pd', pad(notes, BAR, 2.2), t0, .3)
            for e in range(8):
                acc = e in (0, 3, 6)
                add('ky', sum(piano(n, .5, 7) for n in notes) / 3, t0 + e * B / 2, .5 if acc else .28)
            for e in (0, 1.5, 2, 3.5): add('bs', bass(root - 12, B * .9, 4), t0 + e * B, .55)
            if on:
                for q in range(4):
                    add('dr', kick(100, 45, 8), t0 + q * B, .75)
                    if q in (1, 3): add('dr', clap(), t0 + q * B, .4)
                    add('dr', hat(), t0 + (q + .5) * B, .14)
    elif style == 'lofi':    # 84 BPM с раскачкой, Am7–Dm7–G7–Cmaj7, мягкая бочка и малый, бархатные аккорды
        bpm = 84; B = 60 / bpm; BAR = 4 * B; sw = .08 * B
        CH = [([57, 60, 64, 67], 45), ([50, 53, 57, 60], 38), ([55, 59, 62, 65], 43), ([48, 52, 55, 59], 36)]
        for b in range(int(dur / BAR) + 1):
            t0 = b * BAR; notes, root = CH[b % 4]; on = b >= 2
            add('ky', rhodes([n + 12 for n in notes], BAR * .6), t0, .55)
            add('ky', rhodes([n + 12 for n in notes], B * 1.2), t0 + B * 2.5 + sw, .35)
            add('bs', bass(root - 12, B * 1.5, 2.5), t0, .5); add('bs', bass(root - 12, B, 3), t0 + B * 2.5 + sw, .35)
            if on:
                for q in range(4):
                    if q in (0, 2): add('dr', kick(70, 40, 9), t0 + q * B + (sw if q == 2 else 0), .6)
                    if q in (1, 3): add('dr', snare_soft(), t0 + q * B, .32)
                    add('dr', hat(), t0 + q * B, .08); add('dr', hat(), t0 + (q + .5) * B + sw, .06)
    else:
        raise SystemExit('нет стиля ' + style)
    p = pump if pump is not None else 1
    mix = out['dr'] + out['bs'] * p + out['pd'] * p + out['ky']
    fi, fo = int(SR * 1.5), int(SR * 2.5)
    mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    mix /= np.sqrt(np.mean(mix ** 2)) / 10 ** (-18 / 20)
    return np.clip(mix, -.98, .98)

def save(x, path):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())

NAMES = {'tech': '1-тех-минимал', 'ambient': '2-эмбиент', 'drive': '3-драйв', 'lofi': '4-лоу-фай'}
if sys.argv[1] == 'samples':
    for st, nm in NAMES.items():
        save(render(st, 30), f'build/_s.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'build/_s.wav', '-b:a', '128k', f'build/Музыка {nm}.mp3'], check=True)
        print('ok', nm)
else:
    save(render(sys.argv[1], float(sys.argv[2])), 'music_ordo.wav'); print('music_ordo.wav', sys.argv[1])

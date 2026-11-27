"""Фоновая музыка ролика Ordo: светлая и бодрая, без органных подкладок и длинного эха.
104 BPM, до мажор, I–vi–IV–V (C–Am–F–G). Вступление без барабанов, дальше мягкий бит, клавишные на слабые доли
и звонкое арпеджио. Запуск: python3 music_ordo.py [длительность, с] → music_ordo.wav
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 104
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 116.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

def tt(d): return np.arange(int(SR * d)) / SR
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def add(dst, x, at, g=1.0):
    i = int(at * SR)
    if 0 <= i < N:
        x = x[: N - i]; dst[i:i + len(x)] += x * g
def lowpass(x, a):  # однополюсный фильтр, a – доля нового сэмпла
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y

# инструменты
def kick():
    t = tt(.32); f = 110 * np.exp(-t * 28) + 48
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
def snap():
    t = tt(.16); nz = rng.standard_normal(len(t))
    return (nz - lowpass(nz, .08)) * np.exp(-t * 30) * .6
def hat():
    t = tt(.05); nz = rng.standard_normal(len(t))
    return (nz - lowpass(nz, .35)) * np.exp(-t * 90) * .5
def bass(n, d):
    t = tt(d); f = hz(n)
    x = np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)
    return x * np.minimum(1, t / .01) * np.exp(-t * 2.2)
def epiano(notes, d=.45):  # мягкий «рояль-электро»: синус + немного обертона, быстрое затухание
    t = tt(d); x = 0
    for n in notes:
        f = hz(n); x = x + np.sin(2 * np.pi * f * t) * np.exp(-t * 5) + .3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 9)
    return x / len(notes) * np.minimum(1, t / .005)
def mallet(n, d=.3):  # звонкое арпеджио, как маримба
    t = tt(d); f = hz(n)
    return (np.sin(2 * np.pi * f * t) + .2 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)) * np.exp(-t * 11)
def pad(notes, d):  # тихая подложка из синусов, без детюна
    t = tt(d); x = sum(np.sin(2 * np.pi * hz(n) * t) for n in notes) / len(notes)
    return x * np.minimum(1, t / .6) * np.minimum(1, (d - t) / .6)

CH = [([60, 64, 67], 48), ([57, 60, 64], 45), ([53, 57, 60], 41), ([55, 59, 62], 43)]  # C Am F G
drums, bs, keys, arp, pd = (np.zeros(N) for _ in range(5))
bars = int(DUR / BAR) + 1
for b in range(bars):
    t0 = b * BAR; notes, root = CH[b % 4]
    full = b >= 4                     # первые 4 такта – вступление без барабанов
    add(pd, pad(notes, BAR), t0, .18)
    add(bs, bass(root, BEAT * 1.4), t0, .55 if full else .3)
    add(bs, bass(root, BEAT), t0 + BEAT * 2.5, .45 if full else .25)
    for off in (1.5, 3.5):            # клавишные на «и» второй и четвертой доли
        add(keys, epiano([n + 12 for n in notes]), t0 + BEAT * off, .55)
    seq = [notes[0], notes[1], notes[2], notes[1] + 12, notes[2], notes[1], notes[0] + 12, notes[2]]
    for k, n in enumerate(seq):
        add(arp, mallet(n + 12), t0 + k * BEAT / 2, .22 if b >= 2 else .12)
    if full:
        for q in range(4):
            if q in (0, 2): add(drums, kick(), t0 + q * BEAT, .8)
            if q in (1, 3): add(drums, snap(), t0 + q * BEAT, .35)
            for e in (0, .5): add(drums, hat(), t0 + (q + e) * BEAT, .12 if e else .06)

mix = drums + bs + keys + arp + pd
d = int(SR * .27); mix[d:] += .18 * arp[:-d]          # короткая задержка на арпеджио вместо зала
fade_in, fade_out = int(SR * 1.5), int(SR * 3)
mix[:fade_in] *= np.linspace(0, 1, fade_in); mix[-fade_out:] *= np.linspace(1, 0, fade_out)
mix /= np.sqrt(np.mean(mix ** 2)) / 10 ** (-18 / 20)    # громкость около −18 dBFS
mix = np.clip(mix, -.98, .98)
with wave.open('music_ordo.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('music_ordo.wav', round(DUR, 1), 'с')

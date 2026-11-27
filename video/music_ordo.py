"""Фоновая музыка ролика Ordo – спокойная технологичная электроника, как в продуктовых роликах.
98 BPM, ля минор с подъемом: Am–F–C–G. Пульсирующий бас восьмыми, теплая приглушенная подложка, которая «дышит»
в такт бочке, ровный мягкий бит, редкие ноты пианино. Без маримбы, органа и длинного эха.
Запуск: python3 music_ordo.py [длительность, с] → music_ordo.wav
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 98
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 116.0
N = int(SR * DUR)
rng = np.random.default_rng(11)

def tt(d): return np.arange(int(SR * d)) / SR
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def add(dst, x, at, g=1.0):
    i = int(at * SR)
    if 0 <= i < N:
        x = x[: N - i]; dst[i:i + len(x)] += x * g
def soft_saw(f, t, k=7, roll=1.6):  # «пила» из гармоник с сильным спадом – звучит приглушенно, без резкости
    return sum(np.sin(2 * np.pi * f * h * t) / h ** roll for h in range(1, k + 1))
def hp_noise(d, smooth):  # шум без низа: разница с сглаженной копией
    nz = rng.standard_normal(int(SR * d)); w = max(1, int(smooth))
    return nz - np.convolve(nz, np.ones(w) / w, mode='same')

# инструменты
def kick():
    t = tt(.4); f = 90 * np.exp(-t * 22) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
def clap():
    t = tt(.18); return hp_noise(.18, 12) * np.exp(-t * 22) * .45
def hat():
    t = tt(.04); return hp_noise(.04, 3) * np.exp(-t * 110) * .35
def bass(n, d):
    t = tt(d); return soft_saw(hz(n), t, 5, 1.8) * np.minimum(1, t / .008) * np.exp(-t * 6)
def pad(notes, d):
    t = tt(d); x = sum(soft_saw(hz(n), t, 6, 2.0) for n in notes) / len(notes)
    return x * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .4)
def piano(n, d=1.6):
    t = tt(d); f = hz(n)
    x = np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3) + .12 * np.sin(6 * np.pi * f * t) * np.exp(-t * 6)
    return x * np.minimum(1, t / .004) * np.exp(-t * 2.2)

CH = [([57, 60, 64], 45), ([53, 57, 60], 41), ([48, 52, 55], 36), ([55, 59, 62], 43)]  # Am F C G
TOP = [76, 72, 72, 74]                                                                     # мелодия пианино по тактам
drums, bs, pd, pn = (np.zeros(N) for _ in range(4))
bars = int(DUR / BAR) + 1
for b in range(bars):
    t0 = b * BAR; notes, root = CH[b % 4]
    beat_on = b >= 4                         # 4 такта вступления без барабанов
    add(pd, pad(notes, BAR), t0, .5)
    for e in range(8):                       # бас восьмыми, на сильной доле – октава ниже
        add(bs, bass(root - (12 if e % 2 == 0 else 0), BEAT / 2), t0 + e * BEAT / 2, .5 if beat_on else .3)
    if b >= 2 and b % 2 == 0:                # редкие ноты пианино – раз в два такта
        add(pn, piano(TOP[b % 4]), t0, .35); add(pn, piano(TOP[b % 4] - 5), t0 + BEAT * 2, .22)
    if beat_on:
        for q in range(4):
            add(drums, kick(), t0 + q * BEAT, .7)
            if q in (1, 3): add(drums, clap(), t0 + q * BEAT, .3)
            for s in (.25, .5, .75): add(drums, hat(), t0 + (q + s) * BEAT, .1 if s == .5 else .05)

# «дыхание» подложки: проседает на каждую долю, как сайдчейн
ph = (np.arange(N) / SR % BEAT) / BEAT
pump = .55 + .45 * np.minimum(1, ph / .45)
mix = drums + bs * pump + pd * pump + pn
fade_in, fade_out = int(SR * 2), int(SR * 3)
mix[:fade_in] *= np.linspace(0, 1, fade_in); mix[-fade_out:] *= np.linspace(1, 0, fade_out)
mix /= np.sqrt(np.mean(mix ** 2)) / 10 ** (-18 / 20)   # громкость около −18 dBFS
mix = np.clip(mix, -.98, .98)
with wave.open('music_ordo.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('music_ordo.wav', round(DUR, 1), 'с')

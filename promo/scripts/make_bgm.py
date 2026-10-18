#!/usr/bin/env python3
"""Make the original 38 s soundtrack for the OTIA Café student promo.

No samples, no external tracks: everything below is synthesised with numpy
(piano-ish felt keys, warm pad, upright bass, brushed kit, vinyl crackle).
The arrangement is cut to the film's scene changes:

    0.0 s  intro        pad + sparse piano, no drums
    5.3 s  home         kick / brush / bass enter
   10.7 s  menu         melody enters
   18.7 s  checkout     clap + a little more air
   32.0 s  pickup end   drums stop, piano takes over
   34.7 s  outro        final Fmaj9, tail fades to 38.0 s

Run:
    python3 scripts/make_bgm.py
    ffmpeg -y -i src/assets/audio/otia-bgm.wav \\
      -af loudnorm=I=-18:TP=-1.5:LRA=9 -ar 48000 -ac 2 \\
      -codec:a libmp3lame -b:a 192k src/assets/audio/otia-bgm.mp3
"""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

SR = 48_000
DUR = 38.0
N = int(SR * DUR)
BPM = 90.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "assets" / "audio" / "otia-bgm.wav"

rng = np.random.default_rng(20261018)

# Note frequencies used by the arrangement.
NOTE = {
    "F1": 43.65, "F2": 87.31, "F3": 174.61, "F4": 349.23, "F5": 698.46,
    "D2": 73.42, "D3": 146.83, "D4": 293.66, "D5": 587.33,
    "Bb1": 58.27, "Bb2": 116.54, "Bb3": 233.08, "Bb4": 466.16,
    "C2": 65.41, "C3": 130.81, "C4": 261.63, "C5": 523.25,
    "A3": 220.0, "A4": 440.0, "A5": 880.0,
    "E4": 329.63, "E5": 659.25,
    "G4": 392.0, "G5": 783.99,
}


def fft_filter(x: np.ndarray, kind: str, cutoff: float, order: int = 2) -> np.ndarray:
    """Gentle FFT low/high pass, enough for a soft felt-piano mix."""
    n = x.size
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    ratio = np.maximum(freqs, 1e-9) / cutoff
    if kind == "low":
        h = 1.0 / (1.0 + ratio ** (2 * order))
    else:
        h = ratio ** (2 * order) / (1.0 + ratio ** (2 * order))
    return np.fft.irfft(spec * h, n)


def add(buf: np.ndarray, sig: np.ndarray, start: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Add a mono signal into a stereo buffer with equal-power panning."""
    i = int(start * SR)
    if i >= N or i < 0:
        return
    m = min(sig.size, N - i)
    if m <= 0:
        return
    left = math.cos((pan + 1) * math.pi / 4)
    right = math.sin((pan + 1) * math.pi / 4)
    buf[i:i + m, 0] += sig[:m] * gain * left
    buf[i:i + m, 1] += sig[:m] * gain * right


def release_tail(sig: np.ndarray, seconds: float = 0.06) -> np.ndarray:
    """Ramp a note to zero so its buffer edge never clicks."""
    k = min(sig.size, int(seconds * SR))
    if k > 0:
        sig[-k:] *= np.linspace(1.0, 0.0, k) ** 1.4
    return sig


def piano(freq: float, dur: float, vel: float = 1.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for h, amp in enumerate((1.0, 0.48, 0.26, 0.14, 0.08, 0.04), start=1):
        detune = 1 + (h - 1) * 0.00035
        phase = rng.uniform(0, math.tau)
        sig += amp * np.sin(math.tau * freq * h * detune * t + phase) * np.exp(-t * (2.7 + 0.55 * h))
    # A soft hammer and the body of the instrument.
    sig *= np.minimum(1.0, t / 0.006)
    sig += 0.11 * np.sin(math.tau * freq * 0.5 * t) * np.exp(-t * 2.8)
    sig = fft_filter(sig, "low", 7000)
    return release_tail(sig * vel * 0.19, 0.09)


def pad(freqs: list[float], dur: float, vel: float = 1.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for f in freqs:
        for detune, phase, amp in ((-0.0035, 0.4, 0.55), (0.0, 1.3, 1.0), (0.0035, 2.4, 0.55)):
            sig += amp * np.sin(math.tau * f * (1 + detune) * t + phase)
    sig = fft_filter(sig, "low", 1500)
    attack = 1 - np.exp(-t / 0.85)
    release = np.ones(n)
    tail = min(n, int(1.3 * SR))
    release[-tail:] = np.linspace(1.0, 0.0, tail) ** 2
    return release_tail(sig * attack * release * vel * 0.022, 0.12)


def bass(freq: float, dur: float, vel: float = 1.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (
        np.sin(math.tau * freq * t)
        + 0.22 * np.sin(math.tau * freq * 2 * t)
        + 0.07 * np.sin(math.tau * freq * 3 * t)
    )
    env = np.minimum(1.0, t / 0.008) * np.exp(-t / 1.15)
    return release_tail(sig * env * vel * 0.092, 0.1)


def pluck(freq: float, dur: float, vel: float = 1.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (
        np.sin(math.tau * freq * t)
        + 0.36 * np.sin(math.tau * freq * 2.01 * t)
        + 0.14 * np.sin(math.tau * freq * 3.02 * t)
    )
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.5)
    return release_tail(sig * env * vel * 0.105, 0.12)


def bell(freq: float, dur: float, vel: float = 1.0) -> np.ndarray:
    """A soft music-box octave doubling for presence."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (
        np.sin(math.tau * freq * t)
        + 0.32 * np.sin(math.tau * freq * 2.01 * t + 0.4)
        + 0.13 * np.sin(math.tau * freq * 3.02 * t + 1.1)
    )
    sig = fft_filter(sig, "low", 9000)
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.85)
    return release_tail(sig * env * vel * 0.055, 0.15)


def kick(vel: float = 1.0) -> np.ndarray:
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    freq = 48 + 100 * np.exp(-t * 24)
    phase = math.tau * np.cumsum(freq) / SR
    env = np.minimum(1.0, t / 0.002) * np.exp(-t * 8.5)
    return release_tail(np.sin(phase) * env * vel * 0.14, 0.04)


def brush(vel: float = 1.0) -> np.ndarray:
    n = int(0.38 * SR)
    t = np.arange(n) / SR
    noise = fft_filter(rng.standard_normal(n), "high", 1100)
    noise = fft_filter(noise, "low", 6200)
    env = np.minimum(1.0, t / 0.006) * np.exp(-t * 15)
    return release_tail(noise * env * vel * 0.05, 0.03)


def hat(vel: float = 1.0) -> np.ndarray:
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    noise = fft_filter(rng.standard_normal(n), "high", 6000)
    noise = fft_filter(noise, "low", 11000)
    env = np.minimum(1.0, t / 0.002) * np.exp(-t * 38)
    return release_tail(noise * env * vel * 0.02, 0.02)


def clap(vel: float = 1.0) -> np.ndarray:
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    noise = fft_filter(rng.standard_normal(n), "low", 4200)
    noise = fft_filter(noise, "high", 900)
    env = np.zeros(n)
    for offset, amp in ((0.0, 1.0), (0.012, 0.65), (0.026, 0.45)):
        env += amp * np.exp(-np.maximum(0, t - offset) * 28) * (t >= offset)
    return release_tail(noise * env * vel * 0.05, 0.03)


def reverb(stereo: np.ndarray, amount: float = 0.2) -> np.ndarray:
    """Cheap stereo hall: a short synthetic impulse + FFT convolution."""
    ir_n = int(1.65 * SR)
    t = np.arange(ir_n) / SR
    ir = np.stack(
        [rng.standard_normal(ir_n), rng.standard_normal(ir_n)], axis=1
    ) * np.exp(-t * 4.0)[:, None]
    ir[: int(0.018 * SR)] = 0
    ir[:, 0] = fft_filter(ir[:, 0], "low", 6500)
    ir[:, 1] = fft_filter(ir[:, 1], "low", 6500)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))

    out = np.empty_like(stereo)
    nfft = 1 << (int(N + ir_n - 1) - 1).bit_length()
    for ch in range(2):
        wet = np.fft.irfft(np.fft.rfft(stereo[:, ch], nfft) * np.fft.rfft(ir[:, ch], nfft), nfft)
        out[:, ch] = stereo[:, ch] + wet[:N] * amount
    return out


# --- harmony ---------------------------------------------------------------

CHORDS = {
    "F": ("F2", ["F3", "A3", "C4", "E4", "G4"]),
    "Dm": ("D2", ["D3", "F3", "A3", "C4", "E4"]),
    "Bb": ("Bb1", ["Bb2", "D3", "F3", "A3", "D4"]),
    "C": ("C2", ["C3", "E4", "G4", "Bb3", "D4"]),
}

# 14 bars at 90 BPM, resolving on F for the outro.
PROGRESSION = ["F", "Dm", "Bb", "C"] * 3 + ["Bb", "F"]

MELODY = {
    4: [(0.0, "A4", 1.0), (1.5, "C5", 0.5), (2.0, "E5", 1.0), (3.0, "D5", 0.5)],
    5: [(0.0, "D5", 1.0), (1.5, "F5", 0.5), (2.0, "E5", 1.0), (3.0, "C5", 0.5)],
    6: [(0.0, "D5", 1.0), (1.5, "F5", 0.5), (2.0, "A5", 1.0), (3.0, "G5", 0.5)],
    7: [(0.0, "E5", 1.0), (1.5, "G5", 0.5), (2.0, "F5", 1.0), (3.0, "D5", 0.5)],
    8: [(0.0, "A4", 1.0), (1.0, "C5", 0.5), (2.0, "E5", 1.0), (3.0, "D5", 0.5)],
    9: [(0.0, "F5", 1.0), (1.5, "E5", 0.5), (2.0, "D5", 1.0), (3.0, "A4", 0.5)],
    10: [(0.0, "D5", 1.0), (1.5, "F5", 0.5), (2.0, "G5", 1.0), (3.0, "A5", 0.5)],
    11: [(0.0, "G5", 1.0), (1.5, "F5", 0.5), (2.0, "E5", 1.0), (3.0, "D5", 0.5)],
    12: [(0.0, "D5", 1.0), (1.0, "F5", 1.0), (2.0, "A5", 1.0), (3.0, "G5", 1.0)],
    13: [(0.0, "F5", 2.5)],
}


def build() -> np.ndarray:
    piano_bus = np.zeros((N, 2), dtype=np.float64)
    pad_bus = np.zeros((N, 2), dtype=np.float64)
    bass_bus = np.zeros((N, 2), dtype=np.float64)
    drum_bus = np.zeros((N, 2), dtype=np.float64)
    mel_bus = np.zeros((N, 2), dtype=np.float64)
    bell_bus = np.zeros((N, 2), dtype=np.float64)
    vinyl = np.zeros((N, 2), dtype=np.float64)

    # Vinyl bed, very quiet, mono-ish.
    hiss = fft_filter(rng.standard_normal(N), "high", 1000)
    hiss = fft_filter(hiss, "low", 8500)
    pops_idx = rng.integers(0, N - 2000, 420)
    for idx in pops_idx:
        width = rng.integers(20, 120)
        vinyl[idx:idx + width, 0] += rng.uniform(-0.012, 0.012)
        vinyl[idx:idx + width, 1] += rng.uniform(-0.012, 0.012)
    vinyl += hiss[:, None] * 0.0018

    for bar, name in enumerate(PROGRESSION):
        t0 = bar * BAR
        root, notes = CHORDS[name]
        # Pad, with a longer tail on the final chord.
        if bar == 13:
            add(pad_bus, pad([NOTE[n] for n in notes], 4.6, 1.0), t0 - 0.15, pan=0.0)
        else:
            add(pad_bus, pad([NOTE[n] for n in notes], BAR + 0.9, 0.85), t0 - 0.12, pan=0.03)

        # Felt piano arpeggio: sparse on the intro, fuller once the beat is in.
        pattern = [
            (0.0, 0, 0.95), (0.5, 2, 0.45), (1.0, 1, 0.7), (1.5, 3, 0.4),
            (2.0, 2, 0.65), (2.5, 4, 0.38), (3.0, 3, 0.55), (3.5, 1, 0.32),
        ]
        if bar < 2:
            pattern = [(0.0, 0, 0.8), (1.5, 2, 0.42), (2.5, 1, 0.48), (3.25, 3, 0.3)]
        if bar == 12:
            pattern = [(0.0, 0, 0.9), (1.0, 2, 0.55), (2.0, 1, 0.7), (3.0, 3, 0.5)]
        if bar == 13:
            pattern = [(0.0, 0, 1.0), (0.18, 1, 0.55), (0.36, 2, 0.5), (0.58, 3, 0.45), (0.82, 4, 0.4)]
        for beat, note_idx, vel in pattern:
            note = notes[note_idx % len(notes)]
            add(
                piano_bus,
                piano(NOTE[note], 1.7 if bar < 13 else 3.8, vel * rng.uniform(0.86, 1.0)),
                t0 + beat * BEAT + rng.uniform(-0.008, 0.008),
                gain=1.0,
                pan=-0.16 + 0.02 * note_idx,
            )

        # Bass: root on 1 and the "and" of 3, then a long final note.
        if bar >= 2 and bar < 13:
            add(bass_bus, bass(NOTE[root], 1.5, 0.95), t0, pan=0)
            add(bass_bus, bass(NOTE[root], 1.1, 0.6), t0 + 2.5 * BEAT, pan=0)
        elif bar == 13:
            add(bass_bus, bass(NOTE["F1"], 4.2, 0.9), t0, pan=0)

        # Drums from the home scene until the pickup is finished.
        if 2 <= bar <= 12:
            add(drum_bus, kick(0.9 if bar < 7 else 1.0), t0, pan=0)
            add(drum_bus, kick(0.5), t0 + 2.5 * BEAT, pan=0)
            add(drum_bus, brush(0.9), t0 + BEAT, pan=0.05)
            add(drum_bus, brush(0.85), t0 + 3 * BEAT, pan=0.05)
            for off in (0.5, 1.5, 2.5, 3.5):
                add(drum_bus, hat(0.95), t0 + off * BEAT, pan=0.18)
            if bar in (7, 8, 9, 11):
                add(drum_bus, clap(0.7), t0 + BEAT, pan=-0.05)
            if bar == 12:
                for off in (3.0, 3.25, 3.5, 3.75):
                    add(drum_bus, brush(0.55), t0 + off * BEAT, pan=0.0)

        # Melody enters with the menu scene.
        for beat, note, dur in MELODY.get(bar, []):
            add(
                mel_bus,
                pluck(NOTE[note], 1.5 if bar < 13 else 3.0, 0.95),
                t0 + beat * BEAT + rng.uniform(-0.006, 0.006),
                pan=0.22,
            )
            add(
                bell_bus,
                bell(NOTE[note] * 2, 1.5 if bar < 13 else 3.2, 0.6),
                t0 + beat * BEAT + rng.uniform(-0.004, 0.004),
                pan=-0.28,
            )
            add(
                bell_bus,
                bell(NOTE[note] * 4, 0.9, 0.16),
                t0 + beat * BEAT + rng.uniform(-0.003, 0.003),
                pan=0.34,
            )

    # A soft dotted delay on the melody, panned opposite.
    delay = int(BEAT * 0.75 * SR)
    echo = np.zeros_like(mel_bus)
    echo[delay:] = mel_bus[:-delay] * 0.32
    echo[:, 0], echo[:, 1] = echo[:, 1].copy(), echo[:, 0].copy()
    mel_bus += echo

    # Reverb the melodic material, keep the rhythm dry.
    keys = reverb(piano_bus + mel_bus + bell_bus * 0.8 + pad_bus * 0.6, 0.22)

    mix = keys + pad_bus * 0.62 + bass_bus * 0.85 + drum_bus * 0.72 + vinyl
    # Remove rumble under the mix, then a gentle tonal tilt: less boom,
    # more presence around 2–3 kHz, a little air above 8 kHz.
    mix[:, 0] = fft_filter(mix[:, 0], "high", 38, 2)
    mix[:, 1] = fft_filter(mix[:, 1], "high", 38, 2)
    freqs = np.fft.rfftfreq(N, 1 / SR)
    low_shelf = 1 + (10 ** (-4.5 / 20) - 1) / (1 + (freqs / 260) ** 4)
    presence = 1 + (10 ** (5.0 / 20) - 1) * np.exp(-0.5 * (np.log2(np.maximum(freqs, 20) / 2600) / 1.15) ** 2)
    air = 1 + 0.35 / (1 + (6500 / np.maximum(freqs, 1)) ** 2)
    body_dip = 1 + (10 ** (-1.5 / 20) - 1) * np.exp(-0.5 * (np.log2(np.maximum(freqs, 20) / 700) / 0.9) ** 2)
    eq = low_shelf * body_dip * presence * air
    for ch in range(2):
        mix[:, ch] = np.fft.irfft(np.fft.rfft(mix[:, ch]) * eq, N)
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    peak = np.max(np.abs(mix))
    mix = mix / max(peak, 1e-9) * 0.88

    # A short breakdown before the final chord (the drums have stopped and
    # the pickup scene is resolving), then back up for the outro.
    env = np.ones(N)
    dip_a, dip_b = int(31.9 * SR), int(34.55 * SR)
    env[dip_a:dip_b] = 0.7
    ramp = int(0.35 * SR)
    env[dip_a - ramp:dip_a] = np.linspace(1.0, 0.7, ramp)
    rise = int(0.35 * SR)
    env[dip_b:dip_b + rise] = np.linspace(0.7, 1.0, rise)
    mix *= env[:, None]

    # Fade in/out.
    fade_in = int(0.65 * SR)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None] ** 1.5
    fade_out = int(2.2 * SR)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None] ** 1.2
    return mix.astype(np.float32)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    mix = build()
    pcm = (np.clip(mix, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(OUT), "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes(pcm.tobytes())
    print(f"wrote {OUT} ({DUR:.1f}s, {OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

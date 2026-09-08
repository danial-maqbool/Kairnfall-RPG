"""Original audio for the Atelier library.

Music is written for a plucked string voice (a Karplus-Strong delay line) over a
bowed drone, which gives the pack a warmer, more instrumental character than a
stack of sine partials. Ambience is filtered noise shaped by slow oscillators.
Effects are a transient plus a short resonant body.

Everything is synthesised here from scratch; there are no samples.
"""
from __future__ import annotations

import array
import math
import random
import wave
from pathlib import Path

RATE = 22050

MODES = {
    'aeolian': (0, 2, 3, 5, 7, 8, 10),
    'dorian': (0, 2, 3, 5, 7, 9, 10),
    'lydian': (0, 2, 4, 6, 7, 9, 11),
    'phrygian': (0, 1, 3, 5, 7, 8, 10),
    'pentatonic': (0, 3, 5, 7, 10),
}

# key -> (root midi note, mode, beats per minute, seconds, voice colour, drone)
MUSIC = {
    'music_menu': (57, 'aeolian', 68, 24, 0.42, True),
    'music_dawnreach': (60, 'lydian', 92, 24, 0.30, True),
    'music_emberhold': (55, 'phrygian', 84, 24, 0.52, True),
    'music_thornhollow': (57, 'dorian', 76, 24, 0.38, True),
    'music_frostgate': (62, 'aeolian', 64, 24, 0.24, True),
    'music_gloamport': (58, 'dorian', 88, 24, 0.34, True),
    'music_wayfarers_rest': (60, 'pentatonic', 96, 24, 0.28, True),
    'music_wilderness': (53, 'pentatonic', 80, 24, 0.36, True),
    'music_dungeon': (48, 'phrygian', 60, 24, 0.58, True),
    'music_boss': (50, 'phrygian', 132, 24, 0.62, True),
}

AMBIENCE = {
    'ambient_forest': dict(tilt=0.986, gain=0.60, sway=0.35, birds=True),
    'ambient_coast': dict(tilt=0.978, gain=0.75, sway=1.60, surf=True),
    'ambient_wind': dict(tilt=0.990, gain=0.55, sway=0.80),
    'ambient_cave': dict(tilt=0.994, gain=0.42, sway=0.18, drip=True),
}

# key -> (pitch, decay, noise mix, body ratio, chirp)
EFFECTS = {
    'effect_sword': (520, 26, 0.55, 2.4, -0.6),
    'effect_spell': (740, 12, 0.18, 1.5, 0.9),
    'effect_gather': (190, 22, 0.62, 1.8, -0.3),
    'effect_coins': (1650, 18, 0.30, 2.7, 0.4),
    'effect_hammer': (150, 30, 0.48, 2.1, -0.5),
    'effect_equip': (430, 20, 0.36, 1.9, 0.2),
    'effect_drink': (330, 14, 0.42, 1.3, 0.7),
    'effect_ui': (880, 28, 0.10, 2.0, 0.3),
}

TRACKS = tuple(list(MUSIC) + list(AMBIENCE) + list(EFFECTS))


def _hz(note):
    return 440.0 * 2 ** ((note - 69) / 12.0)


def _write(path: Path, samples, target=0.85):
    """Normalise to a per-kind target so music does not sit under the effects."""
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = max(1e-6, max(abs(v) for v in samples))
    scale = target / peak
    data = array.array('h', (max(-32767, min(32767, int(v * scale * 32767))) for v in samples))
    import sys
    if sys.byteorder != 'little':
        data.byteswap()
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(data.tobytes())


def _pluck(buffer, start, note, seconds, level, colour, rng):
    """Karplus-Strong: excite a delay line with noise, then average it down."""
    period = max(2, int(RATE / _hz(note)))
    line = [rng.uniform(-1.0, 1.0) for _ in range(period)]
    # colour the excitation: lower colour is a softer, rounder attack
    for index in range(1, period):
        line[index] = line[index] * colour + line[index - 1] * (1 - colour)
    count = min(int(seconds * RATE), len(buffer) - start)
    index = 0
    # higher strings lose their energy faster, as real ones do
    damp = 0.4990 - 0.0022 * max(0, note - 48) / 12.0
    for step in range(count):
        current = line[index]
        line[index] = (current + line[(index + 1) % period]) * damp
        envelope = math.exp(-step / RATE * 1.4)
        buffer[start + step] += current * level * envelope
        index = (index + 1) % period
    return buffer


def _drone(buffer, note, level):
    hz = _hz(note - 12)
    count = len(buffer)
    for step in range(count):
        seconds = step / RATE
        swell = 0.55 + 0.45 * math.sin(seconds * 0.22 * math.tau)
        value = (math.sin(math.tau * hz * seconds)
                 + 0.34 * math.sin(math.tau * hz * 2 * seconds + 0.4)
                 + 0.12 * math.sin(math.tau * hz * 3 * seconds))
        buffer[step] += value * level * swell


def music(key):
    root, mode_name, bpm, seconds, colour, drone = MUSIC[key]
    mode = MODES[mode_name]
    rng = random.Random(sum(ord(c) * (i + 3) for i, c in enumerate(key)))
    count = seconds * RATE
    buffer = [0.0] * count
    beat = 60.0 / bpm
    if drone:
        _drone(buffer, root, 0.055)
    # a slow four bar chord walk, then a melody that leans on the chord tones
    degrees = [0, 5, 3, 4] if mode_name != 'phrygian' else [0, 1, 5, 4]
    bars = int(seconds / (beat * 4))
    for bar in range(max(1, bars)):
        degree = degrees[bar % len(degrees)]
        chord = [mode[(degree + step) % len(mode)] + 12 * ((degree + step) // len(mode))
                 for step in (0, 2, 4)]
        start = int(bar * beat * 4 * RATE)
        if start >= count:
            break
        for voice, interval in enumerate(chord):
            _pluck(buffer, min(count - 1, start + voice * int(beat * 0.06 * RATE)),
                   root - 12 + interval, beat * 3.6, 0.20, colour * 0.8, rng)
        for step in range(8):
            when = start + int(step * beat * 0.5 * RATE)
            if when >= count:
                break
            if step % 2 == 1 and rng.random() < 0.45:
                continue
            pick = rng.choice(chord) if step % 4 == 0 else mode[rng.randrange(len(mode))]
            octave = 12 if rng.random() < 0.65 else 24
            _pluck(buffer, when, root + pick + octave, beat * 1.4, 0.26, colour, rng)
        if bpm >= 120:
            for step in range(4):
                when = start + int(step * beat * RATE)
                if when < count:
                    _pluck(buffer, when, root - 24, beat * 0.8, 0.30, 0.75, rng)
    for step in range(count):
        seconds_at = step / RATE
        fade = min(1.0, seconds_at / 0.5, (seconds - seconds_at) / 1.2)
        buffer[step] *= max(0.0, fade)
    return buffer


def ambience(key):
    config = AMBIENCE[key]
    rng = random.Random(sum(ord(c) * (i + 7) for i, c in enumerate(key)))
    seconds = 14
    count = seconds * RATE
    buffer = [0.0] * count
    low = 0.0
    band = 0.0
    for step in range(count):
        at = step / RATE
        white = rng.uniform(-1.0, 1.0)
        low = low * config['tilt'] + white * (1 - config['tilt'])
        band = band * 0.72 + (white - low) * 0.28
        sway = 0.55 + 0.45 * math.sin(at * config['sway'] * math.tau / 4)
        value = (low * 2.6 + band * 0.35) * config['gain'] * sway
        if config.get('surf'):
            crest = max(0.0, math.sin(at * 0.42 * math.tau)) ** 3
            value *= 0.5 + 1.5 * crest
        if config.get('drip') and (at % 3.1) < 0.02:
            value += math.sin(math.tau * 880 * at) * math.exp(-(at % 3.1) * 60) * 0.5
        if config.get('birds') and (at % 2.7) < 0.22:
            local = at % 2.7
            warble = 1500 + 420 * math.sin(local * 46)
            value += math.sin(math.tau * warble * at) * math.sin(local / 0.22 * math.pi) * 0.07
        buffer[step] = value
    for step in range(count):
        at = step / RATE
        buffer[step] *= max(0.0, min(1.0, at / 0.6, (seconds - at) / 0.6))
    return buffer


def effect(key):
    hz, decay, noise_mix, ratio, chirp = EFFECTS[key]
    rng = random.Random(sum(ord(c) * (i + 11) for i, c in enumerate(key)))
    seconds = 0.34
    count = int(seconds * RATE)
    buffer = [0.0] * count
    low = 0.0
    for step in range(count):
        at = step / RATE
        attack = min(1.0, at / 0.004)
        envelope = attack * math.exp(-at * decay)
        sweep = hz * (1.0 + chirp * math.exp(-at * 18))
        body = (math.sin(math.tau * sweep * at)
                + 0.40 * math.sin(math.tau * sweep * ratio * at)
                + 0.16 * math.sin(math.tau * sweep * ratio * 1.83 * at))
        white = rng.uniform(-1.0, 1.0)
        low = low * 0.55 + white * 0.45
        buffer[step] = (body * (1 - noise_mix) * 0.5 + low * noise_mix * 0.7) * envelope
    return buffer


def render(key):
    if key in MUSIC:
        return music(key)
    if key in AMBIENCE:
        return ambience(key)
    if key in EFFECTS:
        return effect(key)
    raise KeyError(key)


LOUDNESS = {'music': 0.60, 'ambient': 0.40, 'effect': 0.85}


def write(key, path):
    _write(Path(path), render(key), LOUDNESS.get(key.split('_')[0], 0.7))
    return path

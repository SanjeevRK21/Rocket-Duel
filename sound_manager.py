import pygame
import numpy as np

SAMPLE_RATE = 44100

def _gen_tone(freq, duration, volume=0.4, wave='sine', fade=True):
    frames = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, frames, endpoint=False)
    if wave == 'sine':
        data = np.sin(2 * np.pi * freq * t)
    elif wave == 'square':
        data = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == 'noise':
        data = np.random.uniform(-1, 1, frames)
    else:
        data = np.sin(2 * np.pi * freq * t)
    if fade:
        fade_len = min(frames, int(SAMPLE_RATE * 0.05))
        data[:fade_len] *= np.linspace(0, 1, fade_len)
        data[-fade_len:] *= np.linspace(1, 0, fade_len)
    data = (data * volume * 32767).astype(np.int16)
    stereo = np.column_stack([data, data])
    return pygame.sndarray.make_sound(stereo)

class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._build_sounds()
        except Exception:
            self.enabled = False

    def _build_sounds(self):
        # Click: short high blip
        self.snd_click = _gen_tone(880, 0.05, volume=0.3)
        # Place obstacle: snap
        self.snd_place = _gen_tone(440, 0.08, volume=0.35, wave='square')
        # Win: rising arpeggio (pre-mixed into one buffer)
        frames = int(SAMPLE_RATE * 0.6)
        t = np.linspace(0, 0.6, frames, endpoint=False)
        win_data = (
            np.sin(2 * np.pi * 523 * t) * np.where(t < 0.2, 1, 0) +
            np.sin(2 * np.pi * 659 * t) * np.where((t >= 0.2) & (t < 0.4), 1, 0) +
            np.sin(2 * np.pi * 784 * t) * np.where(t >= 0.4, 1, 0)
        )
        fade = int(SAMPLE_RATE * 0.05)
        win_data[-fade:] *= np.linspace(1, 0, fade)
        win_data = (win_data * 0.4 * 32767).astype(np.int16)
        self.snd_win = pygame.sndarray.make_sound(np.column_stack([win_data, win_data]))
        # Crash: noise burst
        self.snd_crash = _gen_tone(0, 0.25, volume=0.5, wave='noise', fade=True)
        # Engine: channel-based looping low hum (generated but looped externally)
        frames_eng = int(SAMPLE_RATE * 0.5)
        t_eng = np.linspace(0, 0.5, frames_eng, endpoint=False)
        eng = np.sin(2 * np.pi * 120 * t_eng) * 0.15 + np.sin(2 * np.pi * 240 * t_eng) * 0.08
        eng = (eng * 32767).astype(np.int16)
        self.snd_engine = pygame.sndarray.make_sound(np.column_stack([eng, eng]))
        self.engine_channel = None
        self._engine_playing = False

    def play(self, name):
        if not self.enabled: return
        try:
            snd = getattr(self, f"snd_{name}", None)
            if snd:
                snd.play()
        except Exception:
            pass

    def start_engine(self):
        if not self.enabled or self._engine_playing: return
        try:
            self.engine_channel = self.snd_engine.play(-1)
            self._engine_playing = True
        except Exception:
            pass

    def stop_engine(self):
        if not self.enabled: return
        try:
            self.snd_engine.stop()
            self._engine_playing = False
        except Exception:
            pass

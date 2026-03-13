import numpy as np

SAMPLE_RATE = 44100

def pre_init():
    """Call this BEFORE pygame.init() to configure mixer settings."""
    import pygame
    pygame.mixer.pre_init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=1024)

def _make_stereo(data):
    arr = np.ascontiguousarray(np.column_stack([data, data]))
    import pygame
    return pygame.sndarray.make_sound(arr)

def _sine(freq, dur, vol=0.4):
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    d = np.sin(2 * np.pi * freq * t)
    _fade(d)
    return (d * vol * 32767).astype(np.int16)

def _noise(dur, vol=0.45):
    d = np.random.uniform(-1, 1, int(SAMPLE_RATE * dur))
    _fade(d)
    return (d * vol * 32767).astype(np.int16)

def _fade(d, ms=40):
    n = min(len(d), int(SAMPLE_RATE * ms / 1000))
    d[:n]  *= np.linspace(0, 1, n)
    d[-n:] *= np.linspace(1, 0, n)


class SoundManager:
    def __init__(self):
        import pygame
        self.pygame = pygame
        self.enabled = False
        self._engine_playing = False
        try:
            # mixer should already be pre-init'd; just confirm it's up
            if not pygame.mixer.get_init():
                pygame.mixer.init(SAMPLE_RATE, -16, 2, 1024)
            self._build_sounds()
            self.enabled = True
        except Exception as e:
            print(f"[SoundManager] disabled: {e}")

    def _build_sounds(self):
        pygame = self.pygame

        self.snd_click = _make_stereo(_sine(880, 0.05, 0.3))
        self.snd_place = _make_stereo(_sine(440, 0.09, 0.35))

        # Win: three-note arpeggio
        frames = int(SAMPLE_RATE * 0.6)
        t = np.linspace(0, 0.6, frames, endpoint=False)
        w = (np.sin(2*np.pi*523*t) * (t < 0.2)
           + np.sin(2*np.pi*659*t) * ((t >= 0.2) & (t < 0.4))
           + np.sin(2*np.pi*784*t) * (t >= 0.4))
        _fade(w)
        self.snd_win = _make_stereo((w * 0.4 * 32767).astype(np.int16))

        self.snd_crash = _make_stereo(_noise(0.28, 0.5))

        # Engine hum — loopable 0.5s clip
        t_e = np.linspace(0, 0.5, int(SAMPLE_RATE * 0.5), endpoint=False)
        eng = (np.sin(2*np.pi*110*t_e) * 0.18
             + np.sin(2*np.pi*220*t_e) * 0.08
             + np.sin(2*np.pi*330*t_e) * 0.04)
        eng = (eng * 32767).astype(np.int16)
        self.snd_engine = _make_stereo(eng)

    def play(self, name):
        if not self.enabled:
            return
        try:
            snd = getattr(self, f"snd_{name}", None)
            if snd:
                snd.play()
        except Exception:
            pass

    def start_engine(self):
        if not self.enabled or self._engine_playing:
            return
        try:
            self.snd_engine.play(-1)
            self._engine_playing = True
        except Exception:
            pass

    def stop_engine(self):
        if not self.enabled:
            return
        try:
            self.snd_engine.stop()
            self._engine_playing = False
        except Exception:
            pass

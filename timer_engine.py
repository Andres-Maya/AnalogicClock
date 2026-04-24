"""
timer_engine.py
Motores para cronómetro y temporizador.
"""
import time

class StopwatchEngine:
    """Cronómetro: cuenta hacia arriba desde cero."""
    def __init__(self):
        self.reset()

    def start(self):
        if not self._running:
            self._start_time = time.time() - self._elapsed
            self._running = True

    def pause(self):
        if self._running:
            self._elapsed = time.time() - self._start_time
            self._running = False

    def reset(self):
        self._start_time = 0
        self._elapsed = 0
        self._running = False

    def get_elapsed(self):
        if self._running:
            return time.time() - self._start_time
        return self._elapsed

    def is_running(self):
        return self._running

class TimerEngine:
    """Temporizador: cuenta hacia atrás desde un tiempo dado."""
    def __init__(self, duration_sec=60):
        self.set(duration_sec)

    def set(self, duration_sec):
        self._duration = duration_sec
        self._end_time = None
        self._running = False
        self._remaining = duration_sec

    def start(self):
        if not self._running:
            self._end_time = time.time() + self._remaining
            self._running = True

    def pause(self):
        if self._running:
            self._remaining = self._end_time - time.time()
            self._running = False

    def reset(self):
        self._remaining = self._duration
        self._end_time = None
        self._running = False

    def get_remaining(self):
        if self._running:
            rem = self._end_time - time.time()
            return max(0, rem)
        return self._remaining

    def is_running(self):
        return self._running

    def is_finished(self):
        return self.get_remaining() <= 0

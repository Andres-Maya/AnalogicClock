"""
sound_manager.py
Manages the selection and playback of alarm sounds for the timer.

Follows the Single-Responsibility Principle: this class is exclusively
responsible for discovering available .wav files and playing them back
in a cross-platform way.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path


class SoundManager:
    """
    Discovers .wav files located next to the application and plays them
    asynchronously so the UI never blocks.

    Usage::

        sm = SoundManager()
        sm.select(sm.available_sounds[0])   # pick a sound by name
        sm.play()                            # play it (non-blocking)
        sm.stop()                            # stop current playback
    """

    def __init__(self, sounds_dir: str | Path | None = None) -> None:
        """
        Parameters
        ----------
        sounds_dir:
            Directory to scan for ``.wav`` files.  Defaults to the
            folder that contains *this* module file.
        """
        self._sounds_dir = Path(sounds_dir or Path(__file__).parent)
        self._available: list[str] = self._discover()
        self._selected: str | None = (
            self._available[0] if self._available else None
        )
        self._playback_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover(self) -> list[str]:
        """Return a sorted list of .wav filenames found in *sounds_dir*."""
        try:
            return sorted(
                f.name
                for f in self._sounds_dir.iterdir()
                if f.suffix.lower() == ".wav"
            )
        except OSError:
            return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available_sounds(self) -> list[str]:
        """Read-only list of discovered .wav filenames."""
        return list(self._available)

    @property
    def selected_sound(self) -> str | None:
        """The currently-selected sound filename, or ``None`` if none found."""
        return self._selected

    def select(self, filename: str) -> None:
        """
        Choose which sound will be played on the next :meth:`play` call.

        Parameters
        ----------
        filename:
            A bare filename (e.g. ``"Bomba_De_Tiempo.wav"``).
            Must be one of :attr:`available_sounds`.

        Raises
        ------
        ValueError
            If *filename* is not in :attr:`available_sounds`.
        """
        if filename not in self._available:
            raise ValueError(
                f"{filename!r} is not available. "
                f"Choose from: {self._available}"
            )
        self._selected = filename

    def play(self) -> None:
        """
        Play :attr:`selected_sound` asynchronously.

        Safe to call from the Tkinter main thread — playback runs in a
        daemon thread and will not block the UI or prevent shutdown.
        Does nothing if no sound has been selected.
        """
        if not self._selected:
            return
        path = str(self._sounds_dir / self._selected)
        self._playback_thread = threading.Thread(
            target=self._play_blocking,
            args=(path,),
            daemon=True,
            name="SoundManager-playback",
        )
        self._playback_thread.start()

    def stop(self) -> None:
        """
        Request that any ongoing playback stops as soon as possible.

        On Windows the winsound module cannot interrupt playback started
        with ``SND_ASYNC``; on other platforms the thread is simply
        abandoned (it is a daemon, so it will not prevent process exit).
        """
        if sys.platform == "win32":
            import winsound  # type: ignore[import]
            winsound.PlaySound(None, winsound.SND_PURGE)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _play_blocking(self, path: str) -> None:
        """Platform-aware blocking playback — called from a daemon thread."""
        if sys.platform == "win32":
            import winsound  # type: ignore[import]
            winsound.PlaySound(path, winsound.SND_FILENAME)
        elif sys.platform == "darwin":
            os.system(f"afplay {path!r}")
        else:
            # Linux: try aplay, then paplay, then pygame as last resort
            if os.system(f"aplay -q {path!r}") != 0:
                if os.system(f"paplay {path!r}") != 0:
                    try:
                        import pygame  # type: ignore[import]
                        pygame.mixer.init()
                        pygame.mixer.music.load(path)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            import time
                            time.sleep(0.05)
                    except ImportError:
                        pass  # No audio backend available — silent failure

    def __repr__(self) -> str:
        return (
            f"SoundManager("
            f"selected={self._selected!r}, "
            f"available={self._available})"
        )

"""Adquisición: ffmpeg → WAV 44.1 kHz estéreo con pico normalizado a −1 dBFS."""
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import numpy as np
import soundfile as sf

SR_SALIDA = 44100
_DB_OBJETIVO = 10 ** (-1.0 / 20.0)  # −1 dBFS


def decodificar(audio: Path, destino_wav: Path) -> Path:
    """Decodifica cualquier audio (MP3/FLAC/etc.) a WAV 44.1 kHz normalizado.

    Pico de salida = −1 dBFS (con silencio digital, se escribe tal cual).
    Devuelve destino_wav; lanza ErrorEntrada (mensaje en español) al fallar.
    """
    audio = Path(audio)
    destino_wav = Path(destino_wav)
    destino_wav.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chartforge_adqui_") as tmpdir:
        bruto = Path(tmpdir) / "bruto_f32.wav"
        proceso = subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error", "-i", str(audio),
                "-ar", str(SR_SALIDA), "-ac", "2", "-c:a", "pcm_f32le",
                str(bruto),
            ],
            capture_output=True, text=True, timeout=600,
        )
        if proceso.returncode != 0:
            from chartforge.cli import ErrorEntrada  # diferido: evita el ciclo cli->pipeline->adquisicion
            raise ErrorEntrada(f'No se pudo decodificar "{audio.name}": {(proceso.stderr or "").strip()[:300]}')
        datos, _sr = sf.read(str(bruto), dtype="float32", always_2d=True)
    pico = float(np.max(np.abs(datos))) if datos.size else 0.0
    if pico > 0.0:
        datos = (datos / pico) * _DB_OBJETIVO
    sf.write(str(destino_wav), datos, SR_SALIDA, subtype="PCM_16")
    return destino_wav

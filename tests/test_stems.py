"""Test slow de extracción de stems con demucs sobre un clip real de 30 s."""
from __future__ import annotations

from pathlib import Path

import pytest
import soundfile as sf

import chartforge.config as config
from chartforge.etapas.stems import extraer_stems

CLIP = config.RUTA_PROYECTO / "tests" / "fixtures" / "clip30.mp3"
STEMS_ESPERADOS = ("drums", "bass", "other", "vocals")

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def audio_16_bits():
    """Config por defecto del proyecto (venv)."""
    return config.cargar_config("")


def test_extraer_stems_30s(tmp_path, audio_16_bits):
    if not CLIP.is_file():
        pytest.skip("clip de pruebas ausente: correr la fabricacion del repositorio")
    resultado = extraer_stems(CLIP, tmp_path, audio_16_bits)
    assert set(resultado) == set(STEMS_ESPERADOS)
    for nombre, ruta in resultado.items():
        assert isinstance(ruta, Path) and ruta.is_file(), nombre
        # WAV 16-bit PCM / 44.1 kHz
        info = sf.info(str(ruta))
        assert info.format == "WAV", nombre
        assert info.subtype == "PCM_16", nombre
        assert info.samplerate == 44100, nombre
        # duracion ~30 s (tolerancia 0.1 s por bordes de demucs)
        assert abs(info.duration - 30.0) < 0.1, f"{nombre}: {info.duration:.3f}s"

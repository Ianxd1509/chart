"""Tests de features de stems (Task 6) con fixtures sinteticos deterministas."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from chartforge.chartgen.features import ExtraccionStems

SR = 44100
CLICKS = [0.5 + 0.5 * i for i in range(9)]  # 120 BPM
FIXTURES_CLI = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def rutas_sinteticas(tmp_path):
    """drums.wav = clicks 100 Hz decayed @120 BPM; other.wav = ruido blanco."""
    rng = np.random.default_rng(42)  # determinista

    def click_tren(n_seg=5.0):
        datos = np.zeros(int(SR * n_seg), dtype=np.float32)
        for t_click in CLICKS:
            inicio = int(t_click * SR)
            largo = int(0.15 * SR)
            tt = np.arange(largo) / SR
            burst = np.sin(2 * np.pi * 100.0 * tt) * np.exp(-tt * 25.0)
            datos[inicio : inicio + largo] += burst.astype(np.float32)
        pico = np.abs(datos).max()
        return (datos / pico * 0.9).astype(np.float32)  # pico ~0.9 (~-1 dBFS)

    drums = click_tren()
    other = (rng.standard_normal(SR * 5) * 0.1).astype(np.float32)
    r_drums = tmp_path / "drums.wav"
    r_other = tmp_path / "other.wav"
    r_bass = tmp_path / "bass.wav"
    r_vocals = tmp_path / "vocals.wav"
    sf.write(str(r_drums), np.stack([drums, drums], axis=1), SR, subtype="PCM_16")
    sf.write(str(r_other), np.stack([other, other], axis=1), SR, subtype="PCM_16")
    sf.write(str(r_bass), np.zeros((SR * 5, 2), dtype=np.float32), SR, subtype="PCM_16")
    sf.write(str(r_vocals), np.zeros((SR * 5, 2), dtype=np.float32), SR, subtype="PCM_16")
    return {"drums": r_drums, "bass": r_bass, "other": r_other, "vocals": r_vocals}


def test_onsets_de_clicks_al_120bpm(rutas_sinteticas):
    extra = ExtraccionStems(
        rutas_sinteticas["drums"], rutas_sinteticas["bass"],
        rutas_sinteticas["other"], rutas_sinteticas["vocals"], sr=SR,
    )
    onsets = extra.onsets("drums")
    assert isinstance(onsets, np.ndarray) and onsets.dtype == np.float64
    assert len(onsets) >= 8
    for esperado in CLICKS:
        hay_cerca = np.min(np.abs(onsets - esperado)) <= 0.030
        assert hay_cerca, f"falta click en {esperado:.2f} s (onsets: {onsets})"


def test_energias_bandas_del_click_en_baja(rutas_sinteticas):
    extra = ExtraccionStems(
        rutas_sinteticas["drums"], rutas_sinteticas["bass"],
        rutas_sinteticas["other"], rutas_sinteticas["vocals"], sr=SR,
    )
    onsets = extra.onsets("drums")
    df = extra.energias_bandas("drums", onsets)
    assert list(df.columns) == ["tiempo", "baja", "media", "alta"]
    assert len(df) == len(onsets)
    np.testing.assert_allclose(df["tiempo"].to_numpy(), onsets)
    assert (df["baja"] > df["media"]).all(), "el click debe concentrarse en la banda baja (1)"
    assert (df["baja"] > df["alta"]).all(), "el click debe concentrarse en la banda baja (2)"


def test_pitch_nan_en_ruido_homogeneo(rutas_sinteticas):
    extra = ExtraccionStems(
        rutas_sinteticas["drums"], rutas_sinteticas["bass"],
        rutas_sinteticas["other"], rutas_sinteticas["vocals"], sr=SR,
    )
    tiempos = np.array([1.0, 2.0, 3.0])
    pitch = extra.pitch_principal("other", tiempos)
    assert pitch.shape == tiempos.shape
    # pyin puede "afinar" instantes del ruido: lo comprobado
    assert np.isnan(pitch).mean() >= 0.5, f"ruido con demasiada afinacion: {pitch}"


def test_pitch_detectado_en_tono_puro(tmp_path):
    """Sinusoide constante con onsets del propio audio: pyin la ve."""
    r_drums = tmp_path / "drums.wav"
    r_bass = tmp_path / "bass.wav"
    r_other = tmp_path / "other.wav"
    r_vocals = tmp_path / "vocals.wav"
    tt = np.arange(SR * 4) / SR
    tono = (0.5 * np.sin(2 * np.pi * 329.63 * tt)).astype(np.float32)  # E4
    sf.write(str(r_vocals), np.stack([tono, tono], axis=1), SR, subtype="PCM_16")
    sf.write(str(r_drums), np.zeros((SR * 4, 2), dtype=np.float32), SR, subtype="PCM_16")
    sf.write(str(r_bass), np.zeros((SR * 4, 2), dtype=np.float32), SR, subtype="PCM_16")
    sf.write(str(r_other), np.zeros((SR * 4, 2), dtype=np.float32), SR, subtype="PCM_16")
    extra = ExtraccionStems(r_drums, r_bass, r_other, r_vocals, sr=SR)
    onsets = extra.onsets("vocals")
    pitch = extra.pitch_principal("vocals", np.atleast_1d(onsets))
    registrados = pitch[~np.isnan(pitch)]  # los que caen al borde del archivo salen NaN
    assert len(registrados) >= 1, f"pyin no vio el tono: {pitch}"
    assert np.all(np.abs(registrados - 329.63) < 2.0), f"pitch fuera de afinacion: {registrados}"


def test_stems_desconocidos_lanzan(rutas_sinteticas):
    extra = ExtraccionStems(
        rutas_sinteticas["drums"], rutas_sinteticas["bass"],
        rutas_sinteticas["other"], rutas_sinteticas["vocals"], sr=SR,
    )
    with pytest.raises(ValueError):
        extra.onsets("teclas")


def test_decodificar_normaliza_a_menos_1_dbfs(tmp_path):
    from chartforge.etapas.adquisicion import decodificar

    destino = tmp_path / "entrada.wav"
    resultado = decodificar(FIXTURES_CLI / "tono.mp3", destino)
    assert resultado == destino and destino.is_file()
    info = sf.info(str(destino))
    assert info.format == "WAV" and info.subtype == "PCM_16" and info.samplerate == SR
    datos, _ = sf.read(str(destino), dtype="float32")
    assert abs(float(np.abs(datos).max()) - 10 ** (-1.0 / 20.0)) < 0.01


def test_decodificar_falla_mensaje_espanol(tmp_path):
    from chartforge.etapas.adquisicion import decodificar
    from chartforge.cli import ErrorEntrada

    with pytest.raises(ErrorEntrada) as falla:
        decodificar(FIXTURES_CLI / "fake.mp3", tmp_path / "no.wav")
    assert "decodificar" in falla.value.mensaje.lower()

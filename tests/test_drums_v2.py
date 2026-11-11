"""Tests de la bateria v2 (#2 del feedback): kick/snare/tom/cymbal + sensibilidad."""
from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from chartforge.chartgen.drums import generar as generar_drums
from chartforge.chartgen.features import ExtraccionStems

SR = 44100
BPM = 120.0


def _escribir_mono(ruta, datos):
    sf.write(str(ruta), datos.astype(np.float32), SR, subtype="PCM_16")


def _sintetizar(patron: list[tuple[float, float, float]], duracion=3.0):
    """patron = [(tiempo_s, freq_hz, amplitud), ...] bursts con decaimiento."""
    datos = np.zeros(int(SR * duracion), dtype=np.float32)
    for t_click, freq, amp in patron:
        i0 = int(t_click * SR)
        tt = np.arange(int(0.12 * SR)) / SR
        burst = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 30.0) * amp
        if freq >= 4000:  # ruidos brillantes (platillos) → ruido filtrado
            rng = np.random.default_rng(7)
            burst = (
                burst + rng.standard_normal(len(tt)).astype(np.float32) * 0.6 * np.exp(-tt * 20.0) * amp
            )
        i1 = min(len(datos), i0 + len(burst))
        datos[i0:i1] += burst.astype(np.float32)[: i1 - i0]
    return datos


def _extra(tmp_path, drums_data, duracion):
    ruta = tmp_path / "drums.wav"
    pico = float(np.abs(drums_data).max()) or 1.0
    _escribir_mono(ruta, (drums_data / pico * 0.9))
    for resto in ("bass", "other", "vocals"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(int(SR * duracion), dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    return ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])


def test_drums_kick(tmp_path):
    """Click 70 Hz → lane 0 (kick)."""
    datos = _sintetizar([(0.5 * i, 70.0, 1.0) for i in range(1, 7)], 4.0)
    extra = _extra(tmp_path, datos, 4.0)
    gemas = generar_drums(extra, BPM)
    patas = [g for g in gemas if g.lane == 0]
    assert len(patas) >= 4, f"kicks esperados en lane 0: {gemas}"


def test_drums_snare_800hz(tmp_path):
    """Click 800 Hz (body broadband) → lane 1 (snare)."""
    datos = _sintetizar([(0.5 * i, 800.0, 1.0) for i in range(1, 7)], 4.0)
    extra = _extra(tmp_path, datos, 4.0)
    gemas = generar_drums(extra, BPM)
    patas = [g for g in gemas if g.lane == 1]
    assert len(patas) >= 4, f"snares esperados en lane 1: {gemas}"


def test_drums_tom_250hz(tmp_path):
    """Click 250 Hz (low tom tonal) → lane 3."""
    datos = _sintetizar([(0.5 * i, 250.0, 1.0) for i in range(1, 7)], 4.0)
    extra = _extra(tmp_path, datos, 4.0)
    gemas = generar_drums(extra, BPM)
    patas = [g for g in gemas if g.lane == 3]
    assert len(patas) >= 4, f"toms esperados en lane 3: {gemas}"


def test_drums_cymbal_8khz(tmp_path):
    """Clicks 8 kHz brillantes → lane 4 (cymbal)."""
    rng = np.random.default_rng(42)
    datos = np.zeros(int(SR * 4.0), dtype=np.float32)
    for t in (0.5, 1.5, 2.5, 3.5):
        tt = np.arange(int(0.18 * SR)) / SR
        i0 = int(t * SR)
        burst = rng.standard_normal(len(tt)) * np.exp(-tt * 12.0)
        burst = burst.astype(np.float32)
        burst = burst - burst.mean()
        datos[i0 : i0 + len(burst)] += burst * 0.9
    extra = _extra(tmp_path, datos, 4.0)
    gemas = generar_drums(extra, BPM)
    patas = [g for g in gemas if g.lane == 4]
    assert patas, f"platillos esperados en lane 4: {gemas}"


def test_onsets_mas_sensibles_con_delta(tmp_path):
    """onsets(delta=...) acepta sensibilidad y devuelve al menos tantos onsets."""
    datos = _sintetizar(
        [(t, 100.0, 1.0) for t in (0.5, 1.5, 2.5, 3.5)]
        + [(t, 7000.0, 0.08) for t in (0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75)],
        4.0,
    )
    extra = _extra(tmp_path, datos, 4.0)
    normales = extra.onsets("drums")
    sensibles = extra.onsets("drums", delta=0.03)
    assert len(sensibles) >= len(normales)
    assert len(sensibles) > len(normales) + 1

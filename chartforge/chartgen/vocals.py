"""Chart interno de voz (Task 7). No se escribe como pista de .chart:
Clone Hero no tiene pista vocals (S9); las letras van en [Events].

Con letra: gema por palabra a su tick exacto (lane por pitch).
Sin letra: gemas por onsets del stem vocals (cuantizadas a 1/16).
El evento "#sin-letras" lo emite PistaCancion.to_chart_text (modelo).
"""
from __future__ import annotations

import numpy as np

from chartforge import formatos
from chartforge.chartgen.features import ExtraccionStems
from chartforge.chartgen.guitar_bass import _midi
from chartforge.chartgen.modelo import Gema, Letra, ticks_de_tiempo

GRID = formatos.RESOLUCION // 4  # 1/16


def _cuantizar(tiempo: float, bpm: float) -> int:
    return int(round(ticks_de_tiempo(tiempo, bpm) / GRID) * GRID)


def _lane_por_pitch(pitch: np.ndarray) -> list[int]:
    """Lane 0..4 relativa al rango detectado; NaN/una sola altura → lane 0."""
    midis = np.array([_midi(f) for f in pitch if np.isfinite(f) and f > 0])
    if midis.size == 0 or float(midis.max()) - float(midis.min()) < 1.0:
        return [0] * len(pitch)
    m_min, m_max = float(midis.min()), float(midis.max())
    lanes = []
    for f0 in pitch:
        if np.isfinite(f0) and f0 > 0:
            lanes.append(int(round(4.0 * (_midi(f0) - m_min) / (m_max - m_min))) % 5)
        else:
            lanes.append(0)
    return lanes


def generar(feat: ExtraccionStems, letra: Letra | None, bpm: float) -> list[Gema]:
    """Gemas Expert de la voz: por palabra (con letra) o por onset (sin letra)."""
    if letra is not None:
        tiempos = np.array([t for t, _p in letra.palabras], dtype=np.float64)
        if tiempos.size == 0:
            return []
        pitch = feat.pitch_principal("vocals", tiempos)
        lanes = _lane_por_pitch(pitch)
        vistas: set[int] = set()
        gemas = []
        for (t, _palabra), lane in zip(letra.palabras, lanes):
            tick = ticks_de_tiempo(t, bpm)
            if tick not in vistas:
                vistas.add(tick)
                gemas.append(Gema(tick, lane, 0))
        return gemas

    onsets = feat.onsets("vocals")
    if onsets.size == 0:
        return []
    pitch = feat.pitch_principal("vocals", onsets)
    lanes = _lane_por_pitch(pitch)
    vistas: set[tuple[int, int]] = set()
    gemas = []
    for t, lane in zip(onsets, lanes):
        tick = _cuantizar(float(t), bpm)
        if (tick, lane) not in vistas:
            vistas.add((tick, lane))
            gemas.append(Gema(tick, lane, 0))
    return gemas

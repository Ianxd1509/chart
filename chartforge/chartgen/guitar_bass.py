"""Charts de guitarra (stem "other") y bajo (stem "bass") — Task 7.

Gema por onset, lane 0..4 por pitch (mapeo relativo al rango del stem).
Acordes: onsets a <50 ms se fusionan en un mismo tick (max 3 gemas, lanes
consecutivas desde el pitch base). Sustain: la nota sostiene hasta el
siguiente onset si el pitch cambia >1 semitono y el gap es >= 1/4; si el
pitch repite, no hay sustain (no solapadas en la misma lane); en la ultima
nota el sustain se cierra con un barrido de pitch hasta NaN.
"""
from __future__ import annotations

import numpy as np

from chartforge import formatos
from chartforge.chartgen.features import ExtraccionStems
from chartforge.chartgen.modelo import Gema, ticks_de_tiempo

STEMS_VALIDOS = ("other", "bass")
MAX_ACORDE = 3          # onsets <50 ms fusionados, max 3 gemas
GAP_ACORDE_S = 0.050    # fusion de onsets para acorde
GRID = formatos.RESOLUCION // 4  # cuantizacion 1/16
GAP_SUSTAIN_S = 0.25    # minimo para sostener (>= 1/4)
PASO_PITCH_S = 0.10     # barrido de pitch para el sustain de la ultima nota


def _midi(f0: float) -> float:
    return 69.0 + 12.0 * np.log2(f0 / 440.0)


def _cuantizar(tiempo: float, bpm: float) -> int:
    return int(round(ticks_de_tiempo(tiempo, bpm) / GRID) * GRID)


def generar(feat: ExtraccionStems, stem: str, bpm: float) -> list[Gema]:
    """Chart Expert del stem: gemas por onset con lane por pitch."""
    if stem not in STEMS_VALIDOS:
        raise ValueError(f"stem desconocido para guitar_bass: {stem!r}")
    if bpm <= 0:
        raise ValueError("bpm debe ser positivo")
    onsets = feat.onsets(stem)
    if onsets.size == 0:
        return []
    pitch = feat.pitch_principal(stem, onsets)

    # --- lanes por pitch: mapeo relativo al rango detectado en el stem
    midis = np.array([_midi(f) for f in pitch if np.isfinite(f) and f > 0])
    if midis.size:
        m_min, m_max = float(midis.min()), float(midis.max())
    else:
        m_min, m_max = 69.0, 69.0

    def lane_de(f0: float) -> int:
        if not np.isfinite(f0) or f0 <= 0:
            return 0
        if m_max - m_min < 1.0:
            return 0
        lane = int(round(4.0 * (_midi(f0) - m_min) / (m_max - m_min)))
        return max(0, min(4, lane))

    # --- clusters de onset (<50 ms) → acordes de max 3
    clusters: list[list[int]] = []
    for i, tiempo in enumerate(onsets):
        if clusters and float(tiempo) - float(onsets[clusters[-1][0]]) <= GAP_ACORDE_S:
            if len(clusters[-1]) < MAX_ACORDE:
                clusters[-1].append(i)
                continue
        clusters.append([i])

    gemas: list[Gema] = []
    for k, cluster in enumerate(clusters):
        tick = _cuantizar(float(onsets[cluster[0]]), bpm)
        base = lane_de(pitch[cluster[0]])
        lanes = [l for l in (base + j for j in range(len(cluster))) if l <= 4]
        longitud = _sustain_ticks(feat, stem, cluster, k, clusters, onsets, pitch, bpm)
        for lane in lanes:
            gemas.append(Gema(tick, lane, longitud if lane == lanes[0] else 0))
    return gemas


def _sustain_ticks(feat, stem, cluster, k, clusters, onsets, pitch, bpm) -> int:
    """Sustain (ticks, solo la base del acorde); 0 si el pitch no sostiene >= 1/4."""
    t_onset = float(onsets[cluster[0]])
    f_base = pitch[cluster[0]]
    if k + 1 < len(clusters):
        t_siguiente = float(onsets[clusters[k + 1][0]])
        f_sig = pitch[clusters[k + 1][0]]
        if (
            np.isfinite(f_base) and np.isfinite(f_sig) and f_sig > 0
            and abs(_midi(f_sig) - _midi(f_base)) > 1.0
            and (t_siguiente - t_onset) >= GAP_SUSTAIN_S
        ):
            return _cuantizar(t_siguiente, bpm) - _cuantizar(t_onset, bpm)
        return 0
    # ultima nota: barrido de pitch hasta que se rompe (>1 semitono o NaN)
    if not np.isfinite(f_base) or f_base <= 0:
        return 0
    t_fin = t_onset
    while t_fin + PASO_PITCH_S < feat.duracion(stem):
        t_prueba = t_fin + PASO_PITCH_S
        f = feat.pitch_principal(stem, np.array([t_prueba]))[0]
        if not (np.isfinite(f) and f > 0) or abs(_midi(f) - _midi(f_base)) > 1.0:
            break
        t_fin = t_prueba
    return max(0, _cuantizar(t_fin, bpm) - _cuantizar(t_onset, bpm))

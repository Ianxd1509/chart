"""Features de stems para el chartgen (Task 6, consume Task 7).

Cada stem se decodifica UNA sola vez (soundfile → mono float32 cacheado) y los
métodos calculan sobre esa única copia: no hay duplicados en RAM.
Bandas de STFT: baja < 200 Hz < media < 2000 Hz < alta.
"""
from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np
import pandas as pd
import soundfile as sf

BANDA_BAJA_HZ = 200.0
BANDA_MEDIA_HZ = 2000.0
BANDA_SUB_HZ = 160.0
BANDA_TOM_HZ = 350.0
BANDA_BODY_HZ = 1000.0
BANDA_SNAP_HZ = 4000.0
_VENTANA_ONSET_S = 0.10  # ventana de energía tras cada onset
_VENTANA_PITCH_S = 0.30  # ventana pyin por tiempo pedido
_HOP = 512


class ExtraccionStems:
    """Feature-extractor por stem (drums, bass, other, vocals)."""

    def __init__(self, ruta_drums, ruta_bass, ruta_other, ruta_vocals, sr: int = 44100):
        self._rutas: dict[str, Path] = {
            "drums": Path(ruta_drums),
            "bass": Path(ruta_bass),
            "other": Path(ruta_other),
            "vocals": Path(ruta_vocals),
        }
        self._sr_pedida = int(sr)
        self._mono: dict[str, np.ndarray] = {}  # única copia por stem
        self._sr: dict[str, int] = {}

    # ----------------------------------------------------------------------
    def _cargar(self, nombre_stem: str) -> np.ndarray:
        """Carga (una vez) y cachea el stem como mono float32."""
        try:
            ruta = self._rutas[nombre_stem]
        except KeyError as e:
            raise ValueError(f"stem desconocido: {nombre_stem!r}") from e
        if nombre_stem not in self._mono:
            datos, sr = sf.read(str(ruta), dtype="float32", always_2d=True)
            if sr != self._sr_pedida:
                datos = librosa.resample(datos.T, orig_sr=sr, target_sr=self._sr_pedida).T
                sr = self._sr_pedida
            self._mono[nombre_stem] = datos.mean(axis=1).astype(np.float32)
            self._sr[nombre_stem] = sr
        return self._mono[nombre_stem]

    # ----------------------------------------------------------------------
    def onsets(self, nombre_stem: str, delta: float | None = None) -> np.ndarray:
        """Tiempos (s) de los onsets del stem (librosa, con backtrack).

        delta=None → sensibilidad por defecto de librosa; un valor menor
        detecta onsets más débiles (batería).
        """
        datos = self._cargar(nombre_stem)
        sr = self._sr[nombre_stem]
        if datos.size == 0 or not datos.any():
            return np.array([], dtype=np.float64)
        envolvente = librosa.onset.onset_strength(y=datos, sr=sr, hop_length=_HOP)
        kwargs = {"backtrack": True, "sr": sr, "hop_length": _HOP}
        if delta is not None:
            kwargs["delta"] = float(delta)
        picos = librosa.onset.onset_detect(onset_envelope=envolvente, **kwargs)
        return librosa.frames_to_time(picos, sr=sr, hop_length=_HOP)

    def duracion(self, nombre_stem: str) -> float:
        """Duracion total (s) del stem (metodo aditivo pedido por Task 7)."""
        return float(len(self._cargar(nombre_stem)) / self._sr[nombre_stem])

    def energias_bandas(self, nombre_stem: str, onsets: np.ndarray) -> pd.DataFrame:
        """DataFrame(tiempo, baja, media, alta) con energía STFT por onset."""
        datos = self._cargar(nombre_stem)
        sr = self._sr[nombre_stem]
        n_fft = 2048
        frecuencias = np.fft.rfftfreq(n_fft, 1.0 / sr)
        filas = []
        for tiempo in np.asarray(onsets, dtype=np.float64):
            i0 = max(0, int(tiempo * sr))
            i1 = min(len(datos), i0 + int(_VENTANA_ONSET_S * sr))
            segmento = datos[i0:i1]
            if segmento.size == 0:
                filas.append({"tiempo": float(tiempo), "baja": 0.0, "media": 0.0, "alta": 0.0})
                continue
            ventana = np.hanning(segmento.size)
            espectro = np.abs(np.fft.rfft(segmento * ventana, n=n_fft)) ** 2
            filas.append({
                "tiempo": float(tiempo),
                "baja": float(espectro[frecuencias < BANDA_BAJA_HZ].sum()),
                "media": float(espectro[(frecuencias >= BANDA_BAJA_HZ) & (frecuencias < BANDA_MEDIA_HZ)].sum()),
                "alta": float(espectro[frecuencias >= BANDA_MEDIA_HZ].sum()),
            })
        return pd.DataFrame(filas, columns=["tiempo", "baja", "media", "alta"])

    def bandas_detalle(self, nombre_stem: str, onsets: np.ndarray) -> pd.DataFrame:
        """DataFrame(tiempo, sub, tom, body, snap, brillante) — spec de batería v2.

        sub < 160 Hz (kick) · tom 160-350 (tom de piso/medio) · body 350-1000
        (cuerpo del snare) · snap 1000-4000 (alambre del snare/hi-hat) ·
        brillante > 4000 (platillo). Heurística honesta: un bombo y un tom de
        ~80-100 Hz son indistinguibles sin pitch tracking, y se asignan a kick.
        """
        datos = self._cargar(nombre_stem)
        sr = self._sr[nombre_stem]
        n_fft = 2048
        frecuencias = np.fft.rfftfreq(n_fft, 1.0 / sr)
        filas = []
        for tiempo in np.asarray(onsets, dtype=np.float64):
            i0 = max(0, int(tiempo * sr))
            i1 = min(len(datos), i0 + int(_VENTANA_ONSET_S * sr))
            segmento = datos[i0:i1]
            if segmento.size == 0:
                filas.append({"tiempo": float(tiempo), "sub": 0.0, "tom": 0.0,
                              "body": 0.0, "snap": 0.0, "brillante": 0.0})
                continue
            ventana = np.hanning(segmento.size)
            espectro = np.abs(np.fft.rfft(segmento * ventana, n=n_fft)) ** 2
            filas.append({
                "tiempo": float(tiempo),
                "sub": float(espectro[frecuencias < BANDA_SUB_HZ].sum()),
                "tom": float(espectro[(frecuencias >= BANDA_SUB_HZ) & (frecuencias < BANDA_TOM_HZ)].sum()),
                "body": float(espectro[(frecuencias >= BANDA_TOM_HZ) & (frecuencias < BANDA_BODY_HZ)].sum()),
                "snap": float(espectro[(frecuencias >= BANDA_BODY_HZ) & (frecuencias < BANDA_SNAP_HZ)].sum()),
                "brillante": float(espectro[frecuencias >= BANDA_SNAP_HZ].sum()),
            })
        return pd.DataFrame(filas, columns=["tiempo", "sub", "tom", "body", "snap", "brillante"])

    def pitch_principal(self, nombre_stem: str, tiempos: np.ndarray) -> np.ndarray:
        """F0 dominante (pyin) en cada tiempo pedido; NaN cuando no hay tono."""
        datos = self._cargar(nombre_stem)
        sr = self._sr[nombre_stem]
        salida = np.empty(len(tiempos), dtype=np.float64)
        for indice, tiempo in enumerate(np.asarray(tiempos, dtype=np.float64)):
            i0 = max(0, int(tiempo * sr))
            i1 = min(len(datos), i0 + int(_VENTANA_PITCH_S * sr))
            segmento = datos[i0:i1]
            if segmento.size < int(0.05 * sr):
                salida[indice] = np.nan
                continue
            f0, _voz, _flag = librosa.pyin(segmento, fmin=60.0, fmax=600.0, sr=sr)
            f0 = f0[~np.isnan(f0)]
            salida[indice] = float(np.median(f0)) if f0.size else np.nan
        return salida

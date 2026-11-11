"""Transcripción de letras con faster-whisper sobre el stem vocal — etapa de etapas."""
from __future__ import annotations

from chartforge.descarga_modelos import aplicar_entorno


def transcribir(wav_vocals, cfg: dict, reportar=print) -> list[tuple[float, str]]:
    """Transcribe el WAV vocal (44.1 kHz) a palabras con tiempo de inicio.

    Devuelve lista de (segundo_inicio, palabra) en orden de aparición.
    El modelo (base por defecto) vive en modelos/hf del proyecto.
    """
    # asignacion directa: una HF_HOME host no manda los caches fuera del proyecto
    aplicar_entorno()

    import librosa  # diferido: solo en la venv
    import faster_whisper  # diferido: solo en la venv

    datos, _sr = librosa.load(str(wav_vocals), sr=16000, mono=True)
    modelo = faster_whisper.WhisperModel(cfg["letras"]["modelo"], device="cpu", compute_type="int8")
    reportar(f"Transcribiendo letras con whisper {cfg['letras']['modelo']}...")
    segmentos, info = modelo.transcribe(
        datos,
        word_timestamps=True,
        vad_filter=bool(cfg["letras"].get("vad", True)),
    )
    palabras: list[tuple[float, str]] = []
    for segmento in segmentos:  # el generador corre la transcripción
        for palabra in segmento.words:
            texto = palabra.word.strip()
            if texto:
                palabras.append((float(palabra.start), texto))
    return palabras

"""Extracción de stems (batería, bajo, otros, voz) con demucs — tarea de etapas.

El input puede ser MP3/FLAC/etc.: se convierte a WAV 44.1 kHz con ffmpeg y se
alimenta al separador usando soundfile (sin torchaudio, que en Windows no
decodifica MP3). El modelo htdemucs vive en modelos\torch del proyecto.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import soundfile as sf

import chartforge.config as config
from chartforge.descarga_modelos import aplicar_entorno


def _convertir_a_wav_16(audio: Path, destino_wav: Path) -> None:
    """ffmpeg: cualquier formato → WAV 16-bit 44.1 kHz estéreo (línea silenciosa)."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(audio),
            "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
            str(destino_wav),
        ],
        check=True,
    )


def extraer_stems(audio: Path, destino: Path, cfg: dict, reportar=print) -> dict[str, Path]:
    """Separa la pista en 4 stems con htdemucs y escribe WAV 16-bit 44.1 kHz.

    Devuelve dict stem → ruta del WAV (claves: drums, bass, other, vocals).
    """
    audio = Path(audio)
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)

    # variables de entorno ANTES de importar torch/demucs (regla del Task 3).
    # Asignacion directa: una env host (HF_HOME/TORCH_HOME) no puede mandar
    # los caches fuera de modelos\ del proyecto.
    aplicar_entorno()

    import demucs.api  # diferido: solo en la venv
    import torch  # diferido: solo en la venv

    with tempfile.TemporaryDirectory(prefix="chartforge_wav_") as tmpdir:
        wav = Path(tmpdir) / "entrada.wav"
        _convertir_a_wav_16(audio, wav)
        datos, _sr = sf.read(str(wav), dtype="float32", always_2d=True)
        tensor = torch.from_numpy(datos.T)  # (canales, muestras)

        separador = demucs.api.Separator(
            model=cfg["stems"]["modelo"],
            segment=None if not cfg["stems"].get("segmento") else int(cfg["stems"]["segmento"]),
        )
        reportar(f"Separando con {cfg['stems']['modelo']} (segmento {cfg['stems']['segmento']} s)...")
        _wav_entrada, separado = separador.separate_tensor(tensor)  # (resampleada, dict stem→tensor)

    resultado: dict[str, Path] = {}
    for nombre, tensor_stem in separado.items():
        ruta = destino / f"{nombre}.wav"
        sf.write(str(ruta), tensor_stem.T.numpy(), separador.samplerate, subtype="PCM_16")
        resultado[nombre] = ruta
    return resultado

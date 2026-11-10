"""Etapa de empaquetado (Task 8): arma la carpeta de cancion Clone Hero/YARG.

Escribe song.ini (SIN delay/song_length: Ruling Task 2, wiki CH "not
recommended"), notes.chart via PistaCancion.to_chart_text, y song.ogg +
un OGG por stem (ffmpeg libvorbis VBR q6). NUNCA toca CL ni crea ZIP:
el movimiento a CL lo hace Task 9 tras validar.
"""
from __future__ import annotations

import configparser
import subprocess
from pathlib import Path

from chartforge.chartgen.modelo import PistaCancion
from chartforge.formatos import CAMPOS_SONG_INI, NOMBRE_CARPETA, NOMBRES_AUDIO_STEMS

_Q_OGG = "6"
_TIMEOUT_FFMPEG_S = 300


def crear_carpeta_cancion(
    stems_wav: dict[str, Path],
    mix_wav: Path,
    pista: PistaCancion,
    titulo: str,
    artista: str,
    destino: Path,
) -> Path:
    """Crea <destino>/<Artista> - <Titulo> con song.ini, notes.chart y OGG."""
    desconocidos = set(stems_wav) - set(NOMBRES_AUDIO_STEMS)
    if desconocidos:
        raise ValueError(f"stems sin nombre de audio: {sorted(desconocidos)}")
    requeridos = set(NOMBRES_AUDIO_STEMS) - {"cancion"}
    faltantes = requeridos - set(stems_wav)
    if faltantes:
        raise ValueError(f"faltan stems: {sorted(faltantes)}")

    carpeta = destino / NOMBRE_CARPETA(artista, titulo)
    carpeta.mkdir(parents=True, exist_ok=True)

    _escribir_song_ini(carpeta / "song.ini", titulo, artista)
    (carpeta / "notes.chart").write_text(
        pista.to_chart_text({"name": titulo, "artist": artista}),
        encoding="utf-8",
    )

    _a_ogg(Path(mix_wav), carpeta / NOMBRES_AUDIO_STEMS["cancion"])
    for stem, nombre in NOMBRES_AUDIO_STEMS.items():
        if stem == "cancion":
            continue
        _a_ogg(Path(stems_wav[stem]), carpeta / nombre)
    return carpeta


def _escribir_song_ini(ruta: Path, titulo: str, artista: str) -> None:
    parser = configparser.ConfigParser()
    parser.optionxform = str  # conserva el caso de las claves
    parser["Song"] = dict(CAMPOS_SONG_INI)
    parser["Song"]["name"] = titulo
    parser["Song"]["artist"] = artista
    with ruta.open("w", encoding="utf-8") as archivo:
        parser.write(archivo)


def _a_ogg(origen: Path, destino: Path) -> None:
    """WAV → OGG con ffmpeg (libvorbis VBR q6)."""
    comando = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(origen), "-c:a", "libvorbis", "-q:a", _Q_OGG, str(destino),
    ]
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=_TIMEOUT_FFMPEG_S
        )
    except FileNotFoundError as error:
        raise RuntimeError("ffmpeg no esta disponible en PATH") from error
    if resultado.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo: {resultado.stderr.strip()}")

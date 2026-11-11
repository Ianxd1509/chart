"""Etapa de empaquetado (Task 8): arma la carpeta de cancion Clone Hero/YARG.

Escribe song.ini (con album/year/genre del audio cuando existe + diff_* segun
las dificultades generadas; SIN delay/song_length: Ruling Task 2),
notes.chart via PistaCancion.to_chart_text, OGG por stem (ffmpeg libvorbis
VBR q6) y, si el audio trae carátula embebida, album.jpg en la raiz.
NUNCA toca CL: el movimiento a CL lo hace el pipeline tras validar.
"""
from __future__ import annotations

import configparser
import subprocess
from pathlib import Path

from chartforge.chartgen.modelo import PistaCancion
from chartforge.etapas.metadatos import extraer_caratula, leer_tags
from chartforge.formatos import (
    CAMPOS_SONG_INI,
    DIFICULTADES,
    NOMBRE_CARPETA,
    NOMBRES_AUDIO_STEMS,
)

_Q_OGG = "6"
_TIMEOUT_FFMPEG_S = 300

_NIVEL_DIFICULTAD = {"Easy": 1, "Medium": 2, "Hard": 3, "Expert": 4}


def crear_carpeta_cancion(
    stems_wav: dict[str, Path],
    mix_wav: Path,
    pista: PistaCancion,
    titulo: str,
    artista: str,
    destino: Path,
    audio_origen: Path | None = None,
    reportar=print,
) -> Path:
    """Crea <destino>/<Artista> - <Titulo> con song.ini, notes.chart, OGG y carátula.

    audio_origen: MP3/FLAC/… original; solo se usa para tags (album/año/género)
    y carátula embebida en el song.ini/album.jpg. Si es None (o ambos fallan),
    esos campos simplemente no se escriben.
    """
    desconocidos = set(stems_wav) - set(NOMBRES_AUDIO_STEMS)
    if desconocidos:
        raise ValueError(f"stems sin nombre de audio: {sorted(desconocidos)}")
    requeridos = set(NOMBRES_AUDIO_STEMS) - {"cancion"}
    faltantes = requeridos - set(stems_wav)
    if faltantes:
        raise ValueError(f"faltan stems: {sorted(faltantes)}")

    carpeta = destino / NOMBRE_CARPETA(artista, titulo)
    carpeta.mkdir(parents=True, exist_ok=True)

    etiquetas = leer_tags(audio_origen) if audio_origen is not None else {}
    _escribir_song_ini(carpeta / "song.ini", titulo, artista, pista, etiquetas)
    (carpeta / "notes.chart").write_text(
        pista.to_chart_text({"name": titulo, "artist": artista}),
        encoding="utf-8",
    )

    _a_ogg(Path(mix_wav), carpeta / NOMBRES_AUDIO_STEMS["cancion"])
    for stem, nombre in NOMBRES_AUDIO_STEMS.items():
        if stem == "cancion":
            continue
        _a_ogg(Path(stems_wav[stem]), carpeta / nombre)

    if audio_origen is not None:
        caratula = extraer_caratula(audio_origen, carpeta / "album.jpg")
        if caratula is None:
            reportar("Aviso: no hay carátula embebida en el audio (se omite album.jpg).")
    return carpeta


def _nivel_instrumento(gemas_instrumento: dict | None) -> int:
    """Dificultad real generada: 1=Easy … 4=Expert; 0 = sin pista."""
    if not gemas_instrumento:
        return 0
    return max(
        (_NIVEL_DIFICULTAD[dificultad]
         for dificultad in DIFICULTADES
         if gemas_instrumento.get(dificultad)),
        default=0,
    )


def _escribir_song_ini(ruta: Path, titulo: str, artista: str,
                       pista: PistaCancion, etiquetas: dict[str, str]) -> None:
    parser = configparser.ConfigParser()
    parser.optionxform = str  # conserva el caso de las claves
    song = dict(CAMPOS_SONG_INI)
    song["name"] = titulo
    song["artist"] = artista
    if etiquetas.get("album"):
        song["album"] = etiquetas["album"]
    if etiquetas.get("year"):
        song["year"] = etiquetas["year"]
    if etiquetas.get("genre"):
        song["genre"] = etiquetas["genre"]

    drums = _nivel_instrumento(pista.gemas.get("bateria"))
    guitarra = _nivel_instrumento(pista.gemas.get("guitarra"))
    bajo = _nivel_instrumento(pista.gemas.get("bajo"))
    song["diff_drums"] = str(drums)
    song["diff_drums_real"] = "-1"
    song["diff_drums_real_22"] = "-1"
    song["diff_bass"] = str(bajo)
    song["diff_bass_real"] = "-1"
    song["diff_bass_real_22"] = "-1"
    song["diff_rhythm"] = "-1"
    song["diff_guitar"] = str(guitarra)
    song["diff_guitar_real"] = "-1"
    song["diff_guitar_real_22"] = "-1"
    song["diff_keys"] = "-1"
    song["diff_keys_real"] = "-1"
    song["diff_guitar_coop"] = "-1"
    song["diff_vocals"] = "0"  # no hay pista Vocals (las letras son eventos)
    song["diff_vocals_harm"] = "-1"
    song["diff_band"] = str(min(drums, guitarra, bajo))
    song["pro_drums"] = "False"  # nuestro [ExpertDrums] es 5 carriles estándar

    parser["Song"] = song
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

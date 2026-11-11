"""Metadatos del audio origen para el song.ini y la carátula.

Best-effort: leer tags (ffprobe) y extraer la carátula embebida (ffmpeg)
NUNCA aborta la conversión; si fallan, se omite lo que falte y se avisa.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

_TIMEOUT_FFPROBE_S = 60
_TIMEOUT_CARATULA_S = 60
_MAX_VALOR_INI = 80
_PATRON_ANIO = re.compile(r"(\d{4})")
_PROHIBIDOS_INI = re.compile(r'[;<>"\r\n]')


def _sanea(valor: str) -> str:
    """Valor aceptable para el ini: sin control chars ni ';' que rompe el parser."""
    limpio = _PROHIBIDOS_INI.sub(" ", valor).strip()
    limpio = re.sub(r"\s+", " ", limpio)
    return limpio[:_MAX_VALOR_INI].strip()


def leer_tags(audio: Path) -> dict[str, str]:
    """{'album'|'year'|'genre': valor} del audio; {} si no se puede leer.

    ffprobe devuelve claves con mayúsculas/minúsculas variadas según el tag
    (ID3/FLAC3/iTunes…): se normalizan para comparar.
    """
    comando = [
        "ffprobe", "-v", "error",
        "-show_entries", "format_tags",
        "-of", "json",
        str(audio),
    ]
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=_TIMEOUT_FFPROBE_S
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if resultado.returncode != 0:
        return {}
    try:
        data = json.loads(resultado.stdout or "{}")
    except json.JSONDecodeError:
        return {}
    tags = (data.get("format") or {}).get("tags") or {}
    normalizadas = {}
    for clave, valor in tags.items():
        normalizadas[re.sub(r"[^a-z]", "", clave.lower())] = str(valor)

    salida: dict[str, str] = {}
    album = normalizadas.get("album")
    if album and _sanea(album):
        salida["album"] = _sanea(album)
    anio = normalizadas.get("date", "") + " " + normalizadas.get("year", "")
    coincide = _PATRON_ANIO.search(anio)
    if coincide:
        salida["year"] = coincide.group(1)
    genero = normalizadas.get("genre")
    if genero and _sanea(genero):
        salida["genre"] = _sanea(genero)
    return salida


def extraer_caratula(audio: Path, destino_jpg: Path) -> Path | None:
    """Carátula embebida → <destino_jpg> (mjpeg). None si no hay o falla."""
    destino_jpg = Path(destino_jpg)
    comando = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(audio),
        "-map", "0:v:0?", "-frames:v", "1",
        "-vf", "scale=512:512:force_original_aspect_ratio=decrease",
        "-c:v", "mjpeg", "-q:v", "5",
        str(destino_jpg),
    ]
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=_TIMEOUT_CARATULA_S
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if resultado.returncode != 0:
        return None
    if destino_jpg.is_file() and destino_jpg.stat().st_size > 0:
        return destino_jpg
    return None

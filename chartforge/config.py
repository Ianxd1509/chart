"""Carga de config.ini y rutas raíz del proyecto (independientes del CWD)."""
from __future__ import annotations

import configparser
from pathlib import Path

RUTA_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_MODELOS = RUTA_PROYECTO / "modelos"
RUTA_SALIDA = RUTA_PROYECTO / "CL"

_VERDADES = ("1", "true", "si", "sí", "on", "yes", "verdadero")

_DEFAULTS: dict[str, dict[str, str]] = {
    "salida": {"carpeta": "CL"},
    "stems": {"modelo": "htdemucs", "segmento": "6", "batch": "1"},
    "letras": {"activada": "true", "modelo": "base", "vad": "true"},
}


def _normalizar(cfg: dict) -> dict:
    cfg["stems"]["segmento"] = int(cfg["stems"]["segmento"])
    cfg["stems"]["batch"] = int(cfg["stems"]["batch"])
    activada = str(cfg["letras"]["activada"]).strip().lower()
    cfg["letras"]["activada"] = activada in _VERDADES
    vad = str(cfg["letras"].get("vad", "true")).strip().lower()
    cfg["letras"]["vad"] = vad in _VERDADES
    return cfg


def _defaults() -> dict:
    cfg = {seccion: dict(pares) for seccion, pares in _DEFAULTS.items()}
    return _normalizar(cfg)


def cargar_config(ruta: str = "") -> dict:
    """Devuelve la config como dict; si la ruta está vacía o no existe, usa defaults."""
    cfg = _defaults()
    if ruta and Path(ruta).is_file():
        parser = configparser.ConfigParser()
        parser.read(ruta, encoding="utf-8")
        for seccion in cfg:
            if parser.has_section(seccion):
                for clave, valor in parser.items(seccion):
                    cfg[seccion][clave] = valor
        _normalizar(cfg)
    return cfg

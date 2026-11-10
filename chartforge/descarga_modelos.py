"""Descarga previa de modelos de demucs y faster-whisper dentro del proyecto.

Todo cae bajo D:\\charf1\\modelos\\ (TORCH_HOME y HF_HOME del proyecto), de modo
que el proyecto sigue siendo autocontenido: desinstalar = borrar la carpeta.
Los imports de demucs/whisper son diferidos: este módulo se usa también antes
de instalar (por la barra de progreso y la comprobación de espacio).
"""
from __future__ import annotations

import os
import shutil
import sys

import chartforge.config as config

ESPACIO_MINIMO_GB = 20

disk_usage = shutil.disk_usage  # símbolo sustituible en tests


def entorno_descarga() -> dict[str, str]:
    """Variables de entorno que dirigen las descargas a modelos\\ del proyecto."""
    return {
        "TORCH_HOME": str(config.RUTA_MODELOS / "torch"),
        "HF_HOME": str(config.RUTA_MODELOS / "hf"),
    }


def aplicar_entorno() -> dict[str, str]:
    """Reasigna el entorno del proyecto en `os.environ` — gana el proyecto.

    Es asignacion DIRECTA (no setdefault): una HF_HOME/TORCH_HOME global de la
    maquina NO puede mandar los caches fuera de modelos\\, o se rompe la
    promesa de autocontencion (desinstalar = borrar la carpeta).
    """
    env = entorno_descarga()
    for clave, valor in env.items():
        os.environ[clave] = valor
    return env


def hay_espacio(ruta: str, minimo_gb: int = ESPACIO_MINIMO_GB) -> tuple[bool, str]:
    """¿Queda espacio suficiente en la unidad de `ruta`? Devuelve (ok, mensaje)."""
    info = disk_usage(ruta)
    libre_gb = info.free / 1024**3
    if libre_gb < minimo_gb:
        return False, f"Espacio insuficiente: {libre_gb:.1f} GB libres, se necesitan {minimo_gb} GB en {ruta}"
    return True, f"Espacio disponible: {libre_gb:.1f} GB libres en {ruta}"


def _reportar(texto: str) -> None:
    print(texto, flush=True)


def descargar_demucs() -> None:
    """Descarga htdemucs al caché de torch del proyecto (unos 80 MB)."""
    import demucs.pretrained  # diferido: solo en la venv

    _reportar("Descargando modelo demucs htdemucs...")
    modelo = demucs.pretrained.get_model("htdemucs")
    _reportar(f"demucs htdemucs listo ({sum(p.numel() for p in modelo.parameters()) / 1e6:.1f}M parámetros)")


def descargar_whisper() -> None:
    """Descarga faster-whisper 'base' dentro de HF_HOME del proyecto (unos 145 MB)."""
    import huggingface_hub  # diferido: solo en la venv

    _reportar("Descargando modelo whisper base (Systran/faster-whisper-base)...")
    huggingface_hub.snapshot_download("Systran/faster-whisper-base")
    _reportar("whisper base listo")


def descargar_todo(reportar=_reportar) -> None:
    """Descarga todos los modelos con las variables de entorno del proyecto."""
    for clave, valor in aplicar_entorno().items():
        reportar(f"{clave} = {valor}")
    descargar_demucs()
    descargar_whisper()
    reportar("Modelos descargados dentro de modelos\\ del proyecto.")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--todo" not in argv:
        print("Uso: python -m chartforge.descarga_modelos --todo")
        return 2
    ok, mensaje = hay_espacio(str(config.RUTA_PROYECTO))
    print(mensaje)
    if not ok:
        return 1
    descargar_todo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

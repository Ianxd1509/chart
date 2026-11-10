"""Test de imports de la venv (Task 3) y lógica pura de descarga_modelos."""
from __future__ import annotations

import subprocess

import pytest

import chartforge.config as config

VENV = config.RUTA_PROYECTO / "venv"
PYTHON_VENV = VENV / "Scripts" / "python.exe"


def test_imports_en_venv():
    if not PYTHON_VENV.is_file():
        pytest.skip("correr instalar.ps1 primero")
    out = subprocess.run(
        [str(PYTHON_VENV), "-c", "import torch, demucs, faster_whisper, librosa, soundfile, psutil; print('ok')"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert out.returncode == 0, f"imports fallaron:\n{out.stdout}\n{out.stderr}"
    assert out.stdout.strip() == "ok"


def test_entorno_descarga_usa_modelos_del_proyecto():
    import chartforge.descarga_modelos as dm

    env = dm.entorno_descarga()
    assert env["TORCH_HOME"] == str(config.RUTA_MODELOS / "torch")
    assert env["HF_HOME"] == str(config.RUTA_MODELOS / "hf")


def test_aplicar_entorno_reasigna_ganando_al_host(monkeypatch):
    """HF_HOME/TORCH_HOME globales de la maquina NO ganan: se reasignan Directo.

    Con setdefault una env host mandaba cachés fuera de modelos\\ y rompia la
    promesa de autocontencion (revision: Important 3).
    """
    import os

    import chartforge.descarga_modelos as dm

    monkeypatch.setenv("HF_HOME", r"C:\basura_host")
    monkeypatch.setenv("TORCH_HOME", r"C:\basura_host")
    devuelto = dm.aplicar_entorno()
    assert devuelto["HF_HOME"] == str(config.RUTA_MODELOS / "hf")
    assert os.environ["HF_HOME"] == str(config.RUTA_MODELOS / "hf")
    assert os.environ["TORCH_HOME"] == str(config.RUTA_MODELOS / "torch")


def test_hay_espacio_suficiente(monkeypatch):
    import chartforge.descarga_modelos as dm

    class Disco:
        def __init__(self, libre):
            self.free = libre

    GB = 1024**3
    monkeypatch.setattr(dm, "disk_usage", lambda _ruta: Disco(10 * GB))
    ok, mensaje = dm.hay_espacio("D:\\")
    assert ok is False
    assert "espacio" in mensaje.lower()

    monkeypatch.setattr(dm, "disk_usage", lambda _ruta: Disco(50 * GB))
    ok, mensaje = dm.hay_espacio("D:\\")
    assert ok is True
    assert "espacio" in mensaje.lower()

"""Tests de chartforge.config: defaults, carga de ini e independencia del CWD."""
from __future__ import annotations

import textwrap

import chartforge.config as config


def test_defaults_ok():
    cfg = config.cargar_config("")
    assert cfg["salida"]["carpeta"] == "CL"
    assert cfg["stems"]["modelo"] == "htdemucs"
    assert cfg["stems"]["segmento"] == 6
    assert cfg["stems"]["batch"] == 1
    assert cfg["letras"]["activada"] is True
    assert cfg["letras"]["modelo"] == "base"


def test_cargar_config_le_archivo(tmp_path):
    ruta = tmp_path / "config.ini"
    ruta.write_text(textwrap.dedent("""\
        [salida]
        carpeta = OTRA

        [stems]
        modelo = htdemucs
        segmento = 8
        batch = 2

        [letras]
        activada = true
        modelo = base
        """), encoding="utf-8")
    cfg = config.cargar_config(str(ruta))
    assert cfg["salida"]["carpeta"] == "OTRA"
    assert cfg["stems"]["segmento"] == 8
    assert isinstance(cfg["stems"]["segmento"], int)


def test_rutas_independientes_del_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert config.RUTA_SALIDA.name == "CL"
    assert config.RUTA_MODELOS.parent == config.RUTA_PROYECTO
    assert config.RUTA_SALIDA.is_absolute()

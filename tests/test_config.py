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
    assert cfg["letras"]["vad"] is True
    assert cfg["sistema"]["ram_minima_gb"] == 1.5


def test_cargar_config_ram_minima_gb(tmp_path):
    ruta = tmp_path / "config.ini"
    ruta.write_text("""\
[sistema]
ram_minima_gb = 0.8
""", encoding="utf-8")
    cfg = config.cargar_config(str(ruta))
    assert cfg["sistema"]["ram_minima_gb"] == 0.8


def test_cargar_config_ram_minima_gb_invalida_usa_default(tmp_path):
    ruta = tmp_path / "config.ini"
    ruta.write_text("""\
[sistema]
ram_minima_gb = no-es-numero
""", encoding="utf-8")
    cfg = config.cargar_config(str(ruta))
    assert cfg["sistema"]["ram_minima_gb"] == 1.5


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


def test_cargar_config_vad_false(tmp_path):
    ruta = tmp_path / "config.ini"
    ruta.write_text(textwrap.dedent("""\
        [letras]
        activada = true
        modelo = base
        vad = false
        """), encoding="utf-8")
    cfg = config.cargar_config(str(ruta))
    assert cfg["letras"]["vad"] is False


def test_rutas_independientes_del_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert config.RUTA_SALIDA.name == "CL"
    assert config.RUTA_MODELOS.parent == config.RUTA_PROYECTO
    assert config.RUTA_SALIDA.is_absolute()

"""Tests de chartforge.etapas.metadatos (tags + carátula, simulando ffprobe/ffmpeg)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from chartforge.etapas import metadatos


class _Resultado:
    def __init__(self, stdout: bytes = b"", rc: int = 0):
        self.stdout = stdout
        self.returncode = rc
        self.stderr = b""


def test_leer_tags_ok(monkeypatch):
    salida = b'{"format": {"tags": {"album": "99.9", "date": "2019-05-29", "genre": "J-Rock"}}}'
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(salida, 0))
    tags = metadatos.leer_tags(Path("fake.mp3"))
    assert tags == {"album": "99.9", "year": "2019", "genre": "J-Rock"}


def test_leer_tags_normaliza_claves(monkeypatch):
    salida = b'{"format": {"tags": {"ALBUM": "Album", "TRCK": "1", "DATE": "1999"}}}'
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(salida, 0))
    tags = metadatos.leer_tags(Path("fake.mp3"))
    assert tags["album"] == "Album"
    assert tags["year"] == "1999"


def test_leer_tags_utf8_multicos(monkeypatch):
    """ffprobe emite UTF-8; los acentos de ID3 deben sobrevivir intactos."""
    salida = '{"format": {"tags": {"album": "V\u00e1monos Pa\u2019l R\u00edo"}}}'.encode("utf-8")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(salida, 0))
    tags = metadatos.leer_tags(Path("fake.mp3"))
    assert tags["album"] == "Vámonos Pa’l Río"


def test_leer_tags_fallo_sin_binarios(monkeypatch):
    def _no_disponible(*a, **k):
        raise OSError("ffprobe no encontrado")

    monkeypatch.setattr(subprocess, "run", _no_disponible)
    assert metadatos.leer_tags(Path("fake.mp3")) == {}


def test_leer_tags_json_roto(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(b"no es json", 0))
    assert metadatos.leer_tags(Path("fake.mp3")) == {}


def test_leer_tags_rc_error(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(b"", 1))
    assert metadatos.leer_tags(Path("fake.mp3")) == {}


def test_sanea_quita_prohibidos(monkeypatch):
    salida = b'{"format": {"tags": {"album": "99.9; \\"Quote\\" <x>"}}}'
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(salida, 0))
    tags = metadatos.leer_tags(Path("fake.mp3"))
    assert ";" not in tags["album"] and '"' not in tags["album"]


def test_extraer_caratula_ok(monkeypatch, tmp_path):
    dst = tmp_path / "album.jpg"

    def _run(cmd, *a, **k):
        dst.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")
        return _Resultado(b"", 0)

    monkeypatch.setattr(subprocess, "run", _run)
    resultado = metadatos.extraer_caratula(Path("fake.mp3"), dst)
    assert resultado == dst


def test_extraer_caratula_fallo(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(b"", 1))
    assert metadatos.extraer_caratula(Path("fake.mp3"), tmp_path / "album.jpg") is None


def test_extraer_caratula_sin_imagen(monkeypatch, tmp_path):
    # ffmpeg rc=0 pero no creó el archivo (sin pista de video)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Resultado(b"", 0))
    assert metadatos.extraer_caratula(Path("fake.mp3"), tmp_path / "album.jpg") is None

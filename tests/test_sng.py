"""Tests del exportador .sng (#6): layout + roundtrip de vuelta con un parser
INDEPENDIENTE dentro del test (verifica que cualquier lector SGPKG entienda lo
escrito — no se copia el parser de producción aquí)."""
from __future__ import annotations

import struct
from pathlib import Path

import pytest

from chartforge.sng import exportar_sng


def _fixture_carpeta(tmp_path: Path) -> Path:
    carpeta = tmp_path / "Artista - Titulo"
    carpeta.mkdir()
    (carpeta / "song.ini").write_text(
        "[Song]\nname = 99.9\nartist = Mob Choir\nalbum = 99.9\ncharter = ChartForge\n"
        "diff_drums = 4\npro_drums = False\n",
        encoding="utf-8",
    )
    (carpeta / "notes.chart").write_text(
        '[Song]\n{\nName = 99.9\nArtist = Mob Choir\nCharter = ChartForge\nOffset = 0\n'
        'Resolution = 192\n}\n[SyncTrack]\n{\n0 = TS 4\n0 = B 83354\n}\n'
        '[ExpertDrums]\n{\n0 = N 0 0\n}\n',
        encoding="utf-8",
    )
    (carpeta / "song.ogg").write_bytes(b"OggSFAKE-" * 100)
    (carpeta / "drums.ogg").write_bytes(b"OggS DRUMS" * 50)
    (carpeta / "album.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"J" * 5000)
    return carpeta


def _parsear_sng(ruta: Path):
    data = ruta.read_bytes()
    assert data[:6] == b"SNGPKG"
    version, = struct.unpack_from("<I", data, 6)
    assert version == 1
    clave = data[10:26]

    def u64(p):
        return struct.unpack_from("<Q", data, p)[0], p + 8

    def i32(p):
        return struct.unpack_from("<i", data, p)[0], p + 4

    p = 26
    meta_len, p = u64(p)
    meta_end = p + meta_len
    meta_count, p = u64(p)
    metadatos = {}
    for _ in range(meta_count):
        kl, p = i32(p)
        k = data[p:p+kl].decode(); p += kl
        vl, p = i32(p)
        v = data[p:p+vl].decode(); p += vl
        metadatos[k] = v
    assert p == meta_end

    file_meta_len, p = u64(p)
    file_meta_end = p + file_meta_len
    file_count, p = u64(p)
    archivos = []
    for _ in range(file_count):
        nl = data[p]; p += 1
        nombre = data[p:p+nl].decode(); p += nl
        contents_len, p = u64(p)
        contents_idx, p = u64(p)
        archivos.append((nombre, contents_len, contents_idx))
    assert p == file_meta_end

    data_len, p = u64(p)
    assert data_len == sum(a[1] for a in archivos)

    def contenido(a):
        nombre, contents_len, idx = a
        crudo = data[idx:idx+contents_len]
        return bytes(b ^ (clave[i % 16] ^ (i & 0xFF)) for i, b in enumerate(crudo))

    return metadatos, archivos, contenido


def test_sng_roundtrip_layout_completo(tmp_path):
    carpeta = _fixture_carpeta(tmp_path)
    destino = exportar_sng(carpeta, clave=bytes(range(16)))
    assert destino.is_file()
    metadatos, archivos, contenido = _parsear_sng(destino)
    assert metadatos["name"] == "99.9"
    assert metadatos["charter"] == "ChartForge"
    assert metadatos["pro_drums"] == "False"
    nombres = [a[0] for a in archivos]
    assert nombres == sorted(nombres)
    assert "song.ini" not in nombres
    assert {a[0] for a in archivos} == {"notes.chart", "song.ogg", "drums.ogg", "album.jpg"}
    for a in archivos:
        esperado = (carpeta / a[0]).read_bytes()
        assert contenido(a) == esperado, a[0]


def test_sng_song_ini_no_se_empaqueta(tmp_path):
    carpeta = _fixture_carpeta(tmp_path)
    destino = exportar_sng(carpeta, clave=bytes(16))
    _metadatos, archivos, _contenido = _parsear_sng(destino)
    assert "song.ini" not in [a[0] for a in archivos]


def test_sng_sin_song_ini_error(tmp_path):
    carpeta = tmp_path / "sin-ini"
    carpeta.mkdir()
    (carpeta / "song.ogg").write_bytes(b"x")
    with pytest.raises(ValueError, match="song.ini"):
        exportar_sng(carpeta)


def test_sng_carpeta_vacia_error(tmp_path):
    carpeta = tmp_path / "vacia"
    carpeta.mkdir()
    with pytest.raises(ValueError, match="vacía|sin archivos"):
        exportar_sng(carpeta)


def test_sng_destino_default_junto_a_carpeta(tmp_path):
    carpeta = _fixture_carpeta(tmp_path)
    destino = exportar_sng(carpeta, clave=bytes(16))
    assert destino.name == "Artista - Titulo.sng"
    assert destino.parent == tmp_path


def test_sng_clave_determinista_reproduce_bytes(tmp_path):
    carpeta = _fixture_carpeta(tmp_path)
    a = exportar_sng(carpeta, tmp_path / "a.sng", clave=b"\x07" * 16)
    b_path = exportar_sng(carpeta, tmp_path / "b.sng", clave=b"\x07" * 16)
    assert a.read_bytes() == b_path.read_bytes()

"""Exportador .sng (Clone Hero/YARG) de una carpeta de cancion.

Implementación propia desde el spec público "SngFileFormat"
(https://github.com/mdsitton/SngFileFormat, formato `SNGPKG` v1) — nada copiado:
los hechos de formato no tienen copyright; el formato es público por diseño.

Layout (verificado contra un .sng real del Chart de referencia):

  Header:  "SNGPKG"(6) | version u32=1 | xorMask 16 bytes
  Metadata: u64 metadataLen (bytes tras este campo = 8 + pares) | u64 count |
            pares (i32 keyLen + key utf8 | i32 valueLen + value utf8)
  FileIndex: u64 fileMetaLen (bytes tras el campo = 8 + payload) | u64 count |
            entradas (u8 nameLen + name | u64 contentsLen | u64 contentsIndex absoluto)
  FileData:  u64 fileDataLen (= suma de contentsLen) | archivos enmascarados
             concatenados, cada uno con la máscara DESDE CERO por posición.

Enmascarado por byte i (posición DENTRO del archivo):
  masked = byte XOR (xorMask[i % 16] XOR (i & 0xFF))

`song.ini` NO se guarda como archivo: su sección [Song] se exporta como
pares de metadatos (spec "metadata strings"). Sin compresión.
"""
from __future__ import annotations

import configparser
import os
import struct
import sys
from pathlib import Path

MAGIC = b"SNGPKG"
VERSION = 1
_CARACTERES_PROHIBIDOS = '<>:"/\\|?*'


def _validar_nombre(nombre: str) -> None:
    if any(c in nombre for c in _CARACTERES_PROHIBIDOS):
        raise ValueError(f"nombre de archivo .sng invalido: {nombre!r}")
    if any(ord(c) < 32 or ord(c) == 0x7F for c in nombre):
        raise ValueError(f"caracter de control en nombre .sng: {nombre!r}")
    if ".." in nombre:
        raise ValueError(f"ruta relativa .sng invalida: {nombre!r}")


def _masked_bytes(datos: bytes, clave: bytes) -> bytes:
    return bytes(b ^ (clave[i % 16] ^ (i & 0xFF)) for i, b in enumerate(datos))


def _pares_metadatos(pares: dict[str, str]) -> bytes:
    """u64 count + pares clave/valor utf8 (i32 lens)."""
    salida = bytearray(struct.pack("<Q", len(pares)))
    for clave, valor in pares.items():
        k = clave.encode("utf-8")
        v = valor.encode("utf-8")
        salida += struct.pack("<i", len(k)) + k
        salida += struct.pack("<i", len(v)) + v
    return bytes(salida)


def _entradas_indice(archivos: list[tuple[str, int, int]]) -> bytes:
    """Entradas del FileIndex (SIN count; el caller empaqueta u64 len + u64 count)."""
    salida = bytearray()
    for nombre, contents_len, indice in archivos:
        n = nombre.encode("utf-8")
        salida += struct.pack("<B", len(n)) + n
        salida += struct.pack("<Q", int(contents_len))
        salida += struct.pack("<Q", int(indice))
    return bytes(salida)


def _metadatos_desde_ini(ruta_ini: Path) -> dict[str, str]:
    parser = configparser.ConfigParser()
    parser.optionxform = str  # conserva claves song.ini como en el origen
    parser.read(str(ruta_ini), encoding="utf-8")
    if not parser.has_section("Song"):
        raise ValueError("song.ini sin seccion [Song]")
    return {clave.strip(): valor for clave, valor in parser.items("Song")}


def exportar_sng(
    carpeta: Path,
    destino: Path | None = None,
    clave: bytes | None = None,
) -> Path:
    """Construye <carpeta>.sng (o `destino`) desde una carpeta de cancion.

    Lanza ValueError si falta song.ini, si la carpeta no tiene archivos o si
    un nombre no es válido para el formato.
    """
    carpeta = Path(carpeta).resolve()
    if not carpeta.is_dir():
        raise FileNotFoundError(f"no existe la carpeta: {carpeta}")

    archivos_origen = sorted(
        p for p in carpeta.iterdir()
        if p.is_file() and not p.name.startswith(".")
    )
    if not archivos_origen:
        raise ValueError("carpeta sin archivos: nada que empaquetar")

    ruta_ini = carpeta / "song.ini"
    if not ruta_ini.is_file():
        raise ValueError("falta song.ini: es obligatorio para construir el .sng")

    metadatos = _metadatos_desde_ini(ruta_ini)
    if clave is None:
        clave = os.urandom(16)
    if len(clave) != 16:
        raise ValueError("clave xor debe tener 16 bytes")

    # archivos empaquetados (excepto song.ini, cuyos datos van como metadatos)
    archivos: list[tuple[str, bytes]] = []
    for ruta in archivos_origen:
        if ruta.name.lower() == "song.ini":
            continue
        nombre = ruta.name.lower()
        _validar_nombre(nombre)
        archivos.append((nombre, ruta.read_bytes()))

    bloque_metadatos = _pares_metadatos(metadatos)  # u64 count + pares
    header_len = 6 + 4 + 16
    meta_len = len(bloque_metadatos)  # bytes tras el campo: count u64 + pares
    entries_len = sum(1 + len(nombre.encode("utf-8")) + 16 for nombre, _d in archivos)
    file_meta_len = 8 + entries_len  # bytes tras el campo: u64 count + entradas
    data_start = header_len + 8 + meta_len + 8 + file_meta_len + 8
    offset = data_start
    indice: list[tuple[str, int, int]] = []
    for nombre, datos in archivos:
        indice.append((nombre, len(datos), offset))
        offset += len(datos)
    entries = _entradas_indice(indice)
    data_len = sum(len(d) for _n, d in archivos)

    buffer = bytearray()
    buffer += MAGIC
    buffer += struct.pack("<I", VERSION)
    buffer += clave
    buffer += struct.pack("<Q", meta_len)
    buffer += bloque_metadatos
    buffer += struct.pack("<Q", file_meta_len)
    buffer += struct.pack("<Q", len(archivos))
    buffer += entries
    buffer += struct.pack("<Q", data_len)
    for _nombre, datos in archivos:
        buffer += _masked_bytes(datos, clave)

    if destino is None:
        destino = carpeta.parent / (carpeta.name + ".sng")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(bytes(buffer))
    return destino


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("Uso: python -m chartforge.sng <carpeta-de-cancion> [destino.sng]")
        return 2
    try:
        salida = exportar_sng(Path(argv[0]), Path(argv[1]) if len(argv) > 1 else None)
    except (ValueError, FileNotFoundError) as error:
        print(f"ERROR: {error}")
        return 1
    kb = salida.stat().st_size // 1024
    print(f"OK: {salida} ({kb} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI: entrada de archivos, validación y cola de conversiones.

Una canción por vez; mensajes en español. Sin navegador, sin nube.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

from chartforge import pipeline
import chartforge.config as config
from chartforge.config import cargar_config

EXTENSIONES_PERMITIDAS = (".mp3", ".flac")
DURACION_MAXIMA_S = 1200  # 20 minutos
TAMANO_MAXIMO_MB = 200


class ErrorEntrada(Exception):
    """Entrada inválida; `.mensaje` es un texto humano en español."""

    @property
    def mensaje(self) -> str:
        return str(self)


def _ffprobe_duracion(ruta: Path) -> float:
    """Duración en segundos según ffprobe; lanza ErrorEntrada si no decodifica."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError as e:
        raise ErrorEntrada("no encontre ffprobe/ffmpeg en el PATH; instalarlos primero") from e
    if out.returncode != 0:
        raise ErrorEntrada(f'"{ruta.name}" no se puede decodificar como MP3/FLAC')
    try:
        return float(out.stdout.strip().splitlines()[-1])
    except ValueError:
        raise ErrorEntrada(f'"{ruta.name}" no declaro duracion legible')


def validar_archivo(ruta: Path) -> None:
    """Valida el archivo de entrada; lanza ErrorEntrada si algo no cumple."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorEntrada(f"No existe el archivo: {ruta}")
    if ruta.suffix.lower() not in EXTENSIONES_PERMITIDAS:
        raise ErrorEntrada(f'Formato no soportado: "{ruta.name}" (solo .mp3 y .flac)')
    peso_mb = ruta.stat().st_size / (1024 * 1024)
    if peso_mb > TAMANO_MAXIMO_MB:
        raise ErrorEntrada(f'"{ruta.name}" pesa {peso_mb:.0f} MB (maximo {TAMANO_MAXIMO_MB} MB)')
    duracion = _ffprobe_duracion(ruta)
    if duracion > DURACION_MAXIMA_S:
        raise ErrorEntrada(f'"{ruta.name}" dura {duracion / 60:.1f} min (maximo {DURACION_MAXIMA_S // 60} min)')


_PREFIJO_NUMERICO = re.compile(r"^\d+(\.\d+)?[_\s\-]*")
_ESPACIOS = re.compile(r"\s+")
_MENU_DASH = re.compile(r"\s+[-]\s+")


def parsear_titulo_artista(nombre_archivo: str) -> tuple[str, str]:
    """Adivina (titulo, artista) desde el nombre del archivo, sin basura.

    Quita prefijos numericos ("99", "99.9") y marcas de sitio ("spotdown.org"),
    convierte underscores en espacios y divide por " - " cuando existe.
    Función pura (sin E/S).
    """
    nombre = Path(nombre_archivo).stem
    nombre = _PREFIJO_NUMERICO.sub("", nombre)
    nombre = nombre.replace("spotdown.org", "").replace("spotdown", "")
    nombre = _ESPACIOS.sub(" ", nombre.replace("_", " ")).strip(" - ")
    partes = _MENU_DASH.split(nombre)
    if len(partes) >= 2:
        artista = partes[0].strip() or "Desconocido"
        titulo = " - ".join(partes[1:]).strip() or "Desconocido"
        return titulo, artista
    if not nombre:
        return "Desconocido", "Desconocido"
    return nombre, "Desconocido"


def confirmar_titulo_artista(titulo: str, artista: str) -> tuple[str, str]:
    """Muestra `Artista - Titulo`; Enter acepta el valor por defecto."""
    artista_nuevo = input(f"Artista [{artista}]: ").strip() or artista
    titulo_nuevo = input(f"Titulo [{titulo}]: ").strip() or titulo
    return titulo_nuevo, artista_nuevo


def _salida_de_config(cfg: dict) -> Path:
    """Convierte `[salida] carpeta` de config.ini en ruta absoluta.

    Lanza ErrorEntrada (mensaje en español) si la carpeta es vacía, absoluta,
    intenta salir del proyecto (..) o trae caracteres ilegales de Windows.
    """
    carpeta = str(cfg["salida"]["carpeta"]).strip().strip('"')
    partes = Path(carpeta)
    if (
        not carpeta
        or partes.is_absolute()
        or ".." in partes.parts
        or any(c in ':*?"<>|' for c in carpeta)
    ):
        raise ErrorEntrada(f'[salida] carpeta invalida en config.ini: "{carpeta}"')
    return config.RUTA_PROYECTO / carpeta


def main(args: list[str]) -> int:
    """Procesa cada archivo en orden. Exit 0 si todos ok; 1 si alguno falla."""
    pipeline.limpiar_tmp_pendiente()  # al arrancar no hay jobs validos (una cancion a la vez)
    try:
        cfg = cargar_config(str(config.RUTA_PROYECTO / "config.ini"))
        ruta_salida = _salida_de_config(cfg)  # knob real; valida con mensaje español
    except Exception as error:
        print(f"ERROR: la configuracion (config.ini) no se pudo cargar: {error}")
        return 1
    if not args:
        pegado = input("Pega la ruta de un MP3/FLAC y Enter: ").strip().strip('"')
        if not pegado:
            print("Sin archivo: no se hizo nada.")
            return 0
        args = [pegado]
    codigo = 0
    for arg in args:
        ruta = Path(str(arg).strip().strip('"'))
        try:
            validar_archivo(ruta)
        except ErrorEntrada as error:
            print(f"ERROR: {error.mensaje}")
            codigo = 1
            continue
        titulo, artista = parsear_titulo_artista(ruta.name)
        titulo, artista = confirmar_titulo_artista(titulo, artista)
        try:
            destino = pipeline.run_pipeline(
                ruta, titulo, artista, cfg, reportar=_reportar, salida=ruta_salida
            )
        except (
            ErrorEntrada,
            pipeline.ErrorRecursos,
            FileExistsError,
            ValueError,
            RuntimeError,
            OSError,
            subprocess.SubprocessError,
        ) as error:
            print(f"ERROR: {error}")
            codigo = 1
            continue
        except Exception as error:  # ni un traceback en inglés para el usuario
            print(f"ERROR: error inesperado ({type(error).__name__}): {error}")
            codigo = 1
            continue
        print(f"Listo: {destino}")
    return codigo


def _reportar(evento: str, progreso: float | None, texto: str) -> None:
    """Reporter simple de consola (el pipeline de Task 9 usara otro mas completo)."""
    if texto:
        print(f"[{evento}] {texto}")


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))

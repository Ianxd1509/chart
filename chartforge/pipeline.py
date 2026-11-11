"""Pipeline completo (Task 9): 5 etapas en serie, guardas de recursos y CL.

Orden: adquisicion → stems → letras → charting → empaquetado, con una guarda
de recursos (disco >= 2 GB, RAM libre >= 1.5 GB) ENTRE etapas. Todo el trabajo
intermedio vive en <proyecto>/tmp/job_<id>/; al final la carpeta de cancion se
MUEVE a RUTA_SALIDA (CL). Nada entra a CL hasta que todo salio bien: si algo
falla (o el proceso muere), el finally borra el job y CL queda intacta.

Las etapas se importan a este namespace del módulo para que los tests puedan
parchearlas; config.RUTA_* se lee SIEMPRE en runtime (nunca copiada a inicios
de módulo) por la misma razon.
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import chartforge.config as config
from chartforge.etapas.adquisicion import decodificar
from chartforge.etapas.empaquetado import crear_carpeta_cancion
from chartforge.etapas.letras import transcribir
from chartforge.etapas.stems import extraer_stems
from chartforge.formatos import NOMBRE_CARPETA
from chartforge.chartgen.dificultades import aplicar as aplicar_dificultades
from chartforge.chartgen.drums import generar as generar_bateria
from chartforge.chartgen.features import ExtraccionStems
from chartforge.chartgen.guitar_bass import generar as generar_cuerdas
from chartforge.chartgen.modelo import Letra, PistaCancion
from chartforge.chartgen.secciones import (
    energias_por_compas,
    proponer_frases_sp,
    proponer_secciones,
)
from chartforge.chartgen.vocals import generar as generar_voz

# Guardas de recursos (plan Task 9): items a nivel de módulo, parcheables.
ESPACIO_ARRANQUE_BYTES = 4 * 1024**3    # 4 GB libres para EMPEZAR (plan Global Constraints)
ESPACIO_MINIMO_BYTES = 2 * 1024**3      # 2 GB libres en el disco del proyecto
RAM_MINIMA_BYTES = (3 * 1024**3) // 2   # 1.5 GB de RAM disponible

# Claves de demucs -> instrumento interno (formatos: bateria/guitarra/bajo/voz)
STEMS_DEMUCS_A_INTERNOS = {"drums": "bateria", "bass": "bajo", "other": "guitarra", "vocals": "voz"}

NOMBRE_ETAPAS = ("adquisicion", "stems", "letras", "charting", "empaquetado")
PAUSA_LINEA_S = 2.0  # silencio entre palabras que abre una linea nueva de letra


def _reportador_de_etapa(nombre: str, reportar):
    """Adapta el estilo interno de las etapas al contrato del pipeline.

    Las etapas (Task 4-6) llaman reportar(mensaje) con UN argumento; el
    pipeline les entrega un envoltorio que completa la etapa y percent=None.
    """
    def _enviar(mensaje: str) -> None:
        reportar(nombre, None, mensaje)

    return _enviar


class ErrorRecursos(Exception):
    """Falta espacio/RAM para continuar; el texto es un mensaje en español."""


# ---------------------------------------------------------------------------
# guardas
# ---------------------------------------------------------------------------
def _espacio_libre() -> int:
    """Bytes libres en el disco donde vive el proyecto (leído en runtime)."""
    return shutil.disk_usage(config.RUTA_PROYECTO).free


def _ram_libre() -> int:
    """RAM disponible (psutil diferido: solo existe en la venv)."""
    import psutil

    return int(psutil.virtual_memory().available)


def _guarda(antes_de: str, cfg: dict | None = None) -> None:
    """Lanza ErrorRecursos si no hay disco/RAM suficientes antes de la etapa.

    El mínimo de RAM se toma de cfg[sistema][ram_minima_gb] cuando se pasa una
    config; si no, usa RAM_MINIMA_BYTES (constante parcheable en tests).
    """
    espacio = _espacio_libre()
    ram = _ram_libre()
    ram_minima = RAM_MINIMA_BYTES
    if cfg is not None and "sistema" in cfg:
        try:
            ram_minima = int(float(cfg["sistema"]["ram_minima_gb"]) * 1024**3)
        except (KeyError, ValueError, TypeError):
            ram_minima = RAM_MINIMA_BYTES
    if espacio >= ESPACIO_MINIMO_BYTES and ram >= ram_minima:
        return
    raise ErrorRecursos(
        "recursos insuficientes para continuar antes de {0}: "
        "espacio libre {1:.1f} GB (minimo {2:.0f} GB), RAM libre {3:.1f} GB "
        "(minimo {4:.1f} GB). Libera espacio en disco o cierra programas y "
        "vuelve a intentar.".format(
            antes_de,
            espacio / 1024**3,
            ESPACIO_MINIMO_BYTES / 1024**3,
            ram / 1024**3,
            ram_minima / 1024**3,
        )
    )


# ---------------------------------------------------------------------------
# limpieza de jobs pendientes (CLI la llama al arrancar)
# ---------------------------------------------------------------------------
def _registro_pid_para_job() -> str:
    """Linea `pid create_time` para pid.txt: identifica al proceso con
    EXACTITUD incluso si Windows reutiliza el pid despues (el test de kill
    encontro un pid reutilizado vivo)."""
    pid = os.getpid()
    creat = ""
    try:
        import psutil

        creat = f" {psutil.Process(pid).create_time():.3f}"
    except Exception:
        pass
    return f"{pid}{creat}"


def _pid_del_job(carpeta: Path) -> tuple[int | None, float | None]:
    """(pid, create_time) del pid.txt; (None, None) si falta o es basura."""
    marca = carpeta / "pid.txt"
    if not marca.is_file():
        return None, None
    try:
        partes = marca.read_text(encoding="utf-8").strip().split()
        pid = int(partes[0])
        creat = float(partes[1]) if len(partes) > 1 else None
        return pid, creat
    except (ValueError, OSError, IndexError):
        return None, None


def _proceso_vivo(pid: int, create_time: float | None = None) -> bool:
    """Vivo = el proceso existe DE VERDAD; el pid no basta como prueba.

    En Windows un proceso terminado con handles abiertos del padre (como un
    hijo recien muerto dentro de un Popen) responde True a `pid_exists` e
    incluso da su `create_time`: solo `status()` lanza NoSuchProcess. Si
    ademas se dio `create_time`, se exige que coincidan (discrimina pid
    reutilizado por otro proceso).
    """
    try:
        import psutil
    except ImportError:
        return False
    try:
        proceso = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return True  # existe y no lo podemos ver: por las dudas, no tocarlo
    try:
        proceso.status()
    except psutil.NoSuchProcess:
        return False  # terminado pero su objeto aun vive por los handles
    except psutil.ZombieProcess:
        return False
    except psutil.AccessDenied:
        return True
    if create_time is None:
        return True
    try:
        create_real = proceso.create_time()
    except Exception:
        return False
    return abs(create_real - create_time) < 1.0


def limpiar_tmp_pendiente(imprimir=print) -> None:
    """Limpia <proyecto>/tmp al arrancar la CLI, respetando conversiones vivas.

    Regla una-cancion-a-la-vez (plan Task 9) + leccion del incidente Task 10:
    un job cuyo pid.txt declara un proceso VIVO no se toca (es una conversion
    en curso de otra ventana; se avisa en español) — el resto es basura de
    procesos muertos y se borra: jobs, pid.txt basura y archivos sueltos.
    """
    tmp_raiz = Path(config.RUTA_PROYECTO) / "tmp"
    if not tmp_raiz.is_dir():
        return
    try:
        import psutil  # diferido: solo existe en la venv
    except ImportError:
        psutil = None
    for hijo in tmp_raiz.iterdir():
        if hijo.is_dir():
            pid, create_time = _pid_del_job(hijo)
            if psutil is not None and pid is not None and _proceso_vivo(pid, create_time):
                imprimir(
                    f"Aviso: hay una conversion en curso (job \"{hijo.name}\"). "
                    "No limpio su trabajo intermedio; espera a que termine."
                )
                continue
            shutil.rmtree(hijo, ignore_errors=True)
        else:
            try:
                hijo.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# charting interno
# ---------------------------------------------------------------------------
_TABLA_PROHIBIDA = str.maketrans("", "", '"\\')  # el chart no puede con `"` ni `\`


def construir_letra(palabras: list[tuple[float, str]]) -> Letra | None:
    """Agrupa palabras en lineas: pausa > PAUSA_LINEA_S abre una linea nueva.

    Descarta las comillas dobles y las barras invertidas de cada palabra
    (whisper puede emitirlas; el .chart no las admite y abortaria en el
    ULTIMO paso). Si no queda ninguna palabra real, no hay letra.
    """
    if not palabras:
        return None
    ordenadas = sorted(palabras, key=lambda par: par[0])
    ordenadas = [
        (tiempo, texto.translate(_TABLA_PROHIBIDA).strip())
        for tiempo, texto in ordenadas
    ]
    ordenadas = [par for par in ordenadas if par[1]]
    if not ordenadas:
        return None
    grupos: list[list[tuple[float, str]]] = [[ordenadas[0]]]
    for previa, actual in zip(ordenadas, ordenadas[1:]):
        if actual[0] - previa[0] > PAUSA_LINEA_S:
            grupos.append([actual])
        else:
            grupos[-1].append(actual)
    lineas = [(grupo[0][0], " ".join(palabra for _t, palabra in grupo)) for grupo in grupos]
    return Letra(palabras=ordenadas, lineas=lineas)


def _bpm_de(wav_mix: Path) -> float:
    """BPM del mix por beat_track; 120 si no hay pulso fiable."""
    import numpy as np

    try:
        import librosa  # diferido

        y, sr = librosa.load(str(wav_mix), sr=22050, mono=True)
        tempo, _coincidencias = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(np.ravel(tempo)[0]) if np.size(tempo) else 0.0
    except Exception:
        return 120.0
    if not np.isfinite(bpm) or bpm < 60.0 or bpm > 200.0:
        return 120.0
    return bpm


def _crear_pista(
    mix_wav: Path,
    stems_demucs: dict[str, Path],
    palabras: list[tuple[float, str]],
    informar=print,
) -> PistaCancion:
    """Gemas Expert de los 4 instrumentos + letra, a partir de los stems.

    `informar(mensaje)` avisa por consola cuando un stem queda sin gemas
    (instrumento inaudible): politica de la revision — no se inventa musica,
    pero el usuario se entera de que la pista vacia no fue un error.
    """
    feat = ExtraccionStems(
        ruta_drums=stems_demucs["drums"],
        ruta_bass=stems_demucs["bass"],
        ruta_other=stems_demucs["other"],
        ruta_vocals=stems_demucs["vocals"],
    )
    bpm = _bpm_de(mix_wav)
    letra = construir_letra(palabras)
    experto = {
        "bateria": generar_bateria(feat, bpm),
        "guitarra": generar_cuerdas(feat, "other", bpm),
        "bajo": generar_cuerdas(feat, "bass", bpm),
        "voz": generar_voz(feat, letra, bpm),  # interna: no va como pista .chart
    }
    for instrumento, gemas_exp in experto.items():
        if not gemas_exp:
            informar(
                f"Aviso: no hay {instrumento} detectable en su stem (silencioso): "
                f"los charts de {instrumento} salen vacios. El audio de la "
                "cancion se guarda igual."
            )
    gemas = aplicar_dificultades(experto, bpm)
    try:
        rms = energias_por_compas(mix_wav, bpm)
        frases_sp = proponer_frases_sp(rms, bpm)
        secciones = proponer_secciones(rms)
    except Exception:  # SP/secciones son extra: nunca abortar por ellos
        frases_sp, secciones = [], []
    return PistaCancion(bpm=bpm, letra=letra, gemas=gemas,
                        frases_sp=frases_sp, secciones=secciones)


# ---------------------------------------------------------------------------
# movimiento final
# ---------------------------------------------------------------------------
def _mover_a_cl(carpeta: Path, destino: Path) -> Path:
    """Mueve la carpeta armada en tmp a CL (re-chequeando la no sobreescritura)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():  # pudo aparecer mientras se convertia
        raise FileExistsError(
            f'La carpeta "{destino}" ya existe: no se sobreescribe. '
            "Borra o renombra esa carpeta y vuelve a intentar."
        )
    shutil.move(str(carpeta), str(destino))
    return destino


# ---------------------------------------------------------------------------
# pipeline
# ---------------------------------------------------------------------------
def run_pipeline(
    audio: Path,
    titulo: str,
    artista: str,
    cfg: dict | None = None,
    reportar=None,
    salida: Path | None = None,
) -> Path:
    """Convierte un MP3/FLAC en la carpeta de cancion final (por defecto en CL).

    reportar(etapa, percent|None, mensaje) para cada etapa en orden de
    NOMBRE_ETAPAS; percent es siempre None (el CLI arma el mensaje). `salida`
    es una raiz alternativa pedida por la CLI (config.ini [salida] carpeta);
    por defecto todo va a config.RUTA_SALIDA. Devuelve la carpeta final;
    lanza FileExistsError (carpeta ya existe), ErrorRecursos (guardas de
    disco/RAM) o ValueError/RuntimeError (etapas). El job de tmp se borra
    SIEMPRE (finally), tanto si salio bien como si fallo o se corto.
    """
    reportar = reportar or (lambda *args, **kwargs: None)
    cfg = cfg if cfg is not None else config.cargar_config("")

    espacio = _espacio_libre()
    if espacio < ESPACIO_ARRANQUE_BYTES:  # guarda de ARRANQUE: antes de gastar CPU
        raise ErrorRecursos(
            "recursos insuficientes para empezar: quedan {0:.1f} GB en el disco "
            "(minimo {1:.0f} GB). Libera espacio y vuelve a intentar.".format(
                espacio / 1024**3, ESPACIO_ARRANQUE_BYTES / 1024**3
            )
        )

    raiz_salida = Path(salida) if salida is not None else config.RUTA_SALIDA
    destino = raiz_salida / NOMBRE_CARPETA(artista, titulo)
    if destino.exists():  # verificación temprana: no gastar CPU en nada imposible
        raise FileExistsError(
            f'La carpeta "{destino}" ya existe: no se sobreescribe. '
            "Borra o renombra esa carpeta y vuelve a intentar."
        )

    tmp_raiz = Path(config.RUTA_PROYECTO) / "tmp"
    tmp_raiz.mkdir(parents=True, exist_ok=True)
    job = tmp_raiz / f"job_{uuid.uuid4().hex[:12]}"
    job.mkdir(parents=True)
    (job / "pid.txt").write_text(_registro_pid_para_job(), encoding="utf-8")

    reportar("adquisicion", None, "Decodificando el audio a WAV 44.1 kHz...")
    try:
        mix_wav = decodificar(audio, job / "mix.wav")

        _guarda("stems", cfg)
        reportar("stems", None, "Separando stems con demucs (puede tardar ~1.8x la cancion)...")
        ruta_stems = job / "stems"
        stems_demucs = extraer_stems(
            mix_wav, ruta_stems, cfg, _reportador_de_etapa("stems", reportar)
        )
        faltan = [clave for clave in STEMS_DEMUCS_A_INTERNOS if clave not in stems_demucs]
        if faltan:
            raise RuntimeError(f"demucs no devolvio los stems esperados: {faltan}")
        stems_internos = {
            interno: stems_demucs[clave]
            for clave, interno in STEMS_DEMUCS_A_INTERNOS.items()
        }

        _guarda("letras", cfg)
        palabras: list[tuple[float, str]] = []
        if cfg["letras"]["activada"]:
            reportar("letras", None, "Transcribiendo la voz con whisper...")
            try:
                palabras = transcribir(
                    stems_demucs["vocals"], cfg, _reportador_de_etapa("letras", reportar)
                )
            except Exception as error:  # sin letra fiable -> #sin-letras y seguir
                reportar("letras", None, f"Aviso: no se pudo transcribir la letra ({error}).")

        _guarda("charting", cfg)
        reportar("charting", None, "Generando gemas de los 4 instrumentos...")
        pista = _crear_pista(
            mix_wav, stems_demucs, palabras,
            informar=lambda mensaje: reportar("charting", None, mensaje),
        )

        _guarda("empaquetado", cfg)
        reportar("empaquetado", None, "Escribiendo song.ini, notes.chart y OGG...")
        carpeta = crear_carpeta_cancion(
            stems_internos, mix_wav, pista, titulo, artista, destino=job,
            audio_origen=Path(audio),
            reportar=_reportador_de_etapa("empaquetado", reportar),
        )
        return _mover_a_cl(carpeta, destino)
    finally:
        shutil.rmtree(job, ignore_errors=True)

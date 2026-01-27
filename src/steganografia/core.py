"""
API principale per le operazioni di steganografia
"""

from PIL import Image

from config.constants import CompressionMode, SteganographyMethod

from .backup import backup_system

# Import DWT
from .dwt.binary_operations import BinarySteganography as DwtBinary
from .dwt.image_operations import ImageSteganography as DwtImage
from .dwt.message_operations import MessageSteganography as DwtMessage
from .file_utils import _save_image

# Import LSB
from .lsb.binary_operations import BinarySteganography as LsbBinary
from .lsb.image_operations import ImageSteganography as LsbImage
from .lsb.message_operations import MessageSteganography as LsbMessage

# Import PVD
from .pvd.binary_operations import BinarySteganography as PvdBinary
from .pvd.image_operations import ImageSteganography as PvdImage
from .pvd.message_operations import MessageSteganography as PvdMessage

# Esporta le costanti per compatibilità
NO_ZIP = CompressionMode.NO_ZIP
FILE = CompressionMode.FILE
DIR = CompressionMode.DIR


# API per le stringhe
def hide_message(
    img: Image.Image,
    message: str,
    backup_file: str | None = None,
    method: str = SteganographyMethod.LSB,
) -> tuple[Image.Image, dict]:
    """
    Nasconde una stringa in un'immagine. Restituisce (immagine, metriche)

    Args:
        img: Immagine host
        message: Messaggio da nascondere
        backup_file: File di backup opzionale
        method: Metodo di steganografia ('lsb', 'dwt', 'pvd')
    """
    if method == SteganographyMethod.DWT:
        return DwtMessage.hide_message(img, message, backup_file)
    elif method == SteganographyMethod.PVD:
        return PvdMessage.hide_message(img, message, backup_file)
    else:  # Default: LSB
        return LsbMessage.hide_message(img, message, backup_file)


def get_message(
    img: Image.Image,
    backup_file: str | None = None,
    method: str = SteganographyMethod.LSB,
) -> str:
    """
    Recupera una stringa da un'immagine

    Args:
        img: Immagine contenente il messaggio
        backup_file: File di backup opzionale
        method: Metodo di steganografia usato ('lsb', 'dwt', 'pvd')
    """
    if method == SteganographyMethod.DWT:
        return DwtMessage.get_message(img, backup_file)
    elif method == SteganographyMethod.PVD:
        return PvdMessage.get_message(img, backup_file)
    else:  # Default: LSB
        return LsbMessage.get_message(img, backup_file)


# API per le immagini
def hide_image(
    host_img: Image.Image,
    secret_img: Image.Image,
    lsb: int = 0,
    msb: int = 8,
    div: float = 0,
    backup_file: str | None = None,
    method: str = SteganographyMethod.LSB,
) -> tuple[Image.Image, int, int, float, int, int, dict]:
    """
    Nasconde un'immagine in un'altra. Restituisce (immagine, lsb, msb, div, width, height, metriche)

    Args:
        host_img: Immagine host
        secret_img: Immagine da nascondere
        lsb, msb, div: Parametri per LSB (ignorati in DWT/PVD)
        backup_file: File di backup opzionale
        method: Metodo di steganografia ('lsb', 'dwt', 'pvd')
    """
    if method == SteganographyMethod.DWT:
        return DwtImage.hide_image(host_img, secret_img, backup_file)
    elif method == SteganographyMethod.PVD:
        return PvdImage.hide_image(host_img, secret_img, backup_file)
    else:  # Default: LSB
        return LsbImage.hide_image(host_img, secret_img, lsb, msb, div, backup_file)


def get_image(
    img: Image.Image,
    output_path: str,
    lsb: int | None = None,
    msb: int | None = None,
    div: float | None = None,
    width: int | None = None,
    height: int | None = None,
    backup_file: str | None = None,
    method: str = SteganographyMethod.LSB,
) -> Image.Image:
    """
    Recupera un'immagine da un'altra

    Args:
        img: Immagine contenente l'immagine nascosta
        output_path: Percorso di output
        lsb, msb, div, width, height: Parametri di recupero
        backup_file: File di backup opzionale
        method: Metodo di steganografia usato ('lsb', 'dwt', 'pvd')
    """
    if method == SteganographyMethod.DWT:
        return DwtImage.get_image(
            img, output_path, width=width, height=height, backup_file=backup_file
        )
    elif method == SteganographyMethod.PVD:
        return PvdImage.get_image(
            img, output_path, width=width, height=height, backup_file=backup_file
        )
    else:  # Default: LSB
        return LsbImage.get_image(
            img, output_path, lsb, msb, div, width, height, backup_file
        )


# API per i file binari
def hide_bin_file(
    img: Image.Image,
    file_path: str,
    compression_mode: int = NO_ZIP,
    n: int = 0,
    div: float = 0,
    backup_file: str | None = None,
    method: str = SteganographyMethod.LSB,
) -> tuple[Image.Image, int, float, int, dict]:
    """
    Nasconde un file binario in un'immagine. Restituisce (immagine, n, div, size, metriche)

    Args:
        img: Immagine host
        file_path: Percorso del file da nascondere
        compression_mode: Modalità di compressione (0=nessuna, 1=file, 2=directory)
        n, div: Parametri per LSB (ignorati in DWT/PVD)
        backup_file: File di backup opzionale
        method: Metodo di steganografia ('lsb', 'dwt', 'pvd')
    """
    if method == SteganographyMethod.DWT:
        return DwtBinary.hide_binary_file(img, file_path, backup_file)
    elif method == SteganographyMethod.PVD:
        return PvdBinary.hide_binary_file(img, file_path, backup_file)
    else:  # Default: LSB
        return LsbBinary.hide_binary_file(
            img, file_path, compression_mode, n, div, backup_file
        )


def get_bin_file(
    img: Image.Image,
    output_path: str,
    compression_mode: int | None = None,
    n: int | None = None,
    div: float | None = None,
    size: int | None = None,
    backup_file: str | None = None,
    method: str = SteganographyMethod.LSB,
) -> None:
    """
    Recupera un file binario da un'immagine

    Args:
        img: Immagine contenente il file
        output_path: Percorso di output
        compression_mode, n, div, size: Parametri di recupero
        backup_file: File di backup opzionale
        method: Metodo di steganografia usato ('lsb', 'dwt', 'pvd')
    """
    if method == SteganographyMethod.DWT:
        DwtBinary.get_binary_file(img, output_path, size=size, backup_file=backup_file)
    elif method == SteganographyMethod.PVD:
        return PvdBinary.get_binary_file(
            img, output_path, size=size, backup_file=backup_file
        )
    else:  # Default: LSB
        LsbBinary.get_binary_file(
            img, output_path, compression_mode, n, div, size, backup_file
        )


# API per il backup
def load_backup_data(backup_file: str):
    """Carica i parametri da un file di backup"""
    return backup_system.load_backup_data(backup_file)


def get_last_params(data_type: str):
    """Ottiene gli ultimi parametri usati"""
    return backup_system.get_last_params(data_type)


def save_image(img: Image.Image, file_path: str) -> bool:
    """Salva un'immagine su disco"""
    return _save_image(img, file_path)

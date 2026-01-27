"""
Utilità per operazioni sui file e compressione
"""

import zipfile
from os import remove, walk
from os.path import exists, getsize, join, relpath

from config.constants import CompressionMode


def find_div(dim: int, file_path: str, n: int) -> float:
    """Calcola il valore di divisione per la distribuzione dei bit"""
    image_dim = dim * n
    div = (image_dim - n) / (getsize(file_path) * 8)
    return div


def zip_directory(path: str, ziph: zipfile.ZipFile) -> None:
    """Comprime una directory"""
    for root, _, files in walk(path):
        for file in files:
            file_path = join(root, file)
            arcname = relpath(file_path, path)
            ziph.write(file_path, arcname)


def compress_file(file_path: str, compression_mode: int) -> str:
    """
    Comprime un file o directory secondo la modalità specificata

    Args:
        file_path: Percorso del file o directory da comprimere
        compression_mode: Modalità di compressione (NO_ZIP, FILE, DIR)

    Returns:
        Percorso del file risultante (originale o compresso)
    """
    if compression_mode == CompressionMode.NO_ZIP:
        return file_path
    if compression_mode == CompressionMode.FILE:
        print("Compressione file...")
        with zipfile.ZipFile("tmp.zip", "w") as zf:
            zf.write(file_path)
        print("File compresso")
        return "tmp.zip"

    print("Compressione directory...")
    with zipfile.ZipFile("tmp.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        zip_directory(file_path, zipf)
    print("Directory compressa")
    return "tmp.zip"


def cleanup_temp_files() -> None:
    """Rimuove i file temporanei di compressione"""
    if exists("tmp.zip"):
        remove("tmp.zip")


def _save_image(img, file_path: str) -> bool:
    """Salva un'immagine PIL su disco"""
    try:
        img.save(file_path)
        print(f"Immagine salvata come {file_path}")
        return True
    except Exception as e:
        print(f"Errore nel salvataggio: {e}")
        return False

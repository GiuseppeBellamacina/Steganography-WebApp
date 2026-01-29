"""
Operazioni di steganografia per i file binari
"""

import os
import zipfile
from os.path import getsize

import numpy as np
from PIL import Image

from config.constants import CompressionMode, DataType, ErrorMessages

from ..backup import backup_system
from ..bit_operations import set_last_n_bits, string_to_bytes
from ..file_utils import cleanup_temp_files, compress_file, find_div
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class BinarySteganography:
    """Classe per operazioni di steganografia su file binari"""

    @staticmethod
    def hide_binary_file(
        img: Image.Image,
        file_path: str,
        compression_mode: int = CompressionMode.NO_ZIP,
        n: int = 0,
        div: float = 0,
        backup_file: str | None = None,
    ) -> tuple[Image.Image, int, float, int, dict, float]:
        """
        Nasconde un file binario o una cartella in un'immagine

        Args:
            img: Immagine dove nascondere il file
            file_path: Percorso del file da nascondere
            compression_mode: Modalità di compressione
            n: Numero di bit da modificare per pixel
            div: Divisore per la distribuzione
            backup_file: File dove salvare i parametri

        Returns:
            Tupla con (immagine_risultato, n_finale, div_finale, dimensione_file, metrics)
            dove metrics è un dizionario con 'ssim' e 'psnr'
        """
        # Validazione parametri
        ParameterValidator.validate_n(n)
        ParameterValidator.validate_compression_mode(compression_mode)

        # Determina canali
        channels = 3
        if img.mode == "RGBA":
            channels = 4
        if img.mode not in ["RGB", "RGBA"]:
            img = img.convert("RGB")

        # Comprimi file se richiesto
        working_file = compress_file(file_path, compression_mode)

        try:
            # Ottieni dimensione file
            total_bytes = getsize(working_file)

            # Calcolo automatico di n se necessario
            if n == 0:
                n = 1
                while (img.width * img.height) * channels * n < total_bytes * 8:
                    n += 1
                    if n > 8:
                        raise ValueError(
                            ErrorMessages.IMAGE_TOO_SMALL_FILE.format(
                                file_size=total_bytes,
                                width=img.width,
                                height=img.height,
                            )
                        )

            # Verifica dimensioni
            ParameterValidator.validate_image_size_for_file(
                img, total_bytes, n, channels
            )

            # Converte immagine in array
            arr = np.array(img).flatten().copy()
            total_pixels_ch = len(arr)

            # Calcola o valida DIV
            if div == 0:
                div = find_div(total_pixels_ch, working_file, n)
            else:
                ParameterValidator.validate_div_for_file(
                    div, total_pixels_ch, total_bytes, n
                )

            # Inizia a nascondere il file
            print("Nascondendo file...")
            rsv = ""
            ind, pos = 0.0, 0

            # Leggi file
            with open(working_file, "rb") as f:
                f.seek(0)
                for _ in range(total_bytes):
                    byte = f.read(1)
                    bits = format(ord(byte), "08b")
                    bits = rsv + bits
                    rsv = ""
                    while len(bits) >= n:
                        tmp = bits[:n]
                        bits = bits[n:]
                        # Setta gli ultimi n bit del pixel
                        arr[pos] = set_last_n_bits(arr[pos], tmp, n)
                        ind += div
                        pos = round(ind)
                    if len(bits) > 0:
                        rsv = bits

            # Gestisci bit rimanenti
            while len(rsv) > 0:
                tmp = rsv[:n]
                rsv = rsv[n:]
                arr[pos] = set_last_n_bits(arr[pos], tmp, n)
                ind += div
                pos = round(ind)

            percentage = format(
                ((total_bytes * 8) / ((img.width * img.height) * channels * n)) * 100,
                ".2f",
            )
            print(
                f"TERMINATO - Percentuale di pixel usati con n={n} e div={div}: {percentage}%"
            )

            # Crea immagine risultato
            result_img = Image.fromarray(arr.reshape(img.height, img.width, channels))

            # Calcola metriche di qualità (SSIM e PSNR)
            # Per RGB confronto con l'originale, per RGBA converto entrambe in RGB
            img_for_metrics = img.convert("RGB") if img.mode == "RGBA" else img
            result_for_metrics = (
                result_img.convert("RGB") if result_img.mode == "RGBA" else result_img
            )
            metrics = QualityMetrics.calculate_metrics(
                img_for_metrics, result_for_metrics
            )
            print(
                f"Metriche di qualità - SSIM: {metrics['ssim']:.4f}, PSNR: {metrics['psnr']:.2f} dB"
            )

            # Salva i parametri per il recupero
            params = {
                "n": n,
                "div": div,
                "size": total_bytes,
                "zipMode": compression_mode,
                "method": "binary",
                "original_file": file_path,
                "channels": channels,
            }
            backup_system.save_backup_data(DataType.BINARY, params, backup_file)

            return (result_img, n, div, total_bytes, metrics, float(percentage))

        finally:
            # Pulizia file temporanei
            if compression_mode != CompressionMode.NO_ZIP:
                cleanup_temp_files()

    @staticmethod
    def get_binary_file(
        img: Image.Image,
        output_path: str,
        compression_mode: int | None = None,
        n: int | None = None,
        div: float | None = None,
        size: int | None = None,
        backup_file: str | None = None,
    ) -> None:
        """
        Recupera un file binario da un'immagine

        Args:
            img: Immagine che contiene il file
            output_path: Percorso dove salvare il file recuperato
            compression_mode, n, div, size: Parametri per il recupero
            backup_file: File di backup dei parametri
        """
        # Recupera parametri automaticamente se non forniti
        if any(param is None for param in [compression_mode, n, div, size]):
            print("Alcuni parametri mancanti, cercando nei backup...")

            # Controlla se esistono parametri di backup
            backup_data = None
            if backup_file:
                backup_data = backup_system.load_backup_data(backup_file)

            # Se non ci sono backup file, controlla le variabili locali
            if not backup_data:
                recent_params = backup_system.get_last_params(DataType.BINARY)
                if recent_params:
                    print(
                        "Usando parametri dall'ultima operazione di occultamento file binari"
                    )
                    backup_data = {"type": DataType.BINARY, "params": recent_params}

            if backup_data and "params" in backup_data:
                params = backup_data["params"]
                compression_mode = (
                    compression_mode
                    if compression_mode is not None
                    else params.get("zipMode")
                )
                n = n if n is not None else params.get("n")
                div = div if div is not None else params.get("div")
                size = size if size is not None else params.get("size")
                print(
                    f"Parametri recuperati: zipMode={compression_mode}, n={n}, div={div:.2f}, size={size}"
                )
            else:
                raise ValueError(ErrorMessages.PARAMS_MISSING)

        # Verifica parametri
        ParameterValidator.validate_recovery_params(compression_mode, n, div, size)

        # Assert per il type checker
        assert (
            compression_mode is not None
            and n is not None
            and div is not None
            and size is not None
        )

        # Validazioni specifiche
        ParameterValidator.validate_n(n)
        ParameterValidator.validate_compression_mode(compression_mode)

        print("Cercando file...")

        # Inizia recupero file
        arr = np.array(img).flatten().copy()
        bits, res = "", ""
        ind, pos = 0.0, 0
        diff = size * 8
        err = round(size * 8 / n)

        # Gestione file compresso
        working_output = output_path
        if compression_mode != CompressionMode.NO_ZIP:
            res = output_path
            working_output = "tmp.zip"

        with open(working_output, "wb") as file:
            for _ in range(err):
                if diff < n:
                    bits += format(arr[pos], "08b")[-diff:]
                else:
                    bits += format(arr[pos], "08b")[-n:]

                if len(bits) >= 1024:
                    wr = bits[:1024]
                    wr = string_to_bytes(wr)
                    file.write(wr)
                    bits = bits[1024:]

                ind += div
                pos = round(ind)

            if bits:
                bits = string_to_bytes(bits)
                file.write(bits)

        # Gestione decompressione
        if compression_mode == CompressionMode.NO_ZIP:
            print(f"FILE TROVATO - File salvato come {working_output}")
        elif compression_mode == CompressionMode.FILE:
            BinarySteganography._decompress_file(working_output, res)
        else:  # CompressionMode.DIR
            BinarySteganography._decompress_directory(working_output, res)

    @staticmethod
    def _decompress_file(zip_path: str, output_path: str) -> None:
        """Decomprime un file singolo"""
        print("Decompressione file...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                old_path = zf.namelist()[0]
                file_data = zf.read(old_path)
            os.remove(zip_path)

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr(output_path, file_data)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall()
            os.remove(zip_path)
            print(f"FILE TROVATO - File salvato come {output_path}")
        except Exception as e:
            raise ValueError(f"Errore durante l'estrazione del file: {e}")

    @staticmethod
    def _decompress_directory(zip_path: str, output_path: str) -> None:
        """Decomprime una directory"""
        print("Decompressione directory...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(output_path)
            os.remove(zip_path)
            print(f"DIRECTORY TROVATA - Directory salvata come {output_path}")
        except Exception as e:
            raise ValueError(f"Errore durante l'estrazione della directory: {e}")

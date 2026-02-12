"""
Operazioni di steganografia per file binari usando PVD (Pixel Value Differencing)
"""

import numpy as np
from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..metrics import QualityMetrics


class BinarySteganography:
    """Classe per operazioni di steganografia su file binari usando PVD"""

    # === Quantization ranges ===
    RANGES_QUALITY = [
        (0, 7, 2),
        (8, 15, 3),
        (16, 31, 3),
        (32, 63, 4),
        (64, 127, 4),
    ]

    RANGES_CAPACITY = [
        (0, 7, 3),
        (8, 15, 3),
        (16, 31, 4),
        (32, 63, 5),
        (64, 127, 6),
        (128, 255, 7),
    ]

    # === Default configuration ===
    RANGES = RANGES_QUALITY
    PAIR_STEP: int = 1
    CHANNELS = [0, 1, 2]

    @staticmethod
    def _get_range_capacity(diff: int) -> tuple[int, int, int]:
        """Ottiene la capacità in bit per una data differenza di pixel"""
        abs_diff = abs(diff)
        for lower, upper, capacity in BinarySteganography.RANGES:
            if lower <= abs_diff <= upper:
                return lower, upper, capacity
        return 128, 255, 7  # Default al range più alto

    @staticmethod
    def _embed_in_pair(pixel1: int, pixel2: int, bits: str) -> tuple[int, int]:
        """
        Nasconde bit in una coppia di pixel usando PVD

        Args:
            pixel1, pixel2: Valori dei pixel (0-255)
            bits: Stringa di bit da nascondere

        Returns:
            Tupla con i nuovi valori dei pixel
        """
        diff = pixel2 - pixel1
        lower, upper, capacity = BinarySteganography._get_range_capacity(diff)

        # Limita i bit alla capacità del range
        bits = bits[:capacity]
        if len(bits) == 0:
            return pixel1, pixel2

        # Converte i bit in valore decimale
        decimal_value = int(bits.ljust(capacity, "0"), 2)

        # Calcola la nuova differenza
        new_diff = lower + decimal_value

        #  CRITICAL: clamp per auto-sincronizzazione
        new_diff = min(new_diff, upper)

        # Mantiene il segno della differenza originale
        if diff < 0:
            new_diff = -new_diff

        # Calcola i nuovi pixel
        m = abs(new_diff) - abs(diff)

        #  Early return se nessuna modifica
        if m == 0:
            return pixel1, pixel2

        if diff % 2 == 0:  # diff pari
            new_pixel1 = pixel1 - m // 2
            new_pixel2 = pixel2 + m - m // 2
        else:  # diff dispari
            new_pixel1 = pixel1 - (m + 1) // 2
            new_pixel2 = pixel2 + m - (m + 1) // 2

        # Clipping per rimanere nel range valido
        new_pixel1 = max(0, min(255, new_pixel1))
        new_pixel2 = max(0, min(255, new_pixel2))

        return new_pixel1, new_pixel2

    @staticmethod
    def _extract_from_pair(pixel1: int, pixel2: int) -> str:
        """
        Estrae bit da una coppia di pixel usando PVD

        Returns:
            Stringa di bit estratti
        """
        diff = pixel2 - pixel1
        lower, upper, capacity = BinarySteganography._get_range_capacity(diff)

        # Calcola il valore nascosto
        value = abs(diff) - lower

        #  Clamp difensivo
        value = max(0, min(value, (1 << capacity) - 1))

        # Converte in binario
        bits = format(value, f"0{capacity}b")
        return bits

    @staticmethod
    def hide_binary_file(
        img: Image.Image,
        file_path: str,
        backup_file: str | None = None,
        **kwargs,  # Ignora compression_mode, n, div per compatibilità API
    ) -> tuple[Image.Image, int, float, int, dict, float]:
        """
        Nasconde un file binario in un'immagine usando PVD

        Args:
            img: Immagine host
            file_path: Percorso del file da nascondere
            backup_file: File di backup opzionale
        """
        with open(file_path, "rb") as f:
            file_data = f.read()

        file_size = len(file_data)
        file_binary = "".join(format(byte, "08b") for byte in file_data)

        magic_header = "1010101011110000"
        size_binary = format(file_size, "032b")
        terminator = "1111000011110000"  # Terminatore complesso (16 bit)
        full_payload = magic_header + size_binary + file_binary + terminator

        if img.mode != "RGB":
            img = img.convert("RGB")

        print(f"Nascondendo file binario ({file_size} bytes) con PVD...")
        original_img = img.copy()
        img_array = np.array(img, dtype=np.int32).copy()

        bit_index = 0
        height, width, _ = img_array.shape

        for channel in BinarySteganography.CHANNELS:
            for row in range(height):
                for col in range(0, width - 1, 2 * BinarySteganography.PAIR_STEP):
                    if bit_index >= len(full_payload):
                        break

                    pixel1 = int(img_array[row, col, channel])
                    pixel2 = int(
                        img_array[row, col + BinarySteganography.PAIR_STEP, channel]
                    )

                    _, _, capacity = BinarySteganography._get_range_capacity(
                        pixel2 - pixel1
                    )
                    bits_to_embed = full_payload[bit_index : bit_index + capacity]

                    if bits_to_embed:
                        new_p1, new_p2 = BinarySteganography._embed_in_pair(
                            pixel1, pixel2, bits_to_embed
                        )
                        img_array[row, col, channel] = new_p1
                        img_array[row, col + BinarySteganography.PAIR_STEP, channel] = (
                            new_p2
                        )
                        # BUG FIX 2: Incrementa di capacity perché ljust() scrive sempre capacity bit
                        bit_index += capacity

                if bit_index >= len(full_payload):
                    break
            if bit_index >= len(full_payload):
                break

        if bit_index < len(full_payload):
            raise ValueError(
                ErrorMessages.IMAGE_TOO_SMALL_FILE.format(
                    file_size=file_size, width=img.width, height=img.height
                )
            )

        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(img_array, mode="RGB")

        # Calcola percentuale di bit usati
        total_bits_host = height * width * len(BinarySteganography.CHANNELS)
        percentage = format((bit_index / total_bits_host) * 100, ".2f")
        print(
            f"TERMINATO - Percentuale di pixel usati con PVD: {percentage}% ({bit_index}/{total_bits_host} bit)"
        )

        # Salva parametri (sempre nella cache, opzionalmente su file)
        # Determina se RANGES è quality o capacity
        is_quality = BinarySteganography.RANGES == BinarySteganography.RANGES_QUALITY
        params = {
            "method": "pvd",
            "size": file_size,
            "pair_step": BinarySteganography.PAIR_STEP,
            "channels": BinarySteganography.CHANNELS,
            "ranges_type": "quality" if is_quality else "capacity",
        }
        backup_system.save_backup_data(DataType.BINARY, params, backup_file)

        metrics = QualityMetrics.calculate_metrics(original_img, result_img)
        print("File nascosto con successo usando PVD")

        return result_img, 1, 0.0, file_size, metrics, float(percentage)

    @staticmethod
    def get_binary_file(
        img: Image.Image,
        output_path: str,
        backup_file: str | None = None,
        # Parametri manuali opzionali
        ranges_type: str | None = None,  # "quality" o "capacity"
        pair_step: int | None = None,
        channels: list[int] | None = None,
        **kwargs,  # Ignora n, div per compatibilità API
    ) -> None:
        """Recupera un file binario da un'immagine usando PVD"""

        # Inizializza con valori di default
        final_pair_step: int = BinarySteganography.PAIR_STEP
        final_channels: list[int] = BinarySteganography.CHANNELS

        # PRIORITÀ: parametri manuali > backup file > cache recente > default
        if ranges_type is not None or pair_step is not None or channels is not None:
            print("Usando parametri MANUALI forniti dall'interfaccia")
            # Usa parametri manuali se forniti, altrimenti default
            if ranges_type == "quality":
                BinarySteganography.RANGES = BinarySteganography.RANGES_QUALITY
            elif ranges_type == "capacity":
                BinarySteganography.RANGES = BinarySteganography.RANGES_CAPACITY
            final_pair_step = (
                pair_step if pair_step is not None else BinarySteganography.PAIR_STEP
            )
            final_channels = (
                channels if channels is not None else BinarySteganography.CHANNELS
            )
        else:
            # Carica parametri da backup o cache

            if backup_file:
                backup_data = backup_system.load_backup_data(backup_file)
                if backup_data and "params" in backup_data:
                    final_pair_step = backup_data["params"].get(
                        "pair_step", final_pair_step
                    )
                    final_channels = backup_data["params"].get(
                        "channels", final_channels
                    )
                    # Carica RANGES
                    ranges_type = backup_data["params"].get("ranges_type", "quality")
                    BinarySteganography.RANGES = (
                        BinarySteganography.RANGES_QUALITY
                        if ranges_type == "quality"
                        else BinarySteganography.RANGES_CAPACITY
                    )
            else:
                recent_params = backup_system.get_last_params(DataType.BINARY)
                if recent_params:
                    print("Usando parametri dall'ultima operazione di nascondimento")
                    final_pair_step = recent_params.get("pair_step", final_pair_step)
                    final_channels = recent_params.get("channels", final_channels)
                    # Carica RANGES dalla cache
                    ranges_type = recent_params.get("ranges_type", "quality")
                    BinarySteganography.RANGES = (
                        BinarySteganography.RANGES_QUALITY
                        if ranges_type == "quality"
                        else BinarySteganography.RANGES_CAPACITY
                    )

        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Recuperando file binario con PVD...")
        img_array = np.array(img, dtype=np.int32)

        extracted_bits = []
        height, width, _ = img_array.shape

        for channel in final_channels:
            for row in range(height):
                for col in range(0, width - 1, 2 * final_pair_step):
                    pixel1 = int(img_array[row, col, channel])
                    pixel2 = int(img_array[row, col + final_pair_step, channel])

                    bits = BinarySteganography._extract_from_pair(pixel1, pixel2)
                    extracted_bits.append(bits)

        full_binary = "".join(extracted_bits)
        magic_header = "1010101011110000"

        header_pos = full_binary.find(magic_header)
        if header_pos == -1:
            raise ValueError("Nessun file trovato nell'immagine")

        size_start = header_pos + 16
        size_end = size_start + 32
        file_size_binary = full_binary[size_start:size_end]
        file_size = int(file_size_binary, 2)

        file_start = size_end
        file_end = file_start + (file_size * 8)
        file_binary = full_binary[file_start:file_end]

        file_bytes = bytearray()
        for i in range(0, len(file_binary), 8):
            byte = file_binary[i : i + 8]
            if len(byte) == 8:
                file_bytes.append(int(byte, 2))

        with open(output_path, "wb") as f:
            f.write(file_bytes)

        print(f"File recuperato e salvato in {output_path}")

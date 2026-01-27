"""
Operazioni di steganografia per messaggi usando PVD (Pixel Value Differencing)
"""

import numpy as np
from PIL import Image

from config.constants import DataType

from ..backup import backup_system
from ..bit_operations import binary_convert, binary_convert_back
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class MessageSteganography:
    """Classe per operazioni di steganografia su messaggi usando PVD"""

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
        for lower, upper, capacity in MessageSteganography.RANGES:
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
        lower, upper, capacity = MessageSteganography._get_range_capacity(diff)

        # Limita i bit alla capacità del range
        bits = bits[:capacity]
        if len(bits) == 0:
            return pixel1, pixel2

        # Converte i bit in valore decimale
        decimal_value = int(bits.ljust(capacity, "0"), 2)

        # Calcola la nuova differenza
        new_diff = lower + decimal_value

        # ⚠️ CRITICAL: clamp per auto-sincronizzazione
        new_diff = min(new_diff, upper)

        # Mantiene il segno della differenza originale
        if diff < 0:
            new_diff = -new_diff

        # Calcola i nuovi pixel
        m = abs(new_diff) - abs(diff)

        # 🔧 Early return se nessuna modifica
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
        lower, upper, capacity = MessageSteganography._get_range_capacity(diff)

        # Calcola il valore nascosto
        value = abs(diff) - lower

        # 🔧 Clamp difensivo
        value = max(0, min(value, (1 << capacity) - 1))

        # Converte in binario
        bits = format(value, f"0{capacity}b")
        return bits

    @staticmethod
    def hide_message(
        img: Image.Image, message: str, backup_file: str | None = None
    ) -> tuple[Image.Image, dict]:
        """Nasconde una stringa in un'immagine usando PVD"""
        ParameterValidator.validate_image_size_for_message(img, message)

        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Nascondendo messaggio con PVD...")
        original_img = img.copy()
        img_array = np.array(img, dtype=np.int32).copy()  # int32 per evitare overflow

        # Prepara il payload
        msg_binary = binary_convert(message)
        magic_header = "1010101011110000"
        msg_length = format(len(message), "032b")
        checksum = 0
        for char in message:
            checksum ^= ord(char)
        checksum_binary = format(checksum, "016b")
        terminator = "1111000011110000"  # Terminatore complesso (16 bit)

        full_payload = magic_header + msg_length + checksum_binary + msg_binary + terminator

        # Nasconde nei pixel usando coppie orizzontali
        bit_index = 0
        height, width, _ = img_array.shape

        for channel in MessageSteganography.CHANNELS:
            for row in range(height):
                for col in range(0, width - 1, 2 * MessageSteganography.PAIR_STEP):
                    if bit_index >= len(full_payload):
                        break

                    pixel1 = int(img_array[row, col, channel])
                    pixel2 = int(img_array[row, col + 1, channel])

                    # Determina quanti bit possiamo nascondere
                    _, _, capacity = MessageSteganography._get_range_capacity(pixel2 - pixel1)
                    bits_to_embed = full_payload[bit_index : bit_index + capacity]

                    if bits_to_embed:
                        new_p1, new_p2 = MessageSteganography._embed_in_pair(
                            pixel1, pixel2, bits_to_embed
                        )
                        img_array[row, col, channel] = new_p1
                        img_array[row, col + 1, channel] = new_p2
                        bit_index += len(bits_to_embed)

                if bit_index >= len(full_payload):
                    break
            if bit_index >= len(full_payload):
                break

        # Verifica che tutto il messaggio sia stato nascosto
        if bit_index < len(full_payload):
            raise ValueError(
                f"Immagine troppo piccola per nascondere il messaggio. "
                f"Nascosti {bit_index}/{len(full_payload)} bit"
            )

        # Converte in immagine
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(img_array, mode="RGB")

        # Salva parametri (sempre nella cache, opzionalmente su file)
        # Determina se RANGES è quality o capacity confrontandolo
        is_quality = MessageSteganography.RANGES == MessageSteganography.RANGES_QUALITY
        params = {
            "method": "pvd",
            "msg_length": len(message),
            "pair_step": MessageSteganography.PAIR_STEP,
            "channels": MessageSteganography.CHANNELS,
            "ranges_type": "quality" if is_quality else "capacity",
        }
        backup_system.save_backup_data(DataType.STRING, params, backup_file)

        metrics = QualityMetrics.calculate_metrics(original_img, result_img)
        print("Messaggio nascosto con successo usando PVD")
        return result_img, metrics

    @staticmethod
    def get_message(img: Image.Image, backup_file: str | None = None) -> str:
        """Recupera una stringa da un'immagine usando PVD"""
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Carica parametri
        pair_step = MessageSteganography.PAIR_STEP
        channels = MessageSteganography.CHANNELS

        if backup_file:
            backup_data = backup_system.load_backup_data(backup_file)
            if backup_data and "params" in backup_data:
                pair_step = backup_data["params"].get("pair_step", pair_step)
                channels = backup_data["params"].get("channels", channels)
                # CRITICO: carica RANGES
                ranges_type = backup_data["params"].get("ranges_type", "quality")
                MessageSteganography.RANGES = (
                    MessageSteganography.RANGES_QUALITY
                    if ranges_type == "quality"
                    else MessageSteganography.RANGES_CAPACITY
                )
                print(f"Parametri PVD caricati da backup: ranges={ranges_type}, pair_step={pair_step}, channels={channels}")
        else:
            recent = backup_system.get_last_params(DataType.STRING)
            if recent:
                pair_step = recent.get("pair_step", pair_step)
                channels = recent.get("channels", channels)
                # CRITICO: carica RANGES dalla cache
                ranges_type = recent.get("ranges_type", "quality")
                MessageSteganography.RANGES = (
                    MessageSteganography.RANGES_QUALITY
                    if ranges_type == "quality"
                    else MessageSteganography.RANGES_CAPACITY
                )
                print(f"Parametri PVD dalla cache: ranges={ranges_type}, pair_step={pair_step}, channels={channels}")

        print("Recuperando messaggio con PVD...")
        img_array = np.array(img, dtype=np.int32)

        # Estrae i bit
        extracted_bits = []
        height, width, _ = img_array.shape

        for channel in channels:
            for row in range(height):
                for col in range(0, width - 1, 2 * pair_step):
                    pixel1 = int(img_array[row, col, channel])
                    pixel2 = int(img_array[row, col + 1, channel])

                    bits = MessageSteganography._extract_from_pair(pixel1, pixel2)
                    extracted_bits.append(bits)

        full_binary = "".join(extracted_bits)
        magic_header = "1010101011110000"

        header_pos = full_binary.find(magic_header)
        if header_pos == -1:
            raise ValueError("Nessun messaggio trovato nell'immagine (header magic mancante)")

        # Legge lunghezza
        length_start = header_pos + 16
        length_end = length_start + 32
        msg_length_binary = full_binary[length_start:length_end]
        msg_length = int(msg_length_binary, 2)

        # Legge checksum
        checksum_start = length_end
        checksum_end = checksum_start + 16
        expected_checksum = int(full_binary[checksum_start:checksum_end], 2)

        # Legge messaggio
        msg_start = checksum_end
        msg_end = msg_start + (msg_length * 8)
        msg_binary = full_binary[msg_start:msg_end]

        message = binary_convert_back(msg_binary)

        # Verifica checksum
        actual_checksum = 0
        for char in message:
            actual_checksum ^= ord(char)

        if actual_checksum != expected_checksum:
            print("Warning: Checksum non corrisponde. Messaggio potrebbe essere corrotto.")

        print("Messaggio recuperato con successo usando PVD")
        return message

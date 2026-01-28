"""
Operazioni di steganografia per messaggi usando DWT (Discrete Wavelet Transform)
"""

import numpy as np
import pywt
from PIL import Image

from config.constants import DataType

from ..backup import backup_system
from ..bit_operations import binary_convert, binary_convert_back
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class MessageSteganography:
    """Classe per operazioni di steganografia su messaggi usando DWT"""

    WAVELET: str = "haar"  # Wavelet di Haar per semplicità
    ALPHA: float = 0.1  # Fattore di embedding (quanto modificare i coefficienti)
    BANDS: list[str] = ["cH"]  # Bande DWT da usare
    CHANNEL: int = 0  # Canale principale quando USE_ALL_CHANNELS=False (0=R, 1=G, 2=B)
    USE_ALL_CHANNELS: bool = (
        True  # Se True usa tutti e 3 i canali RGB, altrimenti solo CHANNEL
    )

    @staticmethod
    def hide_message(
        img: Image.Image, message: str, backup_file: str | None = None
    ) -> tuple[Image.Image, dict]:
        """
        Nasconde una stringa in un'immagine usando DWT

        Args:
            img: Immagine PIL dove nascondere il messaggio
            message: Messaggio da nascondere
            backup_file: File dove salvare i parametri di backup

        Returns:
            Tupla con (immagine_con_messaggio, metrics)
        """
        # Validazione
        ParameterValidator.validate_image_size_for_message(img, message)

        # Converte in RGB se necessario
        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Nascondendo messaggio con DWT...")
        img_array = np.array(img, dtype=np.float32)
        original_img = img.copy()

        # Prepara il messaggio binario con header robusto a 64 bit
        msg_binary = binary_convert(message)
        magic_header = (
            "1100100100001111010110010100110011010101010011110000101011001101"  # 64 bit
        )
        msg_length = format(len(message), "032b")  # 32 bit
        checksum = 0
        for char in message:
            checksum ^= ord(char)
        checksum_binary = format(checksum, "032b")  # 32 bit (era 16)
        terminator = "1111000011110000"  # 16 bit (non più usato per compatibilità)

        full_payload = (
            magic_header + msg_length + checksum_binary + msg_binary + terminator
        )

        # Verifica capacità
        max_capacity = img.width * img.height * 3 // 4  # Approssimazione
        if len(full_payload) > max_capacity:
            raise ValueError(
                f"Messaggio troppo lungo per questa immagine. "
                f"Lunghezza payload: {len(full_payload)} bit, Capacità: {max_capacity} bit"
            )

        # Determina quali canali usare
        channels_to_use = (
            [0, 1, 2]
            if MessageSteganography.USE_ALL_CHANNELS
            else [MessageSteganography.CHANNEL]
        )

        # Nasconde nei coefficienti DWT dei canali selezionati
        bit_index = 0
        for channel in channels_to_use:
            channel_data = img_array[:, :, channel]

            # Applica DWT 2D
            coeffs = pywt.dwt2(channel_data, MessageSteganography.WAVELET)
            cA, (cH, cV, cD) = coeffs  # Approssimazione e dettagli

            # Usa le bande configurate
            band_map = {"cH": cH, "cV": cV, "cD": cD}
            selected_bands = MessageSteganography.BANDS

            for band_name in selected_bands:
                if band_name not in band_map or bit_index >= len(full_payload):
                    continue

                band_coeffs = band_map[band_name]
                band_flat = band_coeffs.flatten()

                # Usa solo coefficienti significativi (abbastanza grandi)
                threshold = 1.0  # Soglia minima per i coefficienti
                usable_indices = [
                    i for i, c in enumerate(band_flat) if abs(c) > threshold
                ]

                for i in usable_indices:
                    if bit_index >= len(full_payload):
                        break

                    # Modifica il coefficiente usando ALPHA
                    bit = int(full_payload[bit_index])

                    # Delta scalato da ALPHA (moltiplicato per 50 per robustezza)
                    delta = MessageSteganography.ALPHA * 50.0

                    if bit == 1:
                        # Assicura che il coefficiente sia positivo
                        band_flat[i] = abs(band_flat[i]) + delta
                    else:
                        # Assicura che il coefficiente sia negativo
                        band_flat[i] = -abs(band_flat[i]) - delta

                    bit_index += 1

                # Aggiorna la banda modificata
                band_map[band_name] = band_flat.reshape(band_coeffs.shape)

            # Ricostruisce con le bande modificate
            cH = band_map["cH"]
            cV = band_map["cV"]
            cD = band_map["cD"]
            reconstructed = pywt.idwt2((cA, (cH, cV, cD)), MessageSteganography.WAVELET)

            # Gestisce eventuali differenze di dimensione dovute al padding
            reconstructed = reconstructed[
                : channel_data.shape[0], : channel_data.shape[1]
            ]

            img_array[:, :, channel] = reconstructed

        # Converte in immagine
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(img_array, mode="RGB")

        # Salva parametri (sempre nella cache, opzionalmente su file)
        params = {
            "method": "dwt",
            "msg_length": len(message),
            "wavelet": MessageSteganography.WAVELET,
            "alpha": MessageSteganography.ALPHA,
            "bands": MessageSteganography.BANDS,
            "channel": MessageSteganography.CHANNEL,
            "use_all_channels": MessageSteganography.USE_ALL_CHANNELS,
        }
        backup_system.save_backup_data(DataType.STRING, params, backup_file)

        # Calcola metriche
        metrics = QualityMetrics.calculate_metrics(original_img, result_img)

        print("Messaggio nascosto con successo usando DWT")
        return result_img, metrics

    @staticmethod
    def get_message(img: Image.Image, backup_file: str | None = None) -> str:
        """
        Recupera una stringa da un'immagine usando DWT

        Args:
            img: Immagine PIL contenente il messaggio
            backup_file: File di backup con i parametri

        Returns:
            Messaggio recuperato
        """
        # Carica parametri da backup se disponibile
        if backup_file:
            backup_data = backup_system.load_backup_data(backup_file)
            if backup_data and "params" in backup_data:
                MessageSteganography.WAVELET = backup_data["params"].get(
                    "wavelet", MessageSteganography.WAVELET
                )
                MessageSteganography.ALPHA = backup_data["params"].get(
                    "alpha", MessageSteganography.ALPHA
                )
                MessageSteganography.BANDS = backup_data["params"].get(
                    "bands", MessageSteganography.BANDS
                )
                MessageSteganography.CHANNEL = backup_data["params"].get(
                    "channel", MessageSteganography.CHANNEL
                )
                MessageSteganography.USE_ALL_CHANNELS = backup_data["params"].get(
                    "use_all_channels", MessageSteganography.USE_ALL_CHANNELS
                )
                print(
                    f"Parametri DWT caricati da backup: WAVELET={MessageSteganography.WAVELET}, ALPHA={MessageSteganography.ALPHA}, "
                    f"BANDS={MessageSteganography.BANDS}, CHANNEL={MessageSteganography.CHANNEL}, USE_ALL_CHANNELS={MessageSteganography.USE_ALL_CHANNELS}"
                )
        else:
            # Usa parametri dalla cache dell'ultima operazione
            recent = backup_system.get_last_params(DataType.STRING)
            if recent:
                MessageSteganography.WAVELET = recent.get(
                    "wavelet", MessageSteganography.WAVELET
                )
                MessageSteganography.ALPHA = recent.get(
                    "alpha", MessageSteganography.ALPHA
                )
                MessageSteganography.BANDS = recent.get(
                    "bands", MessageSteganography.BANDS
                )
                MessageSteganography.CHANNEL = recent.get(
                    "channel", MessageSteganography.CHANNEL
                )
                MessageSteganography.USE_ALL_CHANNELS = recent.get(
                    "use_all_channels", MessageSteganography.USE_ALL_CHANNELS
                )
                print(
                    f"Parametri DWT dalla cache: WAVELET={MessageSteganography.WAVELET}, ALPHA={MessageSteganography.ALPHA}, "
                    f"BANDS={MessageSteganography.BANDS}, CHANNEL={MessageSteganography.CHANNEL}, USE_ALL_CHANNELS={MessageSteganography.USE_ALL_CHANNELS}"
                )

        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Recuperando messaggio con DWT...")
        img_array = np.array(img, dtype=np.float32)

        # Determina quali canali usare (stessi dell'hide)
        channels_to_use = (
            [0, 1, 2]
            if MessageSteganography.USE_ALL_CHANNELS
            else [MessageSteganography.CHANNEL]
        )

        # === ESTRAZIONE SINCRONIZZATA IN DUE FASI ===
        # FASE 1: Estrai header (64) + msg_length (32) + checksum (32) = 128 bit
        # FASE 2: Calcola bit necessari e continua estrazione

        HEADER_BITS = 64
        LENGTH_BITS = 32
        CHECKSUM_BITS = 32
        TERMINATOR_BITS = 16
        magic_header = (
            "1100100100001111010110010100110011010101010011110000101011001101"
        )

        # FASE 1: Estrai primi 128 bit (header + length + checksum)
        bits_needed = HEADER_BITS + LENGTH_BITS + CHECKSUM_BITS
        extracted_bits = []
        threshold = 1.0  # Soglia minima per coefficienti utilizzabili

        for channel in channels_to_use:
            if len(extracted_bits) >= bits_needed:
                break

            channel_data = img_array[:, :, channel]

            # Applica DWT 2D
            coeffs = pywt.dwt2(channel_data, MessageSteganography.WAVELET)
            cA, (cH, cV, cD) = coeffs

            # Usa le stesse bande configurate nell'hide
            band_map = {"cH": cH, "cV": cV, "cD": cD}
            selected_bands = MessageSteganography.BANDS

            for band_name in selected_bands:
                if band_name not in band_map:
                    continue
                if len(extracted_bits) >= bits_needed:
                    break

                band_coeffs = band_map[band_name]
                band_flat = band_coeffs.flatten()

                # Usa solo coefficienti significativi (stessa soglia dell'hide)
                usable_indices = [
                    i for i, c in enumerate(band_flat) if abs(c) > threshold
                ]

                for i in usable_indices:
                    if len(extracted_bits) >= bits_needed:
                        break
                    # Estrae il bit dal segno del coefficiente
                    if band_flat[i] > 0:
                        extracted_bits.append("1")
                    else:
                        extracted_bits.append("0")

        bitstream = "".join(extracted_bits)

        # Verifica header DEVE essere all'inizio (no find!)
        if len(bitstream) < HEADER_BITS + LENGTH_BITS + CHECKSUM_BITS:
            raise ValueError(
                "Immagine troppo piccola o corrotta: impossibile leggere header messaggio DWT"
            )

        if bitstream[:HEADER_BITS] != magic_header:
            raise ValueError(
                "Header non valido: nessun messaggio DWT trovato. "
                "Possibili cause: (1) Metodo sbagliato (usa LSB/PVD invece di DWT), "
                "(2) Immagine corrotta, (3) Parametri errati (WAVELET/BANDS/CHANNELS/USE_ALL_CHANNELS diversi dall'hide)"
            )

        # Decodifica msg_length e checksum
        msg_length_binary = bitstream[HEADER_BITS : HEADER_BITS + LENGTH_BITS]
        msg_length = int(msg_length_binary, 2)

        checksum_start = HEADER_BITS + LENGTH_BITS
        expected_checksum = int(
            bitstream[checksum_start : checksum_start + CHECKSUM_BITS], 2
        )

        # FASE 2: Calcola bit totali e continua estrazione
        total_bits_needed = (
            HEADER_BITS
            + LENGTH_BITS
            + CHECKSUM_BITS
            + (msg_length * 8)
            + TERMINATOR_BITS
        )

        # Continua estrazione solo se servono più bit
        if len(extracted_bits) < total_bits_needed:
            bits_read = len(extracted_bits)
            current_bit_index = 0

            for channel in channels_to_use:
                if len(extracted_bits) >= total_bits_needed:
                    break

                channel_data = img_array[:, :, channel]
                coeffs = pywt.dwt2(channel_data, MessageSteganography.WAVELET)
                cA, (cH, cV, cD) = coeffs
                band_map = {"cH": cH, "cV": cV, "cD": cD}
                selected_bands = MessageSteganography.BANDS

                for band_name in selected_bands:
                    if band_name not in band_map:
                        continue
                    if len(extracted_bits) >= total_bits_needed:
                        break

                    band_coeffs = band_map[band_name]
                    band_flat = band_coeffs.flatten()
                    usable_indices = [
                        i for i, c in enumerate(band_flat) if abs(c) > threshold
                    ]

                    for i in usable_indices:
                        # Salta bit già estratti nella FASE 1
                        if current_bit_index < bits_read:
                            current_bit_index += 1
                            continue

                        if len(extracted_bits) >= total_bits_needed:
                            break
                        if band_flat[i] > 0:
                            extracted_bits.append("1")
                        else:
                            extracted_bits.append("0")
                        current_bit_index += 1

        bitstream = "".join(extracted_bits)

        # Legge il messaggio
        msg_start = HEADER_BITS + LENGTH_BITS + CHECKSUM_BITS
        msg_end = msg_start + (msg_length * 8)
        msg_binary = bitstream[msg_start:msg_end]

        # Decodifica
        message = binary_convert_back(msg_binary)

        # Verifica checksum
        actual_checksum = 0
        for char in message:
            actual_checksum ^= ord(char)

        if actual_checksum != expected_checksum:
            print(
                "Warning: Checksum non corrisponde. Messaggio potrebbe essere corrotto."
            )

        print("Messaggio recuperato con successo usando DWT")
        return message

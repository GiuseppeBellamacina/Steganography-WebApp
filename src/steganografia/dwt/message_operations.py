"""
Operazioni di steganografia per messaggi usando DWT (Discrete Wavelet Transform)
"""

import numpy as np
import pywt
from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..bit_operations import binary_convert, binary_convert_back
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class MessageSteganography:
    """Classe per operazioni di steganografia su messaggi usando DWT"""

    WAVELET: str = "haar"  # Wavelet di Haar per semplicità
    LEVEL: int = 1  # Livello di decomposizione
    ALPHA: float = 0.1  # Fattore di embedding (quanto modificare i coefficienti)

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

        # Prepara il messaggio binario con header
        msg_binary = binary_convert(message)
        magic_header = "1010101011110000"
        msg_length = format(len(message), "032b")
        checksum = 0
        for char in message:
            checksum ^= ord(char)
        checksum_binary = format(checksum, "016b")
        terminator = "1111000011110000"  # Terminatore complesso (16 bit)

        full_payload = magic_header + msg_length + checksum_binary + msg_binary + terminator

        # Verifica capacità
        max_capacity = img.width * img.height * 3 // 4  # Approssimazione
        if len(full_payload) > max_capacity:
            raise ValueError(
                f"Messaggio troppo lungo per questa immagine. "
                f"Lunghezza payload: {len(full_payload)} bit, Capacità: {max_capacity} bit"
            )

        # Nasconde nei coefficienti DWT di ogni canale
        bit_index = 0
        for channel in range(3):  # R, G, B
            channel_data = img_array[:, :, channel]

            # Applica DWT 2D
            coeffs = pywt.dwt2(channel_data, MessageSteganography.WAVELET)
            cA, (cH, cV, cD) = coeffs  # Approssimazione e dettagli

            # Nasconde nei coefficienti di dettaglio (cH - orizzontale)
            cH_flat = cH.flatten()

            # Usa solo coefficienti significativi (abbastanza grandi)
            threshold = 1.0  # Soglia minima per i coefficienti
            usable_indices = [i for i, c in enumerate(cH_flat) if abs(c) > threshold]

            if len(usable_indices) < len(full_payload):
                # Se non ci sono abbastanza coefficienti in questo canale, continua
                pass

            coeff_idx = 0
            for i in usable_indices:
                if bit_index >= len(full_payload):
                    break

                # Modifica il coefficiente usando ALPHA
                bit = int(full_payload[bit_index])

                # Delta scalato da ALPHA (moltiplicato per 50 per robustezza)
                delta = MessageSteganography.ALPHA * 50.0

                if bit == 1:
                    # Assicura che il coefficiente sia positivo
                    cH_flat[i] = abs(cH_flat[i]) + delta
                else:
                    # Assicura che il coefficiente sia negativo
                    cH_flat[i] = -abs(cH_flat[i]) - delta

                bit_index += 1

            # Ricostruisce la sub-banda
            cH = cH_flat.reshape(cH.shape)

            # Ricostruisce l'immagine con IDWT
            reconstructed = pywt.idwt2((cA, (cH, cV, cD)), MessageSteganography.WAVELET)

            # Gestisce eventuali differenze di dimensione dovute al padding
            reconstructed = reconstructed[: channel_data.shape[0], : channel_data.shape[1]]

            img_array[:, :, channel] = reconstructed

        # Converte in immagine
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(img_array, mode="RGB")

        # Salva parametri (sempre nella cache, opzionalmente su file)
        params = {
            "method": "dwt",
            "msg_length": len(message),
            "wavelet": MessageSteganography.WAVELET,
            "level": MessageSteganography.LEVEL,
            "alpha": MessageSteganography.ALPHA,
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
                MessageSteganography.WAVELET = backup_data["params"].get("wavelet", MessageSteganography.WAVELET)
                MessageSteganography.ALPHA = backup_data["params"].get("alpha", MessageSteganography.ALPHA)
                print(f"Parametri DWT caricati da backup: WAVELET={MessageSteganography.WAVELET}, ALPHA={MessageSteganography.ALPHA}")
        else:
            # Usa parametri dalla cache dell'ultima operazione
            recent = backup_system.get_last_params(DataType.STRING)
            if recent:
                MessageSteganography.WAVELET = recent.get("wavelet", MessageSteganography.WAVELET)
                MessageSteganography.ALPHA = recent.get("alpha", MessageSteganography.ALPHA)
                print(f"Parametri DWT dalla cache: WAVELET={MessageSteganography.WAVELET}, ALPHA={MessageSteganography.ALPHA}")

        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Recuperando messaggio con DWT...")
        img_array = np.array(img, dtype=np.float32)

        # Estrae i bit dai coefficienti DWT
        extracted_bits = []

        for channel in range(3):  # R, G, B
            channel_data = img_array[:, :, channel]

            # Applica DWT 2D
            coeffs = pywt.dwt2(channel_data, MessageSteganography.WAVELET)
            cA, (cH, cV, cD) = coeffs

            # Legge dai coefficienti di dettaglio
            cH_flat = cH.flatten()

            # Usa solo coefficienti significativi (stessa soglia)
            threshold = 1.0
            usable_indices = [i for i, c in enumerate(cH_flat) if abs(c) > threshold]

            for i in usable_indices:
                # Estrae il bit dal segno del coefficiente
                if cH_flat[i] > 0:
                    extracted_bits.append("1")
                else:
                    extracted_bits.append("0")

        # Cerca il magic header
        full_binary = "".join(extracted_bits)
        magic_header = "1010101011110000"

        # Debug: mostra i primi bit estratti
        print(f"Primi 100 bit estratti: {full_binary[:100]}")
        print(f"Totale bit estratti: {len(full_binary)}")

        header_pos = full_binary.find(magic_header)
        if header_pos == -1:
            # Prova a cercare in una finestra più ampia
            search_limit = min(5000, len(full_binary) - 64)
            for pos in range(search_limit):
                if pos + 16 <= len(full_binary):
                    candidate = full_binary[pos : pos + 16]
                    if candidate == magic_header:
                        header_pos = pos
                        print(f"Header trovato alla posizione: {pos}")
                        break

            if header_pos == -1:
                raise ValueError(ErrorMessages.NO_MESSAGE_FOUND)

        # Legge la lunghezza del messaggio
        length_start = header_pos + 16
        length_end = length_start + 32
        msg_length_binary = full_binary[length_start:length_end]
        msg_length = int(msg_length_binary, 2)

        # Legge il checksum
        checksum_start = length_end
        checksum_end = checksum_start + 16
        expected_checksum = int(full_binary[checksum_start:checksum_end], 2)

        # Legge il messaggio
        msg_start = checksum_end
        msg_end = msg_start + (msg_length * 8)
        msg_binary = full_binary[msg_start:msg_end]

        # Decodifica
        message = binary_convert_back(msg_binary)

        # Verifica checksum
        actual_checksum = 0
        for char in message:
            actual_checksum ^= ord(char)

        if actual_checksum != expected_checksum:
            print("Warning: Checksum non corrisponde. Messaggio potrebbe essere corrotto.")

        print("Messaggio recuperato con successo usando DWT")
        return message

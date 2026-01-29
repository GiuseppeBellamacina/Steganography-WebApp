"""
Operazioni di steganografia LSB per i messaggi (stringhe)
"""

from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..bit_operations import (
    binary_convert,
    binary_convert_back,
    set_color_component,
    set_last_bit,
)
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class MessageSteganography:
    """Classe per operazioni di steganografia LSB su stringhe"""

    @staticmethod
    def hide_message(
        img: Image.Image, message: str, backup_file: str | None = None
    ) -> tuple[Image.Image, dict, float]:
        """
        Nasconde una stringa in un'immagine

        Args:
            img: Immagine PIL dove nascondere il messaggio
            message: Messaggio da nascondere
            backup_file: File dove salvare i parametri di backup

        Returns:
            Tupla con (immagine_con_messaggio, metrics, percentuale) dove metrics è un dizionario con 'ssim' e 'psnr' e percentuale è la percentuale di pixel usati
        """
        # Validazione
        ParameterValidator.validate_image_size_for_message(img, message)

        # Converte in RGB se necessario
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Inizia a nascondere
        print("Nascondendo messaggio...")
        img_copy = img.copy()
        mat = img_copy.load()
        if mat is None:
            raise ValueError("Impossibile caricare i dati dell'immagine")

        # Crea il payload con header robusto
        msg_binary = binary_convert(message)

        # Header magico (16 bit): 1010101011110000
        magic_header = "1010101011110000"

        # Lunghezza del messaggio (32 bit): per sapere esattamente quanti caratteri leggere
        msg_length = format(len(message), "032b")

        # Calcola checksum semplice (16 bit): XOR di tutti i byte del messaggio
        checksum = 0
        for char in message:
            checksum ^= ord(char)
        checksum_binary = format(checksum, "016b")

        # Terminatore (16 bit) - pattern complesso per evitare falsi positivi
        terminator = "1111000011110000"

        # Costruisce il payload completo: HEADER + LENGTH + CHECKSUM + MESSAGE + TERMINATOR
        full_payload = (
            magic_header + msg_length + checksum_binary + msg_binary + terminator
        )
        msg_list = list(full_payload)

        for i in range(img.width):
            for j in range(img.height):
                for z in range(3):
                    if msg_list:
                        bit = msg_list.pop(0)
                        pixel = mat[i, j]
                        color = int(pixel[z])  # type: ignore[index]
                        color = set_last_bit(color, bit)
                        mat = set_color_component(mat, i, j, color, z)
                    else:
                        break

        original_len = len(full_payload)
        percentage = format(
            ((original_len / ((img.width * img.height) * 3)) * 100), ".2f"
        )
        print(
            f"TERMINATO - Percentuale di pixel usati: {percentage}% (Header: {len(magic_header + msg_length + checksum_binary + terminator)} bit, Messaggio: {len(msg_binary)} bit)"
        )

        # Salva i parametri per il recupero
        params = {"original_message": message, "method": "string"}
        backup_system.save_backup_data(DataType.STRING, params, backup_file)

        # Calcola metriche di qualità (SSIM e PSNR)
        metrics = QualityMetrics.calculate_metrics(img, img_copy)
        print(
            f"Metriche di qualità - SSIM: {metrics['ssim']:.4f}, PSNR: {metrics['psnr']:.2f} dB"
        )

        return img_copy, metrics, float(percentage)

    @staticmethod
    def get_message(img: Image.Image, backup_file: str | None = None) -> str:
        """
        Recupera un messaggio nascosto da un'immagine

        Args:
            img: Immagine PIL che contiene il messaggio
            backup_file: File di backup dei parametri

        Returns:
            Messaggio recuperato
        """
        # Controlla se esistono parametri di backup
        backup_data = None
        if backup_file:
            backup_data = backup_system.load_backup_data(backup_file)

        # Se non ci sono backup file, controlla le variabili locali
        if not backup_data:
            recent_params = backup_system.get_last_params(DataType.STRING)
            if recent_params:
                print("Usando parametri dall'ultima operazione di occultamento")
                backup_data = {"type": DataType.STRING, "params": recent_params}

        if img.mode != "RGB":
            img = img.convert("RGB")

        # Inizia la procedura di recupero
        mat = img.load()
        if mat is None:
            raise ValueError("Impossibile caricare i dati dell'immagine")

        # Estrae tutti i bit dall'immagine
        all_bits = []
        for i in range(img.width):
            for j in range(img.height):
                for z in range(3):
                    pixel = mat[i, j]
                    color = int(pixel[z])  # type: ignore[index]
                    bit = format(color, "08b")[-1]
                    all_bits.append(bit)

        # Cerca l'header magico
        magic_header = "1010101011110000"
        header_found = False
        start_pos = 0

        # Cerca l'header nei primi bit dell'immagine (entro i primi 1000 bit per performance)
        search_limit = min(
            1000, len(all_bits) - 72
        )  # 72 = header(16) + length(32) + checksum(16) + min_terminator(8)

        for pos in range(search_limit):
            if pos + 16 <= len(all_bits):
                candidate_header = "".join(all_bits[pos : pos + 16])
                if candidate_header == magic_header:
                    header_found = True
                    start_pos = pos
                    break

        if not header_found:
            raise ValueError(ErrorMessages.NO_MESSAGE_FOUND)

        print(f"Header magico trovato alla posizione {start_pos}")

        # Estrae la lunghezza del messaggio (32 bit dopo l'header)
        length_start = start_pos + 16
        if length_start + 32 > len(all_bits):
            raise ValueError(ErrorMessages.DECODE_FAILED)

        length_bits = "".join(all_bits[length_start : length_start + 32])
        try:
            message_length = int(length_bits, 2)
        except ValueError:
            raise ValueError(ErrorMessages.DECODE_FAILED)

        # Controllo di sanità sulla lunghezza
        if message_length <= 0 or message_length > 10000:  # Limite ragionevole
            raise ValueError(ErrorMessages.NO_MESSAGE_FOUND)

        print(f"Lunghezza messaggio attesa: {message_length} caratteri")

        # Estrae il checksum (16 bit dopo la lunghezza)
        checksum_start = length_start + 32
        if checksum_start + 16 > len(all_bits):
            raise ValueError(ErrorMessages.DECODE_FAILED)

        checksum_bits = "".join(all_bits[checksum_start : checksum_start + 16])
        expected_checksum = int(checksum_bits, 2)

        # Estrae il messaggio (message_length * 8 bit dopo il checksum)
        message_start = checksum_start + 16
        message_bits_length = message_length * 8

        if message_start + message_bits_length > len(all_bits):
            raise ValueError(ErrorMessages.DECODE_FAILED)

        message_bits = "".join(
            all_bits[message_start : message_start + message_bits_length]
        )

        # Verifica il terminatore (16 bit dopo il messaggio)
        terminator_start = message_start + message_bits_length
        if terminator_start + 16 > len(all_bits):
            raise ValueError(ErrorMessages.DECODE_FAILED)

        terminator_bits = "".join(all_bits[terminator_start : terminator_start + 16])
        if terminator_bits != "1111000011110000":
            raise ValueError(ErrorMessages.NO_MESSAGE_FOUND)

        # Decodifica il messaggio
        try:
            message = binary_convert_back(message_bits)
        except Exception as e:
            raise ValueError(ErrorMessages.DECODE_FAILED) from e

        # Verifica il checksum
        calculated_checksum = 0
        for char in message:
            calculated_checksum ^= ord(char)

        if calculated_checksum != expected_checksum:
            raise ValueError("Messaggio corrotto: checksum non valido")

        # Verifica con il backup se disponibile
        if backup_data and "params" in backup_data:
            original = backup_data["params"].get("original_message", "")
            if original == message:
                print("Messaggio verificato con backup")

        print(f"Messaggio recuperato e verificato: {len(message)} caratteri")
        return message

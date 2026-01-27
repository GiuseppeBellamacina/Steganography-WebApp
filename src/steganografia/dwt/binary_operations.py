"""
Operazioni di steganografia per file binari usando DWT (Discrete Wavelet Transform)
"""

import numpy as np
import pywt
from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..metrics import QualityMetrics


class BinarySteganography:
    """Classe per operazioni di steganografia su file binari usando DWT"""

    WAVELET: str = "haar"  # Wavelet di Haar per semplicità
    LEVEL: int = 1  # Livello di decomposizione
    SEED: int = 42  # Seed per determinismo
    STEP: float = 12.0  # Step di quantizzazione (compatibilità con image)
    CHANNEL: int = 0  # Canale principale (compatibilità)
    BITS_SECRET: int = 3  # Compatibilità con image (non usato in binary)
    BANDS: list[str] = ["cH"]  # Banda DWT da usare per binary
    ALPHA: float = 0.1  # Fattore di embedding (quanto modificare i coefficienti)
    USE_ALL_CHANNELS: bool = False  # Se True usa tutti e 3 i canali RGB (3x capacità)

    @staticmethod
    def hide_binary_file(
        img: Image.Image,
        file_path: str,
        backup_file: str | None = None,
        **kwargs,  # Ignora compression_mode, n, div per compatibilità API
    ) -> tuple[Image.Image, int, float, int, dict]:
        """
        Nasconde un file binario in un'immagine usando DWT

        Args:
            img: Immagine host
            file_path: Percorso del file da nascondere
            backup_file: File di backup opzionale
        """
        # Legge il file
        with open(file_path, "rb") as f:
            file_data = f.read()

        file_size = len(file_data)

        # Converte in binario
        file_binary = "".join(format(byte, "08b") for byte in file_data)

        # Prepara payload con header
        magic_header = "1010101011110000"
        size_binary = format(file_size, "032b")
        terminator = "1111000011110000"  # Terminatore complesso (16 bit)
        full_payload = magic_header + size_binary + file_binary + terminator

        # Verifica capacità
        max_capacity = img.width * img.height * 3 // 4
        if len(full_payload) > max_capacity:
            raise ValueError(
                ErrorMessages.IMAGE_TOO_SMALL_FILE.format(
                    file_size=file_size, width=img.width, height=img.height
                )
            )

        if img.mode != "RGB":
            img = img.convert("RGB")

        print(f"Nascondendo file binario ({file_size} bytes) con DWT...")
        print(
            f"DWT Hide Binary - Parametri: WAVELET={BinarySteganography.WAVELET}, LEVEL={BinarySteganography.LEVEL}, ALPHA={BinarySteganography.ALPHA}, BANDS={BinarySteganography.BANDS}, USE_ALL_CHANNELS={BinarySteganography.USE_ALL_CHANNELS}"
        )
        original_img = img.copy()
        img_array = np.array(img, dtype=np.float32)

        # Determina quali canali usare
        channels_to_use = (
            [0, 1, 2] if BinarySteganography.USE_ALL_CHANNELS else [BinarySteganography.CHANNEL]
        )
        selected_bands = BinarySteganography.BANDS

        bit_index = 0
        for channel_idx in channels_to_use:
            if bit_index >= len(full_payload):
                break

            channel_data = img_array[:, :, channel_idx]
            coeffs = pywt.dwt2(channel_data, BinarySteganography.WAVELET)
            cA, (cH, cV, cD) = coeffs

            # Usa le bande configurate
            band_map = {"cH": cH, "cV": cV, "cD": cD}

            for band_name in selected_bands:
                if band_name not in band_map or bit_index >= len(full_payload):
                    continue

                coeff_flat = band_map[band_name].flatten()
                for i in range(len(coeff_flat)):
                    if bit_index >= len(full_payload):
                        break
                    bit = int(full_payload[bit_index])
                    # EMBEDDING BASATO SU SEGNO CON ALTA ROBUSTEZZA:
                    # Forza coefficienti a valori grandi e distinti per sopravvivere a clip/uint8
                    # bit=1 → coefficiente GRANDE e POSITIVO
                    # bit=0 → coefficiente GRANDE e NEGATIVO
                    abs_val = abs(coeff_flat[i])
                    if abs_val < 1.0:  # Coefficiente troppo piccolo
                        abs_val = 2.0

                    # Usa moltiplicatori fissi robusti basati su ALPHA
                    strength = max(5.0, 1.0 / BinarySteganography.ALPHA)  # Min 5x per robustezza

                    if bit == 1:
                        # bit=1: grande valore POSITIVO
                        coeff_flat[i] = abs_val * strength
                    else:
                        # bit=0: grande valore NEGATIVO
                        coeff_flat[i] = -abs_val * strength
                    bit_index += 1

                # Aggiorna la banda modificata
                band_map[band_name] = coeff_flat.reshape(band_map[band_name].shape)

            # Ricostruisce con le bande modificate
            cH = band_map["cH"]
            cV = band_map["cV"]
            cD = band_map["cD"]
            reconstructed = pywt.idwt2((cA, (cH, cV, cD)), BinarySteganography.WAVELET)
            reconstructed = reconstructed[: channel_data.shape[0], : channel_data.shape[1]]
            img_array[:, :, channel_idx] = reconstructed

        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(img_array, mode="RGB")

        # Salva parametri (sempre nella cache, opzionalmente su file)
        params = {
            "method": "dwt",
            "size": file_size,
            "wavelet": BinarySteganography.WAVELET,
            "level": BinarySteganography.LEVEL,
            "seed": BinarySteganography.SEED,
            "step": BinarySteganography.STEP,
            "channel": BinarySteganography.CHANNEL,
            "bits_secret": BinarySteganography.BITS_SECRET,
            "bands": BinarySteganography.BANDS,
            "alpha": BinarySteganography.ALPHA,
            "use_all_channels": BinarySteganography.USE_ALL_CHANNELS,
        }
        backup_system.save_backup_data(DataType.BINARY, params, backup_file)

        metrics = QualityMetrics.calculate_metrics(original_img, result_img)
        print("File nascosto con successo usando DWT")

        return result_img, 1, 0.0, file_size, metrics

    @staticmethod
    def get_binary_file(
        img: Image.Image,
        output_path: str,
        size: int | None = None,
        backup_file: str | None = None,
        **kwargs,  # Ignora compression_mode, n, div per compatibilità API
    ) -> None:
        """
        Recupera un file binario da un'immagine usando DWT

        Args:
            img: Immagine contenente il file nascosto
            output_path: Percorso di output
            size: Dimensione del file nascosto in byte
            backup_file: File di backup opzionale
        """
        # Carica parametri da backup o cache (compatibile con image_operations.py)
        backup_data = None
        if backup_file:
            backup_data = backup_system.load_backup_data(backup_file)

        # Se non c'è backup file, usa cache dell'ultima operazione
        if not backup_data:
            recent_params = backup_system.get_last_params(DataType.BINARY)
            if recent_params:
                print("Usando parametri dall'ultima operazione di nascondimento")
                backup_data = {"params": recent_params}

        if backup_data and "params" in backup_data:
            params = backup_data["params"]
            size = params.get("size")
            # Carica TUTTI i parametri DWT per compatibilità
            wavelet = params.get("wavelet", BinarySteganography.WAVELET)
            level = params.get("level", BinarySteganography.LEVEL)
            seed = params.get("seed", BinarySteganography.SEED)
            step = params.get("step", BinarySteganography.STEP)
            channel_idx = params.get("channel", BinarySteganography.CHANNEL)
            bits_secret = params.get("bits_secret", BinarySteganography.BITS_SECRET)
            bands = params.get("bands", BinarySteganography.BANDS)
            alpha = params.get("alpha", BinarySteganography.ALPHA)
            use_all_channels = params.get("use_all_channels", BinarySteganography.USE_ALL_CHANNELS)

            print(
                f"DWT Get Binary - Parametri: WAVELET={wavelet}, LEVEL={level}, SEED={seed}, ALPHA={alpha}, BANDS={bands}, USE_ALL_CHANNELS={use_all_channels}"
            )
        else:
            # Usa valori di default se non c'è backup
            size = None
            wavelet = BinarySteganography.WAVELET
            level = BinarySteganography.LEVEL
            seed = BinarySteganography.SEED
            step = BinarySteganography.STEP
            channel_idx = BinarySteganography.CHANNEL
            bits_secret = BinarySteganography.BITS_SECRET
            bands = BinarySteganography.BANDS
            alpha = BinarySteganography.ALPHA
            use_all_channels = BinarySteganography.USE_ALL_CHANNELS

        if size is None:
            raise ValueError(ErrorMessages.PARAMS_MISSING)

        if img.mode != "RGB":
            img = img.convert("RGB")

        print(f"Recuperando file binario ({size} bytes) con DWT...")
        img_array = np.array(img, dtype=np.float32)

        # Determina quali canali usare (deve corrispondere a hide)
        channels_to_use = [0, 1, 2] if use_all_channels else [channel_idx]
        extracted_bits = []

        # ESTRAZIONE BASATA SU SEGNO (semplice e robusto)
        for ch_idx in channels_to_use:
            channel_data = img_array[:, :, ch_idx]
            coeffs = pywt.dwt2(channel_data, wavelet)
            cA, (cH, cV, cD) = coeffs

            # Estrae bit dalle bande configurate
            band_map = {"cH": cH, "cV": cV, "cD": cD}

            for band_name in bands:
                if band_name not in band_map:
                    continue

                coeff_flat = band_map[band_name].flatten()
                for coeff in coeff_flat:
                    # bit=1 se POSITIVO, bit=0 se NEGATIVO
                    extracted_bits.append("1" if coeff > 0 else "0")

        full_binary = "".join(extracted_bits)
        magic_header = "1010101011110000"

        header_pos = full_binary.find(magic_header)
        if header_pos == -1:
            raise ValueError(
                "Nessun file trovato nell'immagine. "
                "Possibili cause: (1) Metodo sbagliato - verifica di usare DWT sia per hide che per get, "
                "(2) Immagine corrotta, (3) Nessun file nascosto presente."
            )

        size_start = header_pos + 16
        size_end = size_start + 32
        file_size_binary = full_binary[size_start:size_end]
        file_size = int(file_size_binary, 2)

        file_start = size_end
        file_end = file_start + (file_size * 8)
        file_binary = full_binary[file_start:file_end]

        # Ricostruisce il file
        file_bytes = bytearray()
        for i in range(0, len(file_binary), 8):
            byte = file_binary[i : i + 8]
            if len(byte) == 8:
                file_bytes.append(int(byte, 2))

        with open(output_path, "wb") as f:
            f.write(file_bytes)

        print(f"File recuperato e salvato in {output_path}")

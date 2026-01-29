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
    CHANNEL: int = 0  # Canale principale (0=R, 1=G, 2=B)
    BANDS: list[str] = ["cH"]  # Banda DWT da usare per binary
    ALPHA: float = (
        0.1  # Fattore di embedding - PARAMETRO PRINCIPALE (controlla strength = 1.0 / ALPHA)
    )
    USE_ALL_CHANNELS: bool = False  # Se True usa tutti e 3 i canali RGB (3x capacità)

    @staticmethod
    def hide_binary_file(
        img: Image.Image,
        file_path: str,
        backup_file: str | None = None,
        **kwargs,  # Ignora compression_mode, n, div per compatibilità API
    ) -> tuple[Image.Image, int, float, int, dict, float]:
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

        # Prepara payload con header robusto a 64 bit (riduce falsi positivi)
        magic_header = (
            "1100100100001111010110010100110011010101010011110000101011001101"  # 64 bit
        )
        size_binary = format(file_size, "032b")  # 32 bit
        terminator = "1111000011110000"  # 16 bit
        full_payload = magic_header + size_binary + file_binary + terminator

        # Verifica capacità (header 64 + size 32 + file + terminator 16)
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
            f"DWT Hide Binary - Parametri: WAVELET={BinarySteganography.WAVELET}, ALPHA={BinarySteganography.ALPHA}, BANDS={BinarySteganography.BANDS}, USE_ALL_CHANNELS={BinarySteganography.USE_ALL_CHANNELS}"
        )
        original_img = img.copy()
        img_array = np.array(img, dtype=np.float32)

        # Determina quali canali usare
        channels_to_use = (
            [0, 1, 2]
            if BinarySteganography.USE_ALL_CHANNELS
            else [BinarySteganography.CHANNEL]
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
                    strength = max(
                        5.0, 1.0 / BinarySteganography.ALPHA
                    )  # Min 5x per robustezza

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
            reconstructed = reconstructed[
                : channel_data.shape[0], : channel_data.shape[1]
            ]
            img_array[:, :, channel_idx] = reconstructed

        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(img_array, mode="RGB")

        # Calcola percentuale di bit usati
        total_bits_host = img.width * img.height * 3
        percentage = format((len(full_payload) / total_bits_host) * 100, ".2f")
        print(
            f"TERMINATO - Percentuale di pixel usati con DWT: {percentage}% ({len(full_payload)}/{total_bits_host} bit)"
        )

        # Salva parametri (sempre nella cache, opzionalmente su file)
        params = {
            "method": "dwt",
            "size": file_size,
            "wavelet": BinarySteganography.WAVELET,
            "channel": BinarySteganography.CHANNEL,
            "bands": BinarySteganography.BANDS,
            "alpha": BinarySteganography.ALPHA,
            "use_all_channels": BinarySteganography.USE_ALL_CHANNELS,
        }
        backup_system.save_backup_data(DataType.BINARY, params, backup_file)

        metrics = QualityMetrics.calculate_metrics(original_img, result_img)
        print("File nascosto con successo usando DWT")

        return result_img, 1, 0.0, file_size, metrics, float(percentage)

    @staticmethod
    def get_binary_file(
        img: Image.Image,
        output_path: str,
        backup_file: str | None = None,
        # Parametri manuali opzionali (usati se manual_params=True)
        alpha: float | None = None,
        bands: list[str] | None = None,
        use_all_channels: bool | None = None,
        **kwargs,  # Ignora n, div per compatibilità API
    ) -> None:
        """
        Recupera un file binario da un'immagine usando DWT

        Args:
            img: Immagine contenente il file nascosto
            output_path: Percorso di output
            backup_file: File di backup opzionale
            alpha: Fattore di embedding manuale (opzionale)
            bands: Bande DWT manuali (opzionale)
            use_all_channels: Usa tutti i canali RGB (opzionale)
        """
        # PRIORITÀ: parametri manuali > backup file > cache recente > default
        # Se sono forniti parametri manuali, usali
        if alpha is not None or bands is not None or use_all_channels is not None:
            print("Usando parametri MANUALI forniti dall'interfaccia")
            # Usa parametri manuali se forniti, altrimenti default
            alpha = alpha if alpha is not None else BinarySteganography.ALPHA
            bands = bands if bands is not None else BinarySteganography.BANDS
            use_all_channels = (
                use_all_channels
                if use_all_channels is not None
                else BinarySteganography.USE_ALL_CHANNELS
            )
            # Altri parametri sempre da default
            wavelet = BinarySteganography.WAVELET
            channel_idx = BinarySteganography.CHANNEL
        else:
            # Carica parametri da backup o cache
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
                # Carica TUTTI i parametri DWT
                wavelet = params.get("wavelet", BinarySteganography.WAVELET)
                channel_idx = params.get("channel", BinarySteganography.CHANNEL)
                bands = params.get("bands", BinarySteganography.BANDS)
                alpha = params.get("alpha", BinarySteganography.ALPHA)
                use_all_channels = params.get(
                    "use_all_channels", BinarySteganography.USE_ALL_CHANNELS
                )
            else:
                # Usa valori di default se non c'è backup
                wavelet = BinarySteganography.WAVELET
                channel_idx = BinarySteganography.CHANNEL
                bands = BinarySteganography.BANDS
                alpha = BinarySteganography.ALPHA
                use_all_channels = BinarySteganography.USE_ALL_CHANNELS

        print(
            f"DWT Get Binary - Parametri: WAVELET={wavelet}, ALPHA={alpha}, BANDS={bands}, USE_ALL_CHANNELS={use_all_channels}"
        )

        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Recuperando file binario con DWT (dimensione dall'header)...")
        img_array = np.array(img, dtype=np.float32)

        # Determina quali canali usare (deve corrispondere a hide)
        channels_to_use = [0, 1, 2] if use_all_channels else [channel_idx]
        extracted_bits = []

        # Assicura che bands non sia None
        if bands is None:
            bands = ["cH"]

        # === ESTRAZIONE SINCRONIZZATA IN DUE FASI ===
        # FASE 1: Estrai solo header (64 bit) + size (32 bit) = 96 bit
        # FASE 2: Calcola quanti bit servono e continua estrazione

        HEADER_BITS = 64
        SIZE_BITS = 32
        TERMINATOR_BITS = 16
        magic_header = (
            "1100100100001111010110010100110011010101010011110000101011001101"
        )

        # FASE 1: Estrai primi 96 bit (header + size)
        bits_needed = HEADER_BITS + SIZE_BITS
        extracted_bits = []

        for ch_idx in channels_to_use:
            if len(extracted_bits) >= bits_needed:
                break

            channel_data = img_array[:, :, ch_idx]
            coeffs = pywt.dwt2(channel_data, wavelet)
            cA, (cH, cV, cD) = coeffs
            band_map = {"cH": cH, "cV": cV, "cD": cD}

            for band_name in bands:
                if band_name not in band_map:
                    continue
                if len(extracted_bits) >= bits_needed:
                    break

                coeff_flat = band_map[band_name].flatten()
                for coeff in coeff_flat:
                    if len(extracted_bits) >= bits_needed:
                        break
                    extracted_bits.append("1" if coeff > 0 else "0")

        bitstream = "".join(extracted_bits)

        # Verifica header DEVE essere all'inizio (no find!)
        if len(bitstream) < HEADER_BITS + SIZE_BITS:
            raise ValueError(
                "Immagine troppo piccola o corrotta: impossibile leggere header"
            )

        if bitstream[:HEADER_BITS] != magic_header:
            raise ValueError(
                "Header non valido: nessun file DWT nascosto trovato. "
                "Possibili cause: (1) Metodo sbagliato (usa LSB/PVD invece di DWT), "
                "(2) Immagine corrotta, (3) Parametri errati (wavelet/bands/channels diversi)"
            )

        # Decodifica file_size dai bit 64-96
        file_size_binary = bitstream[HEADER_BITS : HEADER_BITS + SIZE_BITS]
        file_size = int(file_size_binary, 2)

        # FASE 2: Calcola bit totali necessari e continua estrazione
        total_bits_needed = HEADER_BITS + SIZE_BITS + (file_size * 8) + TERMINATOR_BITS

        # Continua estrazione per il payload rimanente (solo se servono più bit)
        if len(extracted_bits) < total_bits_needed:
            # Traccia posizione: quale canale, banda e coefficiente abbiamo letto finora
            bits_read = len(extracted_bits)
            current_bit_index = 0

            for ch_idx in channels_to_use:
                if len(extracted_bits) >= total_bits_needed:
                    break

                channel_data = img_array[:, :, ch_idx]
                coeffs = pywt.dwt2(channel_data, wavelet)
                cA, (cH, cV, cD) = coeffs
                band_map = {"cH": cH, "cV": cV, "cD": cD}

                for band_name in bands:
                    if band_name not in band_map:
                        continue
                    if len(extracted_bits) >= total_bits_needed:
                        break

                    coeff_flat = band_map[band_name].flatten()
                    for coeff in coeff_flat:
                        # Salta i bit già estratti nella FASE 1
                        if current_bit_index < bits_read:
                            current_bit_index += 1
                            continue

                        if len(extracted_bits) >= total_bits_needed:
                            break
                        extracted_bits.append("1" if coeff > 0 else "0")
                        current_bit_index += 1

        bitstream = "".join(extracted_bits)

        # Estrai payload file (dopo header + size)
        file_start = HEADER_BITS + SIZE_BITS
        file_end = file_start + (file_size * 8)
        file_binary = bitstream[file_start:file_end]

        # Ricostruisce il file
        file_bytes = bytearray()
        for i in range(0, len(file_binary), 8):
            byte = file_binary[i : i + 8]
            if len(byte) == 8:
                file_bytes.append(int(byte, 2))

        with open(output_path, "wb") as f:
            f.write(file_bytes)

        print(f"File recuperato e salvato in {output_path}")

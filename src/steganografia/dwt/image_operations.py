"""
Operazioni di steganografia per immagini usando DWT (Discrete Wavelet Transform)
"""

import numpy as np
import pywt
from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..metrics import QualityMetrics


class ImageSteganography:
    """Classe per operazioni di steganografia su immagini usando DWT"""

    WAVELET: str = "haar"  # Wavelet di Haar per semplicità
    LEVEL: int = 1  # Livello decomposizione (1=veloce, 2=più robusto ma meno capacità)
    SEED: int = 42  # Seed fisso per determinismo
    STEP: float = 12.0  # Step di quantizzazione QIM (8-32: capacità vs qualità)
    CHANNEL: int = 0  # Usa solo canale R (grayscale-like) per robustezza
    BITS_SECRET: int = 3  # Bit per pixel dell'immagine segreta (2-4 MSB)
    BANDS: list[str] = [
        "cH",
        "cV",
    ]  # Bande DWT da usare: ['cH'] | ['cH','cV'] | ['cH','cV','cD']

    @staticmethod
    def hide_image(
        host_img: Image.Image,
        secret_img: Image.Image,
        backup_file: str | None = None,
        **kwargs,  # Ignora lsb, msb, div per compatibilità API
    ) -> tuple[Image.Image, int, int, float, int, int, dict]:
        """
        Nasconde un'immagine in un'altra usando DWT

        Args:
            host_img: Immagine host
            secret_img: Immagine da nascondere
            backup_file: File di backup opzionale
        """
        # Validazione dimensioni DWT (usa calcolo personalizzato)
        # Non usa validate_image_size_for_image perché DWT ha capacità diversa da LSB

        # Converte in RGB
        if host_img.mode != "RGB":
            host_img = host_img.convert("RGB")
        if secret_img.mode != "RGB":
            secret_img = secret_img.convert("RGB")

        print("Nascondendo immagine con DWT...")
        original_host = host_img.copy()
        host_array = np.array(host_img, dtype=np.float32)
        secret_array = np.array(secret_img, dtype=np.float32).flatten()

        secret_width, secret_height = secret_img.size

        # Riduce profondità bit per robustezza: parametrizzabile
        bits_secret = ImageSteganography.BITS_SECRET
        secret_bits = []
        for pixel_value in secret_array:
            # Prende solo i bit più significativi (riduzione parametrica)
            shift = 8 - bits_secret
            msb_value = int(pixel_value) >> shift
            secret_bits.append(format(msb_value, f"0{bits_secret}b"))
        secret_binary = "".join(secret_bits)

        # Calcola capacità totale disponibile (selezione deterministica fissa)
        step = ImageSteganography.STEP
        channel_idx = ImageSteganography.CHANNEL
        rng = np.random.default_rng(ImageSteganography.SEED)

        # DWT sul canale selezionato
        channel_data = host_array[:, :, channel_idx]
        coeffs = pywt.dwt2(channel_data, ImageSteganography.WAVELET)
        cA, (cH, cV, cD) = coeffs

        # Raccoglie coefficienti da tutte le bande configurate
        band_map = {"cH": cH, "cV": cV, "cD": cD}
        selected_bands = ImageSteganography.BANDS

        print(
            f"DWT Hide - Parametri: STEP={step}, BITS={bits_secret}, BANDS={selected_bands}"
        )

        all_coeffs = []
        for band_name in selected_bands:
            if band_name in band_map:
                coeff_flat = band_map[band_name].flatten()
                # USA TUTTI i coefficienti (nessun filtro, come quando funzionava)
                # Questo garantisce determinismo perfetto tra hide e get
                for idx in range(len(coeff_flat)):
                    all_coeffs.append((band_name, idx, coeff_flat[idx]))

        total_usable = len(all_coeffs)
        if len(secret_binary) > total_usable:
            raise ValueError(
                f"Immagine host troppo piccola per DWT. "
                f"Richiesti: {len(secret_binary)} bit, Disponibili: {total_usable} bit. "
                f"Host: {host_img.width}x{host_img.height}, Secret: {secret_img.width}x{secret_img.height}"
            )

        # Shuffle deterministico della lista completa
        rng.shuffle(all_coeffs)
        selected_coeffs = all_coeffs[: len(secret_binary)]

        # Embedding dei bit con QIM bin-centered su tutte le bande
        band_arrays = {name: band_map[name].flatten().copy() for name in selected_bands}

        for bit_idx, (band_name, flat_idx, original_val) in enumerate(selected_coeffs):
            bit_value = int(secret_binary[bit_idx])
            coeff_value = band_arrays[band_name][flat_idx]
            sign = np.sign(coeff_value)
            if sign == 0:
                sign = 1  # Default per coefficienti nulli
            abs_val = abs(coeff_value)

            # QIM: determina parità target (0=pari, 1=dispari)
            quantized_index = int(abs_val // step)
            if quantized_index % 2 != bit_value:
                quantized_index += 1 if bit_value == 1 else -1
            if quantized_index < 0:
                quantized_index = 0

            # Scrive al CENTRO del bin per robustezza numerica
            new_abs_val = (quantized_index + 0.5) * step
            band_arrays[band_name][flat_idx] = sign * new_abs_val

        # Ricostruisce tutte le bande modificate
        for band_name in selected_bands:
            if band_name == "cH":
                cH = band_arrays[band_name].reshape(cH.shape)
            elif band_name == "cV":
                cV = band_arrays[band_name].reshape(cV.shape)
            elif band_name == "cD":
                cD = band_arrays[band_name].reshape(cD.shape)
        reconstructed = pywt.idwt2((cA, (cH, cV, cD)), ImageSteganography.WAVELET)
        reconstructed = reconstructed[: channel_data.shape[0], : channel_data.shape[1]]
        host_array[:, :, channel_idx] = reconstructed

        host_array = np.clip(host_array, 0, 255).astype(np.uint8)
        result_img = Image.fromarray(host_array, mode="RGB")

        # Salva parametri (sempre nella cache, opzionalmente su file)
        params = {
            "method": "dwt",
            "width": secret_width,
            "height": secret_height,
            "wavelet": ImageSteganography.WAVELET,
            "seed": ImageSteganography.SEED,
            "step": ImageSteganography.STEP,
            "channel": ImageSteganography.CHANNEL,
            "bits_per_pixel": ImageSteganography.BITS_SECRET,
            "level": ImageSteganography.LEVEL,
            "bands": ImageSteganography.BANDS,
        }
        backup_system.save_backup_data(DataType.IMAGE, params, backup_file)

        metrics = QualityMetrics.calculate_metrics(original_host, result_img)
        print("Immagine nascosta con successo usando DWT")

        # Restituisce con parametri dummy per compatibilità
        return result_img, 1, 8, 0.0, secret_width, secret_height, metrics

    @staticmethod
    def get_image(
        img: Image.Image,
        output_path: str,
        width: int | None = None,
        height: int | None = None,
        backup_file: str | None = None,
        **kwargs,  # Ignora lsb, msb, div per compatibilità API
    ) -> Image.Image:
        """
        Recupera un'immagine nascosta usando DWT

        Args:
            img: Immagine contenente l'immagine nascosta
            output_path: Percorso di output
            width: Larghezza dell'immagine nascosta (manuale)
            height: Altezza dell'immagine nascosta (manuale)
            backup_file: File di backup opzionale
        """
        # Carica parametri da backup se necessario
        if backup_file:
            backup_data = backup_system.load_backup_data(backup_file)
            if backup_data and "params" in backup_data:
                # MERGE: parametri manuali hanno priorità
                width = (
                    width if width is not None else backup_data["params"].get("width")
                )
                height = (
                    height
                    if height is not None
                    else backup_data["params"].get("height")
                )
                # CRITICO: carica TUTTI i parametri DWT usati durante hide
                ImageSteganography.WAVELET = backup_data["params"].get(
                    "wavelet", ImageSteganography.WAVELET
                )
                ImageSteganography.STEP = backup_data["params"].get(
                    "step", ImageSteganography.STEP
                )
                ImageSteganography.BITS_SECRET = backup_data["params"].get(
                    "bits_per_pixel", ImageSteganography.BITS_SECRET
                )
                ImageSteganography.BANDS = backup_data["params"].get(
                    "bands", ImageSteganography.BANDS
                )
                ImageSteganography.LEVEL = backup_data["params"].get(
                    "level", ImageSteganography.LEVEL
                )
                ImageSteganography.SEED = backup_data["params"].get(
                    "seed", ImageSteganography.SEED
                )
                ImageSteganography.CHANNEL = backup_data["params"].get(
                    "channel", ImageSteganography.CHANNEL
                )
                print(
                    f"Parametri DWT caricati da backup: WAVELET={ImageSteganography.WAVELET}, STEP={ImageSteganography.STEP}, "
                    f"BITS={ImageSteganography.BITS_SECRET}, BANDS={ImageSteganography.BANDS}"
                )

        # Se non c'è backup, prova a recuperare dall'ultima operazione
        if width is None or height is None:
            recent_params = backup_system.get_last_params(DataType.IMAGE)
            if recent_params:
                print("Usando parametri dall'ultima operazione di nascondimento")
                width = recent_params.get("width")
                height = recent_params.get("height")
                # Carica anche i parametri DWT dalla cache
                ImageSteganography.WAVELET = recent_params.get(
                    "wavelet", ImageSteganography.WAVELET
                )
                ImageSteganography.STEP = recent_params.get(
                    "step", ImageSteganography.STEP
                )
                ImageSteganography.BITS_SECRET = recent_params.get(
                    "bits_per_pixel", ImageSteganography.BITS_SECRET
                )
                ImageSteganography.BANDS = recent_params.get(
                    "bands", ImageSteganography.BANDS
                )
                ImageSteganography.LEVEL = recent_params.get(
                    "level", ImageSteganography.LEVEL
                )
                ImageSteganography.SEED = recent_params.get(
                    "seed", ImageSteganography.SEED
                )
                ImageSteganography.CHANNEL = recent_params.get(
                    "channel", ImageSteganography.CHANNEL
                )
                print(
                    f"Parametri DWT dalla cache: WAVELET={ImageSteganography.WAVELET}, STEP={ImageSteganography.STEP}, "
                    f"BITS={ImageSteganography.BITS_SECRET}, BANDS={ImageSteganography.BANDS}"
                )

        if width is None or height is None:
            raise ValueError(ErrorMessages.PARAMS_MISSING)

        if img.mode != "RGB":
            img = img.convert("RGB")

        print("Recuperando immagine con DWT...")
        img_array = np.array(img, dtype=np.float32)

        # Riduzione profondità bit parametrica
        bits_secret = ImageSteganography.BITS_SECRET
        total_bits_needed = width * height * 3 * bits_secret
        extracted_bits = []

        # Stessi parametri del nascondimento
        step = ImageSteganography.STEP
        channel_idx = ImageSteganography.CHANNEL
        rng = np.random.default_rng(ImageSteganography.SEED)  # Stesso seed

        # DWT sul canale selezionato
        channel_data = img_array[:, :, channel_idx]
        coeffs = pywt.dwt2(channel_data, ImageSteganography.WAVELET)
        cA, (cH, cV, cD) = coeffs

        # Raccoglie coefficienti da tutte le bande configurate (STESSA logica di hide)
        band_map = {"cH": cH, "cV": cV, "cD": cD}
        selected_bands = ImageSteganography.BANDS

        print(
            f"DWT Get - Parametri: STEP={step}, BITS={bits_secret}, BANDS={selected_bands}"
        )

        all_coeffs = []
        for band_name in selected_bands:
            if band_name in band_map:
                coeff_flat = band_map[band_name].flatten()
                # USA TUTTI i coefficienti (STESSO metodo di hide, nessun filtro)
                for idx in range(len(coeff_flat)):
                    all_coeffs.append((band_name, idx, coeff_flat[idx]))

        # STESSO shuffle deterministico
        rng.shuffle(all_coeffs)
        selected_coeffs = all_coeffs[:total_bits_needed]

        # Estrazione dei bit con QIM bin-centered
        for band_name, flat_idx, coeff_value in selected_coeffs:
            if len(extracted_bits) >= total_bits_needed:
                break

            abs_val = abs(coeff_value)
            # Decodifica QIM dal centro del bin
            quantized_index = int(round(float(abs_val) / step - 0.5))
            bit_value = quantized_index % 2  # Legge parità (0=pari, 1=dispari)
            extracted_bits.append(str(bit_value))

        # Verifica di aver estratto abbastanza bit
        if len(extracted_bits) < total_bits_needed:
            raise ValueError(
                f"Non abbastanza dati estratti. Estratti: {len(extracted_bits)} bit, "
                f"Richiesti: {total_bits_needed} bit per immagine {width}x{height}"
            )

        # Ricostruisce l'immagine (espande N bit a 8 bit)
        secret_binary = "".join(extracted_bits[:total_bits_needed])
        secret_pixels = []

        for i in range(0, len(secret_binary), bits_secret):
            bits = secret_binary[i : i + bits_secret]
            if len(bits) == bits_secret:
                # Espande N MSB a 8 bit (shifta a sinistra)
                shift = 8 - bits_secret
                pixel_value = int(bits, 2) << shift
                secret_pixels.append(pixel_value)

        secret_array = np.array(secret_pixels, dtype=np.uint8)
        secret_array = secret_array.reshape((height, width, 3))
        secret_img = Image.fromarray(secret_array, mode="RGB")
        secret_img.save(output_path)

        print(f"Immagine recuperata e salvata in {output_path}")
        return secret_img

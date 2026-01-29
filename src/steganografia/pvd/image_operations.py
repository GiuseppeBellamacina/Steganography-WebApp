"""
Image steganography using PVD (Pixel Value Differencing)
Wu & Tsai (2003) inspired implementation
"""

import numpy as np
from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class ImageSteganography:
    """
    PVD-based image steganography
    """

    # === Quantization ranges ===
    # (lower, upper, bits)
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
    PAIR_STEP: int = 1  # sparsity
    CHANNELS = [0, 1, 2]  # RGB

    # ======================================================
    # Configuration helpers
    # ======================================================

    @staticmethod
    def configure_quality_mode():
        ImageSteganography.RANGES = ImageSteganography.RANGES_QUALITY
        ImageSteganography.PAIR_STEP = 2
        ImageSteganography.CHANNELS = [0, 1]
        print("PVD configured: QUALITY mode")

    @staticmethod
    def configure_capacity_mode():
        ImageSteganography.RANGES = ImageSteganography.RANGES_CAPACITY
        ImageSteganography.PAIR_STEP = 1
        ImageSteganography.CHANNELS = [0, 1, 2]
        print("PVD configured: CAPACITY mode")

    @staticmethod
    def configure_custom(
        pair_step: int = 1,
        channels: list[int] | None = None,
        use_quality_ranges: bool = True,
    ):
        ImageSteganography.PAIR_STEP = max(1, pair_step)
        ImageSteganography.CHANNELS = channels or [0, 1, 2]
        ImageSteganography.RANGES = (
            ImageSteganography.RANGES_QUALITY
            if use_quality_ranges
            else ImageSteganography.RANGES_CAPACITY
        )
        print(
            f"PVD custom config | step={ImageSteganography.PAIR_STEP}, "
            f"channels={ImageSteganography.CHANNELS}"
        )

    # ======================================================
    # Core PVD logic
    # ======================================================

    @staticmethod
    def _range_for_difference(diff: int):
        d = abs(diff)
        for low, high, bits in ImageSteganography.RANGES:
            if low <= d <= high:
                return low, high, bits
        # FIX: usa l'ultimo range definito invece di hardcoded (compatibile con QUALITY e CAPACITY)
        return ImageSteganography.RANGES[-1]

    @staticmethod
    def _embed_pair(p1: int, p2: int, bits: str):
        diff = p2 - p1
        low, high, capacity = ImageSteganography._range_for_difference(diff)

        bits = bits[:capacity]
        if not bits:
            return p1, p2, 0

        value = int(bits, 2)
        new_diff = low + value
        new_diff = min(new_diff, high)
        new_diff = -new_diff if diff < 0 else new_diff

        delta = new_diff - diff

        # 🔧 Ottimizzazione: evita micro-shift quando value == 0
        if delta == 0:
            return p1, p2, len(bits)

        if diff % 2 == 0:
            p1 -= delta // 2
            p2 += delta - delta // 2
        else:
            p1 -= (delta + 1) // 2
            p2 += delta - (delta + 1) // 2

        p1 = np.clip(p1, 0, 255)
        p2 = np.clip(p2, 0, 255)

        return int(p1), int(p2), len(bits)

    @staticmethod
    def _extract_pair(p1: int, p2: int):
        diff = p2 - p1
        low, _, capacity = ImageSteganography._range_for_difference(diff)
        value = abs(diff) - low

        # Clamp difensivo per casi limite
        value = max(0, min(value, (1 << capacity) - 1))

        return format(value, f"0{capacity}b")

    # ======================================================
    # Public API
    # ======================================================

    @staticmethod
    def hide_image(
        host_img: Image.Image,
        secret_img: Image.Image,
        backup_file: str | None = None,
        **kwargs,
    ):
        ParameterValidator.validate_image_size_for_image(host_img, secret_img, 1, 8)

        host_img = host_img.convert("RGB")
        secret_img = secret_img.convert("RGB")

        original = host_img.copy()
        host = np.array(host_img, dtype=np.int32)
        secret = np.array(secret_img, dtype=np.uint8).flatten()

        width, height = secret_img.size

        # ⚠️ IMPORTANTE: PVD è LOSSY RECOVERY (non reversibile al 100%)
        # - SECRET_BITS = 2 raccomandato per qualità ottimale (PSNR > 40 dB)
        # - Riduciamo la precisione: buttiamo via (8 - SECRET_BITS) bit per canale
        # - L'immagine recuperata sarà simile ma non identica (quantizzazione intenzionale)
        SECRET_BITS = 2
        shift = 8 - SECRET_BITS
        secret_bits = "".join(format(px >> shift, f"0{SECRET_BITS}b") for px in secret)

        bit_idx = 0
        h, w, _ = host.shape

        for ch in ImageSteganography.CHANNELS:
            for y in range(h):
                # FIX: usa w - PAIR_STEP per evitare out-of-bounds quando x + PAIR_STEP
                for x in range(
                    0,
                    w - ImageSteganography.PAIR_STEP,
                    2 * ImageSteganography.PAIR_STEP,
                ):
                    if bit_idx >= len(secret_bits):
                        break

                    p1 = host[y, x, ch]
                    p2 = host[y, x + ImageSteganography.PAIR_STEP, ch]

                    low, high, cap = ImageSteganography._range_for_difference(p2 - p1)
                    chunk = secret_bits[bit_idx : bit_idx + cap]

                    p1n, p2n, used = ImageSteganography._embed_pair(p1, p2, chunk)
                    host[y, x, ch] = p1n
                    host[y, x + ImageSteganography.PAIR_STEP, ch] = p2n
                    bit_idx += used

                if bit_idx >= len(secret_bits):
                    break
            if bit_idx >= len(secret_bits):
                break

        if bit_idx < len(secret_bits):
            raise ValueError(ErrorMessages.IMAGE_TOO_SMALL_IMAGE)

        stego = Image.fromarray(host.astype(np.uint8), "RGB")

        # Calcola percentuale di bit usati
        total_bits_host = h * w * len(ImageSteganography.CHANNELS)
        percentage = format((bit_idx / total_bits_host) * 100, ".2f")
        print(
            f"TERMINATO - Percentuale di pixel usati con PVD: {percentage}% ({bit_idx}/{total_bits_host} bit)"
        )

        # Determina se RANGES è quality o capacity
        is_quality = ImageSteganography.RANGES == ImageSteganography.RANGES_QUALITY
        params = {
            "method": "pvd",
            "width": width,
            "height": height,
            "secret_bits": SECRET_BITS,
            "pair_step": ImageSteganography.PAIR_STEP,
            "channels": ImageSteganography.CHANNELS,
            "ranges_type": "quality" if is_quality else "capacity",
        }
        backup_system.save_backup_data(DataType.IMAGE, params, backup_file)

        metrics = QualityMetrics.calculate_metrics(original, stego)
        return stego, 1, 8, 0.0, width, height, metrics, float(percentage)

    @staticmethod
    def get_image(
        img: Image.Image,
        output_path: str,
        width: int | None = None,
        height: int | None = None,
        backup_file: str | None = None,
        **kwargs,
    ):
        img = img.convert("RGB")

        # Carica parametri con gestione None
        if backup_file:
            backup_data = backup_system.load_backup_data(backup_file)
            if backup_data and "params" in backup_data:
                data = backup_data["params"]
            else:
                data = backup_system.get_last_params(DataType.IMAGE)
        else:
            data = backup_system.get_last_params(DataType.IMAGE)

        if not data:
            raise ValueError(ErrorMessages.PARAMS_MISSING)

        # MERGE: parametri manuali hanno priorità su backup
        width = width if width is not None else data["width"]
        height = height if height is not None else data["height"]

        # Type safety: garantisce che width e height non siano None
        if width is None or height is None:
            raise ValueError("Width e height mancanti nei parametri di backup")

        SECRET_BITS = data.get("secret_bits", 2)  # Default: 2 bit (qualità ottimale)
        pair_step = data.get("pair_step", ImageSteganography.PAIR_STEP)
        channels = data.get("channels", ImageSteganography.CHANNELS)
        # Carica RANGES
        ranges_type = data.get("ranges_type", "quality")
        ImageSteganography.RANGES = (
            ImageSteganography.RANGES_QUALITY
            if ranges_type == "quality"
            else ImageSteganography.RANGES_CAPACITY
        )

        # FIX: usa len(channels) invece di hardcoded 3 per total_bits
        total_bits = width * height * len(channels) * SECRET_BITS

        arr = np.array(img, dtype=np.int32)
        extracted = []
        count = 0

        h, w, _ = arr.shape
        for ch in channels:
            for y in range(h):
                # FIX: usa w - pair_step per evitare out-of-bounds
                for x in range(0, w - pair_step, 2 * pair_step):
                    if count >= total_bits:
                        break
                    bits = ImageSteganography._extract_pair(
                        arr[y, x, ch],
                        arr[y, x + pair_step, ch],
                    )
                    extracted.append(bits)
                    count += len(bits)
                if count >= total_bits:
                    break
            if count >= total_bits:
                break

        bitstream = "".join(extracted)[:total_bits]

        # ⚠️ Ricostruzione LOSSY: shiftiamo indietro i bit ridotti
        # L'immagine recuperata ha perdita di precisione di (8 - SECRET_BITS) bit/canale
        # Questa è la natura intrinseca di PVD, non un bug
        pixels = []
        shift = 8 - SECRET_BITS
        for i in range(0, len(bitstream), SECRET_BITS):
            chunk = bitstream[i : i + SECRET_BITS]
            pixels.append(int(chunk, 2) << shift)

        secret = np.array(pixels[: width * height * 3], dtype=np.uint8)
        secret = secret.reshape((height, width, 3))
        result = Image.fromarray(secret, "RGB")
        result.save(output_path)

        return result

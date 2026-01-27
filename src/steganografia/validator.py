"""
Validazione dei parametri per le operazioni di steganografia
"""

from PIL import Image

from config.constants import CompressionMode, ErrorMessages, ValidationLimits


class ParameterValidator:
    """Validatore per i parametri di steganografia"""

    @staticmethod
    def validate_lsb(lsb: int) -> None:
        """Valida il parametro LSB"""
        if lsb < ValidationLimits.MIN_LSB or lsb > ValidationLimits.MAX_LSB:
            raise ValueError(ErrorMessages.INVALID_LSB)

    @staticmethod
    def validate_msb(msb: int) -> None:
        """Valida il parametro MSB"""
        if msb < ValidationLimits.MIN_MSB or msb > ValidationLimits.MAX_MSB:
            raise ValueError(ErrorMessages.INVALID_MSB)

    @staticmethod
    def validate_n(n: int) -> None:
        """Valida il parametro N"""
        if n < ValidationLimits.MIN_N or n > ValidationLimits.MAX_N:
            raise ValueError(ErrorMessages.INVALID_N)

    @staticmethod
    def validate_compression_mode(zip_mode: int) -> None:
        """Valida la modalità di compressione"""
        if zip_mode not in [
            CompressionMode.NO_ZIP,
            CompressionMode.FILE,
            CompressionMode.DIR,
        ]:
            raise ValueError(ErrorMessages.INVALID_ZIP_MODE)

    @staticmethod
    def validate_lsb_msb_relationship(lsb: int, msb: int) -> None:
        """Valida la relazione tra LSB e MSB"""
        if lsb > msb:
            raise ValueError(ErrorMessages.LSB_GREATER_MSB)

    @staticmethod
    def validate_image_size_for_message(img: Image.Image, message: str) -> None:
        """Valida che l'immagine sia abbastanza grande per il messaggio"""
        if (img.width * img.height) * 3 < len(message) * 8:
            raise ValueError(
                ErrorMessages.IMAGE_TOO_SMALL_MESSAGE.format(
                    msg_len=len(message), width=img.width, height=img.height
                )
            )

    @staticmethod
    def validate_image_size_for_image(
        host_img: Image.Image, secret_img: Image.Image, lsb: int, msb: int
    ) -> None:
        """Valida che l'immagine host sia abbastanza grande per l'immagine segreta"""
        if (lsb * host_img.width * host_img.height * 3) < (
            msb * secret_img.width * secret_img.height * 3
        ):
            raise ValueError(
                ErrorMessages.IMAGE_TOO_SMALL_IMAGE.format(
                    host_width=host_img.width,
                    host_height=host_img.height,
                    secret_width=secret_img.width,
                    secret_height=secret_img.height,
                )
            )

    @staticmethod
    def validate_image_size_for_file(
        img: Image.Image, file_size: int, n: int, channels: int
    ) -> None:
        """Valida che l'immagine sia abbastanza grande per il file"""
        if (img.width * img.height) * channels * n < file_size * 8:
            raise ValueError(
                ErrorMessages.IMAGE_TOO_SMALL_FILE.format(
                    file_size=file_size, width=img.width, height=img.height
                )
            )

    @staticmethod
    def validate_div_for_images(
        div: float, arr1_len: int, arr2_len: int, lsb: int, msb: int
    ) -> None:
        """Valida il parametro DIV per le immagini"""
        if div * arr2_len * msb > arr1_len * lsb:
            raise ValueError(ErrorMessages.DIV_EXCESSIVE.format(div=div))

    @staticmethod
    def validate_div_for_file(div: float, total_pixels: int, file_size: int, n: int) -> None:
        """Valida il parametro DIV per i file"""
        if total_pixels * n < div * file_size * 8:
            raise ValueError(ErrorMessages.DIV_EXCESSIVE.format(div=div))

    @staticmethod
    def validate_recovery_params(*params) -> None:
        """Valida che tutti i parametri necessari per il recupero siano presenti"""
        if any(param is None for param in params):
            raise ValueError(ErrorMessages.PARAMS_MISSING)

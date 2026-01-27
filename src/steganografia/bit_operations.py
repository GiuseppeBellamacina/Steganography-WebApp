"""
Operazioni core per la manipolazione dei bit nella steganografia
"""


def binary_convert(text: str) -> str:
    """Converte una stringa di testo in una stringa binaria (carattere per carattere)"""
    return "".join(format(ord(char), "08b") for char in text)


def binary_convert_back(text: str) -> str:
    """Converte una stringa binaria in una stringa di testo (8-bit)"""
    return "".join(chr(int(text[i * 8 : i * 8 + 8], 2)) for i in range(len(text) // 8))


def set_last_bit(value: int, bit: str) -> int:
    """Setta l'ultimo bit di un numero"""
    value_str = format(
        value, "08b"
    )  # converte un intero in una stringa di 8 caratteri (byte)
    value_str = value_str[:7] + bit  # cambia l'ultimo bit
    result = int(value_str, 2)  # riconverte la stringa in un numero
    result = min(255, max(0, result))  # controlla se il numero è fuori range
    return result


def set_last_n_bits(value: int, bits: str, n: int) -> int:
    """Setta gli ultimi n bits di un numero"""
    value_str = format(value, "08b")
    n = min(n, len(bits))
    value_str = value_str[:-n] + bits
    result = int(value_str, 2)
    result = min(255, max(0, result))
    return result


def set_color_component(mat, i: int, j: int, color: int, channel: int):
    """Cambia una componente di colore RGB di un pixel"""
    if channel == 0:
        mat[i, j] = (color, mat[i, j][1], mat[i, j][2])
    elif channel == 1:
        mat[i, j] = (mat[i, j][0], color, mat[i, j][2])
    elif channel == 2:
        mat[i, j] = (mat[i, j][0], mat[i, j][1], color)
    return mat


def string_to_bytes(bit_string: str) -> bytearray:
    """Converte una stringa di bit in bytes"""
    byte_array = bytearray()
    for i in range(0, len(bit_string), 8):
        byte = bit_string[i : i + 8]
        if len(byte) == 8:
            byte_array.append(int(byte, 2))
    return byte_array

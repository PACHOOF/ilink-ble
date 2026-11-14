"""Comprueba que las tramas generadas coinciden con las capturadas de la app oficial.

Uso: python test_protocol.py
"""

from protocol import build_frame, frame_on, frame_off, frame_brightness


def test():
    # Tramas capturadas de la app iLink
    assert frame_off() == bytes.fromhex("55AA01080500F2")
    assert frame_on() == bytes.fromhex("55AA01080501F1")
    assert frame_brightness(0xFF) == bytes.fromhex("55AA010801FFF7")
    assert frame_brightness(0x00) == bytes.fromhex("55AA01080100F6")

    # Trama de varios bytes de datos (sincronización de hora 20:46:03)
    assert build_frame(0x05, 0x01, [0x14, 0x2E, 0x03]) == bytes.fromhex("55AA030501142E03B2")

    # Tramas sin datos
    assert build_frame(0x0B, 0x01, []) == bytes.fromhex("55AA000B01F4")

    # Validación de rango
    for invalido in (-1, 256):
        try:
            frame_brightness(invalido)
        except ValueError:
            pass
        else:
            raise AssertionError(f"frame_brightness({invalido}) debería fallar")

    print("[+] Todas las pruebas pasan")


if __name__ == "__main__":
    test()

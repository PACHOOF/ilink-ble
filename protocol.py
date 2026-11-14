"""Construcción de tramas del protocolo BLE de la lámpara iLink.

Este módulo no depende de Bluetooth: solo genera los bytes que hay que enviar.
Formato: 55 AA | LEN | CMD | SUB | DATOS | CHK  (ver PROTOCOL.md)
"""


def build_frame(cmd, sub, data):
    header = [0x55, 0xAA]
    cuerpo = [len(data), cmd, sub] + data
    chk = (-sum(cuerpo)) & 0xFF

    return bytes(header + cuerpo + [chk])


def frame_on():
    return build_frame(0x08, 0x05, [0x01])


def frame_off():
    return build_frame(0x08, 0x05, [0x00])


def frame_brightness(val):
    if val < 0 or val > 255:
        raise ValueError("[!] Brillo debe estar entre 0 y 255")
    return build_frame(0x08, 0x01, [val])

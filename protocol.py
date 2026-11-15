"""Construcción de tramas del protocolo BLE de la lámpara iLink.

Este módulo no depende de Bluetooth: solo genera los bytes que hay que enviar.
Formato: 55 AA | LEN | CMD | SUB | DATOS | CHK  (ver PROTOCOL.md)
"""

def frame_on():
    return build_frame(0x08, 0x05, [0x01])

def frame_off():
    return build_frame(0x08, 0x05, [0x00])

def frame_brightness(val):
    if not 0 <= val <= 255: raise ValueError("[!] Brillo debe estar entre 0 y 255")
    return build_frame(0x08, 0x01, [val])

def frame_color(rgb):
    if len(rgb) != 3: raise ValueError("[!] La funcion frame_color solo acepta 3 valores en rgb")
    if any(x < 0 or x > 255 for x in rgb): raise ValueError("[!] Valores de RGB deben estar entre 0 y 255")
    return build_frame(0x08,0x02,list(rgb))

def frame_temperature(val):
    if not 0 <= val <= 255: raise ValueError("[!] Temperatura debe estar entre 0 y 255")
    return build_frame(0x08,0x07,[val])

def frame_ambient_mode(mode):
    if not 1 <= mode <= 5: raise ValueError("[!] Modo de ambiente debe estar entre 1 y 5")
    return build_frame(0x08,0x09,[mode])

def build_frame(cmd,sub,data):
    header = [0x55, 0xAA]
    cuerpo = [len(data),cmd,sub]+data
    chk = (-sum(cuerpo)) & 0xFF

    return bytes(header + cuerpo + [chk])
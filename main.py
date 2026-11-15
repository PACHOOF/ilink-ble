import argparse
import asyncio
import json
from pathlib import Path

from bleak.exc import BleakError

from lamp import Lamp, scan

CONFIG = Path.home() / ".ilink.json"


def load_address():
    """Devuelve la dirección guardada, o None si no hay ninguna."""
    if not CONFIG.exists():
        return None
    try:
        return json.loads(CONFIG.read_text()).get("address")
    except json.JSONDecodeError:
        return None


def save_address(address):
    CONFIG.write_text(json.dumps({"address": address}))


async def get_address(args):
    """Decide qué dirección usar: argumento > guardada > escaneo."""
    if args.address:
        return args.address

    if not args.scan:
        saved = load_address()
        if saved:
            print(f"[*] Usando dirección guardada: {saved}")
            return saved

    print("[*] Buscando la lámpara...")
    device, _ = await scan()
    if device is None:
        return None
    print(f"[+] Lámpara encontrada: {device.address}")
    return device.address


async def main():
    parser = argparse.ArgumentParser(description="Control de lámpara iLink por BLE")
    parser.add_argument("--address", help="dirección de la lámpara (MAC en Windows/Linux, UUID en macOS)")
    parser.add_argument("--scan", action="store_true", help="ignorar la dirección guardada y volver a escanear")
    args = parser.parse_args()

    address = await get_address(args)
    if address is None:
        print("[!] Lámpara no encontrada. ¿Está encendida y con la app oficial cerrada?")
        return

    try:
        async with Lamp(address) as lamp:
            save_address(address)   # se guarda solo si la conexión ha funcionado

            await lamp.off()
            await asyncio.sleep(2)

            await lamp.on()
            await asyncio.sleep(2)

            await lamp.brightness(10)
            await asyncio.sleep(2)

            await lamp.brightness(255)
            await asyncio.sleep(2)

            await lamp.color((255,0,0))
            await asyncio.sleep(2)
            await lamp.color((0, 255, 0))
            await asyncio.sleep(2)
            await lamp.color((0, 0, 255))
            await asyncio.sleep(2)

            await lamp.brightness(10)
            await asyncio.sleep(2)
            await lamp.color((115, 0, 210))
            await asyncio.sleep(2)
            await lamp.brightness(255)
            await asyncio.sleep(2)

            await lamp.temperature(0)
            await asyncio.sleep(2)
            await lamp.temperature(255)
            await asyncio.sleep(2)

            await lamp.ambient_mode(1)
            await asyncio.sleep(2)
            await lamp.ambient_mode(3)
            await asyncio.sleep(2)
            await lamp.ambient_mode(5)
            await asyncio.sleep(2)
    except (BleakError, asyncio.TimeoutError):
        print(f"[!] No se pudo conectar a {address}. Prueba con --scan para buscarla de nuevo.")


if __name__ == "__main__":
    asyncio.run(main())
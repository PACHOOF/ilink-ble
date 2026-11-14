"""Comunicación BLE con la lámpara iLink."""

import protocol
from bleak import BleakScanner, BleakClient

LAMP_SERVICE_UUID = "0000a032-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000a040-0000-1000-8000-00805f9b34fb"


async def scan():
    devices = await BleakScanner.discover(timeout=5, return_adv=True)
    for d, adv in devices.values():
        if LAMP_SERVICE_UUID in adv.service_uuids:
            return d, adv
    return None, None


class Lamp:
    def __init__(self, device):
        self.device = device
        self.client = BleakClient(device)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def connect(self):
        await self.client.connect()

    async def disconnect(self):
        await self.client.disconnect()

    async def _send(self, frame):
        await self.client.write_gatt_char(char_specifier=CHARACTERISTIC_UUID, data=frame, response=True)

    async def on(self):
        await self._send(protocol.frame_on())

    async def off(self):
        await self._send(protocol.frame_off())

    async def brightness(self, val):
        await self._send(protocol.frame_brightness(val))

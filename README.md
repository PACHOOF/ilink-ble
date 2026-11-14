# ilink-ble

Documentación del protocolo Bluetooth Low Energy de una lámpara inteligente controlada con la app **iLink**, obtenida por ingeniería inversa para poder controlarla sin la app oficial.

## Estado

| Función | Estado |
| --- | --- |
| Formato de trama y checksum | ✅ Descifrado |
| Brillo | ✅ Confirmado |
| Encender / apagar | ✅ Confirmado |
| Sincronizar hora | 🟡 Deducido, sin probar |
| Color (RGB) | ❌ Pendiente |
| Modos y efectos | ❌ Pendiente |

## Resumen rápido

Las órdenes se escriben en la característica `0xA040` del servicio `0xA032` con este formato:

```
55 AA | LEN | CMD | SUB | DATOS | CHK
CHK = (0x100 - (LEN + CMD + SUB + DATOS...)) & 0xFF
```

| Acción | Trama |
| --- | --- |
| Encender | `55AA01080501F1` |
| Apagar | `55AA01080500F2` |
| Brillo 50 % | `55AA0108018076` |

## Documentación

- [`PROTOCOL.md`](PROTOCOL.md): perfil GATT, formato de trama, comandos conocidos y pendientes.
- [`METHODOLOGY.md`](METHODOLOGY.md): cómo se ha capturado el tráfico y cómo se ha deducido cada campo.

## Uso

Requiere Python 3.9+ y un ordenador con Bluetooth LE. La app oficial debe estar cerrada en el móvil, porque la lámpara solo acepta una conexión a la vez.

```bash
git clone https://github.com/PACHOOF/ilink-ble.git
cd ilink-ble
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py                   # busca la lámpara y ejecuta la demo
python main.py --scan            # ignora la dirección guardada y vuelve a buscar
python main.py --address XX:XX:XX:XX:XX:XX
```

La primera vez busca la lámpara por su servicio `0xA032` y, si la conexión funciona, guarda la dirección en `~/.ilink.json` para no tener que escanear la próxima vez.

> **macOS:** CoreBluetooth no expone la MAC, así que la dirección es un UUID propio de cada Mac.

La demo apaga la lámpara, la enciende y cambia el brillo al mínimo y al máximo.

### Usarlo desde tu propio código

```python
import asyncio
from lamp import Lamp

async def main():
    async with Lamp("XX:XX:XX:XX:XX:XX") as lamp:
        await lamp.on()
        await lamp.brightness(128)

asyncio.run(main())
```

### Pruebas

```bash
python test_protocol.py
```

Comprueba que las tramas generadas coinciden byte a byte con las capturadas de la app oficial. No necesita Bluetooth.

## Estructura

| Archivo | Contenido |
| --- | --- |
| `protocol.py` | Construcción de tramas y checksum. No depende de Bluetooth. |
| `lamp.py` | Escaneo y clase `Lamp` (conexión y envío con [bleak](https://github.com/hbldh/bleak)). |
| `main.py` | Script de línea de comandos con la demo. |
| `test_protocol.py` | Pruebas de `protocol.py`. |

## Aviso

Proyecto con fines educativos y de interoperabilidad, realizado sobre una lámpara propia. El protocolo no tiene autenticación: cualquier dispositivo dentro del alcance puede controlar la lámpara. Úsalo solo con dispositivos tuyos.

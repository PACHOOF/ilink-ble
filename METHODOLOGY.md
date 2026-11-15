# Cómo se ha obtenido el protocolo

Este documento explica el proceso completo: cómo se capturó el tráfico, qué problemas aparecieron y cómo se dedujo cada campo de la trama. No se ha usado documentación del fabricante ni se ha descompilado la app; todo sale de observar el tráfico Bluetooth.

## 1. Captura en iOS

La captura se hizo con el log HCI del propio iPhone, sin hardware adicional. Este log registra lo que el sistema intercambia con el chip Bluetooth, ya descifrado.

1. Instalar el perfil **Bluetooth for iOS/iPadOS** desde
   `https://developer.apple.com/bug-reporting/profiles-and-logs/?name=bluetooth`
   (basta un Apple ID gratuito). El perfil caduca a los 3 días.
2. Reiniciar el iPhone para que el perfil quede activo.
3. Usar la app de la lámpara apuntando la hora de cada acción, dejando unos 10 segundos entre acciones.
4. Lanzar un sysdiagnose pulsando a la vez los dos botones de volumen y el lateral, y esperar unos 10 minutos.
5. Recogerlo en *Ajustes → Privacidad y seguridad → Análisis y mejoras → Datos de análisis* (`sysdiagnose_….tar.gz`).
6. Descomprimirlo y abrir `logs/Bluetooth/bluetoothd-hci-latest.pklg` (o los otros `bluetoothd-hci-*.pklg`) en Wireshark, que soporta el formato PacketLogger.

Con un Mac también se puede capturar en directo con PacketLogger (incluido en *Additional Tools for Xcode*).

### Limitaciones encontradas

- **El log no guarda los anuncios BLE** de otros dispositivos, así que no sirve para encontrar el dispositivo por su nombre.
- **El log tiene huecos.** Se interrumpe con eventos `AP Sleep`, y en una de las sesiones no quedó registrado ningún tráfico de la lámpara aunque funcionó con normalidad.
- **Los handles de conexión se reutilizan**: el mismo `Connection Handle` puede corresponder a conexiones distintas en momentos distintos.

Si el log de iOS no basta, las alternativas son un Android con el registro HCI de Bluetooth (`btsnoop_hci.log`) o un sniffer por radio como un nRF52840 con nRF Sniffer.

## 2. Localizar la lámpara en la captura

1. **Listar conexiones:**
   `bthci_evt.le_meta_subevent == 0x01 || bthci_evt.le_meta_subevent == 0x0a || bthci_evt.code == 0x03`
2. **Descartar las que no tienen tráfico GATT** comprobando `btatt` por handle de conexión.
3. **Identificar el servicio.** Con nRF Connect se vio que la lámpara anuncia el servicio `0xA032`. En la captura, el filtro
   `btatt.uuid16 == 0xa032 || btatt.uuid16 == 0xa040`
   lleva directamente al descubrimiento de servicios y a todo el tráfico posterior, porque Wireshark asocia cada handle a su UUID.
4. **Leer la tabla de características** en el *Read By Type Response*: ahí aparece que A040 (handle `0x000C`) admite escritura.
5. **Filtrar las órdenes:**
   `btatt.uuid16 == 0xa040 && (btatt.opcode == 0x12 || btatt.opcode == 0x52)`

Para sacar los valores a una tabla:

```
tshark -r captura.pklg -Y "btatt.uuid16 == 0xa040 && btatt.opcode == 0x12" \
  -T fields -e frame.time -e btatt.value
```

## 3. Deducción del formato

### Cabecera

Todas las tramas empiezan por `55 AA`. Un valor fijo al principio de cada mensaje suele ser una cabecera de sincronización.

### Longitud

Había tramas de 6, 7 y 9 bytes, y el tercer byte valía `00`, `01` y `03` respectivamente. En cada caso coincidía con el número de bytes entre el quinto byte y el último. De ahí sale `LEN` y, por posición, `CMD` y `SUB`.

### Checksum

La pista vino de la ráfaga de brillo, donde todas las tramas eran iguales salvo los dos últimos bytes:

```
55AA010801 FE F8
55AA010801 F2 04
55AA010801 EC 0A
55AA010801 00 F6
55AA010801 FF F7
```

Esos dos bytes siempre suman `0xF6` (módulo 256). Si se añaden `01 + 08 + 01`, la suma da `0x100`: el último byte compensa el resto para que el total sea cero. La regla se comprobó después en todas las tramas.

### Significado de cada comando

- **Brillo (`08/01`):** decenas de tramas cada ~90 ms en las que solo cambia un byte, que baja de `FE` a `00` y luego sube hasta `FF`. Ese patrón corresponde a arrastrar un deslizador.
- **Encender/apagar (`08/05`):** `00` y `01` aparecen aislados, separados ~1 s, justo antes de tocar el brillo. El mismo patrón se repite en otra sesión. Un valor `00`/`01` suelto encaja con un interruptor (pendiente de confirmar a mano).
- **Hora (`05/01`):** los datos `14 2E 03` son 20, 46 y 3 en decimal, y el paquete se envió a las 20:46:03 UTC. La app pone en hora la lámpara al conectarse.
- **`0B/01`, `0B/0A`, `08/15`:** solo aparecen al conectar y no hay con qué compararlos, así que siguen sin identificar.

### Localizar órdenes por su contenido

Una vez conocido el formato, no hace falta cuadrar horas entre el iPhone y la captura. Todas las órdenes empiezan por `55 AA`, así que se pueden filtrar directamente:

```
btatt.value[0:2] == 55:aa
```

Y para ver solo las que todavía no se conocen, se excluyen los pares `CMD SUB` ya identificados (bytes 3 y 4 del valor):

```
btatt.value[0:2] == 55:aa && !(btatt.value[3:2] in {08:01 08:05 08:15 0b:01 0b:0a 05:01})
```

Además, la sincronización de hora (`05/01`) que la app envía al conectar lleva la hora UTC dentro de la trama. Eso marca el inicio de cada sesión aunque el reloj de la captura no cuadre.

Así se encontraron el color RGB (`08/02`), la temperatura de blanco (`08/07`), el brillo de la pestaña de temperatura (`08/08`) y los modos (`08/09`): en cada captura se tocó una sola función de la app.

## 4. Verificación

Para confirmar cada comando se envía la trama a la característica A040 (con la app oficial cerrada) y se observa la lámpara. Se puede hacer a mano con nRF Connect o con el script de este repositorio.

Resultados:

- `55AA01080500F2` apaga y `55AA01080501F1` enciende.
- `08/01` cambia el brillo en todo el rango `00`–`FF`.
- Una trama con el checksum mal calculado se ignora, lo que confirma que la lámpara lo valida.
- No hace falta enviar la secuencia inicial de la app ni emparejar.
- Color, temperatura y modos se probaron igual. Además se comprobó en cada uno si enciende la lámpara, si respeta el brillo y si sustituye a los demás, para construir el modelo de estado de `PROTOCOL.md`.

## 5. Herramientas usadas

- Perfil de logging Bluetooth de Apple y sysdiagnose
- Wireshark y tshark
- nRF Connect (iOS) para explorar los servicios GATT

# Protocolo BLE de la lámpara iLink

> **Estado:** encender, apagar, brillo, color RGB, temperatura de blanco y modos están confirmados enviando las tramas desde un script propio. El resto se ha deducido de capturas y está marcado como tal.

## 1. Perfil GATT

La lámpara anuncia el servicio `0xA032` y expone cuatro características propias, además de los servicios estándar Generic Access (`0x1800`) y Generic Attribute (`0x1801`).

| Característica | Propiedades | Handle de valor* | Uso |
| --- | --- | --- | --- |
| `0xA042` | Notify | `0x0009` | Respuestas de la lámpara (sin confirmar) |
| `0xA040` | Write (con respuesta) | `0x000C` | **Órdenes** |
| `0xA041` | Read | `0x000E` | Estado o información (sin confirmar) |
| `0xA043` | Notify | `0x0010` | Respuestas de la lámpara (sin confirmar) |

\* Handles observados en una unidad concreta. Pueden variar entre firmwares; lo fiable es buscar la característica por su UUID.

Todas las órdenes se envían como *Write Request* a **A040**, y la lámpara responde a cada una con un *Write Response* vacío.

## 2. Formato de trama

```
+------+------+-----+-----+-----+--------------+-----+
| 0x55 | 0xAA | LEN | CMD | SUB | DATOS (LEN)  | CHK |
+------+------+-----+-----+-----+--------------+-----+
```

| Campo | Tamaño | Descripción |
| --- | --- | --- |
| `55 AA` | 2 bytes | Cabecera fija |
| `LEN` | 1 byte | Número de bytes del campo `DATOS` |
| `CMD` | 1 byte | Comando |
| `SUB` | 1 byte | Subcomando |
| `DATOS` | `LEN` bytes | Parámetros (puede estar vacío) |
| `CHK` | 1 byte | Checksum |

### Checksum

La suma de todos los bytes desde `LEN` hasta `CHK`, ambos incluidos, es `0x00` módulo 256:

```
CHK = (0x100 - (LEN + CMD + SUB + DATOS...)) & 0xFF
```

Ejemplo con `55 AA 01 08 05 00 F2`:

```
01 + 08 + 05 + 00 = 0x0E
0x100 - 0x0E      = 0xF2  ✓
```

La regla se cumple en todas las tramas capturadas, y la lámpara la comprueba: una trama con el checksum incorrecto se ignora sin dar error.

## 3. Comandos conocidos

### Resumen

| CMD | SUB | Datos | Acción | Estado |
| --- | --- | --- | --- | --- |
| `08` | `01` | `00`–`FF` | Brillo global | ✅ Confirmado |
| `08` | `02` | `RR GG BB` | Color RGB | ✅ Confirmado |
| `08` | `05` | `00` / `01` | Apagar / encender | ✅ Confirmado |
| `08` | `07` | `00` (frío) – `FF` (cálido) | Temperatura de blanco | ✅ Confirmado |
| `08` | `08` | `00`–`FF` | Brillo de la pestaña "Temperatura de color" | 🟡 Comportamiento sin aclarar |
| `08` | `09` | `01`–`05` | Modo de ambiente | ✅ Confirmado |
| `08` | `15` | — | Se envía al conectar | Desconocido |
| `05` | `01` | `HH MM SS` (UTC) | Sincronizar reloj | Muy probable |
| `0B` | `01` | — | Se envía al conectar | Desconocido |
| `0B` | `0A` | `01` | Se envía al conectar | Desconocido |

En la app, la pestaña **"Temperatura de color"** tiene los cinco modos (`08/09`), el deslizador frío ↔ cálido (`08/07`) y el deslizador de 0 % a 100 % (`08/08`).

### Encender y apagar — `08/05`

| Acción | Trama |
| --- | --- |
| Apagar | `55AA01080500F2` |
| Encender | `55AA01080501F1` |

Al apagar con `08/05 00` la lámpara conserva el color y el brillo, y al encender vuelve al mismo estado.

### Brillo — `08/01`

| Valor | Trama |
| --- | --- |
| `00` (mínimo) | `55AA01080100F6` |
| `80` (50 %) | `55AA0108018076` |
| `FF` (máximo) | `55AA010801FFF7` |

- Es un brillo **global**: se aplica al color RGB, a la temperatura de blanco y a los modos.
- Cambiar el color, la temperatura o el modo no lo modifica.
- Se guarda al apagar y se puede cambiar con la lámpara apagada: al encenderla se usa el nuevo valor.
- No enciende la lámpara.

### Color RGB — `08/02`

`LEN = 03`, con un byte por canal.

| Color | Datos | Trama |
| --- | --- | --- |
| Rojo | `FF 00 00` | `55AA030802FF0000F4` |
| Verde | `00 FF 00` | `55AA03080200FF00F4` |
| Azul | `00 00 FF` | `55AA0308020000FFF4` |
| Blanco | `FF FF FF` | `55AA030802FFFFFFF6` |
| Naranja | `FF 80 00` | `55AA030802FF800074` |

- Enciende la lámpara si está apagada.
- Respeta el brillo de `08/01`.
- Sustituye el modo o la temperatura de blanco que hubiera.
- `00 00 00` **apaga la lámpara y borra el color**: un `08/05 01` posterior la enciende con el color por defecto, no con el anterior.

### Temperatura de blanco — `08/07`

| Valor | Trama |
| --- | --- |
| `00` (más frío) | `55AA01080700F0` |
| `7F` (intermedio) | `55AA0108077F71` |
| `FF` (más cálido) | `55AA010807FFF1` |

- Enciende la lámpara si está apagada.
- Respeta el brillo de `08/01`.
- Sustituye el color RGB.

### Brillo de la pestaña de temperatura — `08/08`

| Valor | Trama |
| --- | --- |
| `00` | `55AA01080800EF` |
| `FF` | `55AA010808FFF0` |

Comportamiento observado, todavía sin un modelo claro:

- Con un **modo** activo, cambia la intensidad igual que `08/01`.
- Con un **color RGB** activo, la lámpara pasa al blanco por defecto.
- Con una **temperatura** (`08/07`) activa, no se aprecia ningún cambio.
- Después de `08/01 FF` + `08/08 10`, tanto un color RGB como una temperatura se ven al máximo: el valor de `08/08` no se aplica a ellos.

Para controlar el brillo desde código, se recomienda `08/01`.

### Modos de ambiente — `08/09`

| Valor | Nombre en la app | Inglés | Trama |
| --- | --- | --- | --- |
| `01` | Blanco | White | `55AA01080901ED` |
| `02` | Moonlight | Moonlight | `55AA01080902EC` |
| `03` | Luz de sol | Sunlight | `55AA01080903EB` |
| `04` | Puesta de sol | Sunset | `55AA01080904EA` |
| `05` | Luz de vela | Candlelight | `55AA01080905E9` |

- `00` y `06` se ignoran. Los valores de `07` a `FF` no se han probado todavía.
- Enciende la lámpara si está apagada.
- Respeta el brillo de `08/01`.
- Un color RGB posterior quita el modo.

### Sincronizar reloj — `05/01`

| Acción | Cálculo | Trama |
| --- | --- | --- |
| Poner en hora 20:46:03 UTC | `03+05+01+14+2E+03 = 0x4E` → `0xB2` | `55AA030501142E03B2` |

## 4. Modelo de estado

Por lo observado, la lámpara se comporta como si tuviera dos grupos de LED, unos RGB y otros blancos (cálidos y fríos). La **última** orden de color, temperatura o modo decide qué se muestra, y el brillo global (`08/01`) se aplica encima de todo.

```
             ┌─ 08/02  color RGB ─────────┐
encendida ───┼─ 08/07  temperatura blanco ┼──× 08/01 brillo global ──> luz
             └─ 08/09  modo de ambiente ──┘
```

## 5. Secuencia observada de la app oficial

Al conectar, la app hace el descubrimiento de servicios y envía, en este orden:

1. `55AA000B01F4`
2. `55AA010B0A01E9`
3. `55AA000815E3`
4. Sincronización de hora (`CMD 05 / SUB 01`)

Después solo envía órdenes según lo que pulse el usuario. Al mover el deslizador de brillo manda una orden cada ~90 ms.

La secuencia inicial **no es obligatoria**: la lámpara obedece todas las órdenes anteriores aunque no se le envíe.

## 6. Pendiente

- [x] Confirmar encender/apagar y brillo
- [x] Color RGB (`08/02`) y temperatura de blanco (`08/07`)
- [x] Modos de ambiente (`08/09`)
- [ ] Aclarar el comportamiento de `08/08`
- [ ] Probar los valores `07`–`FF` de `08/09` (modos ocultos)
- [ ] Probar los subcomandos de `08` no observados (`00`, `03`, `04`, `06`, `0A`...)
- [ ] Significado de `0B/01`, `0B/0A` y `08/15`
- [ ] Formato de las notificaciones de A042/A043 y del valor de A041
- [x] Si la lámpara exige emparejamiento o cifrado de enlace (no: basta con conectar)
- [ ] Comprobar la sincronización de hora
- [x] Si la secuencia inicial es obligatoria (no lo es)

## 7. Notas de seguridad

- No hay cifrado ni autenticación en la capa de aplicación.
- No hay contador ni nonce: la misma acción genera siempre los mismos bytes, así que se pueden reenviar (*replay*).
- El checksum solo detecta errores de transmisión; no protege la integridad frente a un atacante.

Cualquier dispositivo que pueda conectarse por GATT a la lámpara puede controlarla.

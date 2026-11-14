# Protocolo BLE de la lámpara iLink

> **Estado:** encender, apagar y brillo están confirmados enviando las tramas desde un script propio. El resto se ha deducido de capturas y está marcado como tal.

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

| Trama (hex) | CMD | SUB | Datos | Acción | Estado |
| --- | --- | --- | --- | --- | --- |
| `55AA01080500F2` | `08` | `05` | `00` | Apagar | ✅ Confirmado |
| `55AA01080501F1` | `08` | `05` | `01` | Encender | ✅ Confirmado |
| `55AA010801` + valor + CHK | `08` | `01` | `00`–`FF` | Brillo (mínimo → máximo) | ✅ Confirmado |
| `55AA030501` + HH MM SS + CHK | `05` | `01` | hora, minuto, segundo (UTC) | Sincronizar reloj | Muy probable |
| `55AA000B01F4` | `0B` | `01` | — | Se envía al conectar; función desconocida | Desconocido |
| `55AA010B0A01E9` | `0B` | `0A` | `01` | Se envía al conectar; función desconocida | Desconocido |
| `55AA000815E3` | `08` | `15` | — | Se envía al conectar; función desconocida | Desconocido |

### Ejemplos

| Acción | Cálculo | Trama |
| --- | --- | --- |
| Brillo al 50 % (`0x80`) | `01+08+01+80 = 0x8A` → `0x100−0x8A = 0x76` | `55AA0108018076` |
| Brillo máximo (`0xFF`) | `01+08+01+FF = 0x109` → `0xF7` | `55AA010801FFF7` |
| Brillo mínimo (`0x00`) | `01+08+01+00 = 0x0A` → `0xF6` | `55AA01080100F6` |
| Poner en hora 20:46:03 | `03+05+01+14+2E+03 = 0x4E` → `0xB2` | `55AA030501142E03B2` |

## 4. Secuencia observada de la app oficial

Al conectar, la app hace el descubrimiento de servicios y envía, en este orden:

1. `55AA000B01F4`
2. `55AA010B0A01E9`
3. `55AA000815E3`
4. Sincronización de hora (`CMD 05 / SUB 01`)

Después solo envía órdenes según lo que pulse el usuario. Al mover el deslizador de brillo manda una orden cada ~90 ms.

La secuencia inicial **no es obligatoria**: la lámpara obedece encender, apagar y brillo aunque no se le envíe.

## 5. Pendiente

- [x] Confirmar encender/apagar y brillo
- [ ] Comandos de color (RGB) y temperatura de blanco
- [ ] Modos y efectos (por ejemplo, "luz de vela")
- [ ] Significado de `0B/01`, `0B/0A` y `08/15`
- [ ] Formato de las notificaciones de A042/A043 y del valor de A041
- [x] Si la lámpara exige emparejamiento o cifrado de enlace (no: basta con conectar)
- [ ] Comprobar la sincronización de hora
- [x] Si la secuencia inicial es obligatoria (no lo es)

## 6. Notas de seguridad

- No hay cifrado ni autenticación en la capa de aplicación.
- No hay contador ni nonce: la misma acción genera siempre los mismos bytes, así que se pueden reenviar (*replay*).
- El checksum solo detecta errores de transmisión; no protege la integridad frente a un atacante.

Cualquier dispositivo que pueda conectarse por GATT a la lámpara puede controlarla.

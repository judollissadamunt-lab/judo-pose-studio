# Revisión visual de Kumi-kata

Capturas de Chromium con cámaras equivalentes antes y después de la corrección.
Tori lleva judogi blanco y Uke azul. La vista frontal sigue el eje entre ambos;
la lateral permite ver los dos cuerpos de perfil.

| Vista | Antes | Después |
| --- | --- | --- |
| Frontal | ![Antes frontal](before/frontal.png) | ![Después frontal](after/frontal.png) |
| Lateral | ![Antes lateral](before/lateral.png) | ![Después lateral](after/lateral.png) |
| Superior | ![Antes superior](before/superior.png) | ![Después superior](after/superior.png) |

## Validación

Prueba funcional ejecutada en Chromium con Playwright, WebGL por software y
verificación TLS activada. Servidor: `python3 -m http.server 8000`.

- Carga del HTML y escena Three.js sin errores JavaScript.
- Cuatro palmas a menos de 5 mm de los puntos de agarre calculados.
- Derecha/izquierda anatómicas, codos de bisagra y muñecas neutras en la postura inicial.
- Edición de articulación y controles bloqueados para los ejes no válidos del codo.
- Animación de dos fases hasta el 100 %.
- Recuperación exacta de las rotaciones de una fase guardada.
- Exportación/importación JSON y recuperación de dos fases tras recargar.

Antes, la separación palma–destino era aproximadamente 13 cm en solapa y
25 cm en manga, tomando las unidades del modelo como metros.

## Limitaciones

Las manos son geometría simplificada sin cierre articulado de dedos. No hay un
sistema general de colisiones o de mantenimiento automático del contacto durante
la edición libre y las animaciones. Las fases antiguas pueden cambiar visualmente
por la corrección de lateralidad y la aplicación de límites articulares.

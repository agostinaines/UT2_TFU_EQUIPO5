# UT2_TFU_EQUIPO5

Este repositorio contiene una API que simula un sistema de administración de sensores. Estos generan registros en un log cada 10 segundos, con una probabilidad de dañarse del 1%. Los siguientes son todos los endpoints disponibles:
```
'/' -- WELCOME
'/register' -- REGISTRAR A UN NUEVO OPERADOR
'/login' -- INICIAR SESIÓN
'/allSensors' -- OBTENER TODOS LOS SENSORES
'/allLogs' -- OBTENER TODOS LOS REGISTROS
'/sensor/<id>/logs' -- OBTENER TODOS LOS REGISTROS DE UN SENSOR
'/newSensor' -- CREAR UN NUEVO SENSOR, POR DEFAULT DESACTIVADO
'/toggle/<id>' -- ACTIVAR O DESACTIVAR UN SENSOR
'/repairSensor/<id>' -- REPARAR SENSOR DAÑADO
'/updateSensor/<id>' -- EDITAR UN SENSOR
```
Los métodos automáticos que generan las lecturas de los sensores también determinan cuándo estos se dañan. Al momento de dañarse dejan de generar registros.

<H3>Cómo correr el proyecto</H3>
Luego de clonar el repositorio, nos moveremos a la carpeta ´src´

```
docker compose up --build
```
Una vez ejecutamos este código, podremos ver los registros en la terminal.
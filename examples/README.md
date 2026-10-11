# Escenarios de prueba

Estos archivos sirven para demostrar la validación de escenarios desde la
interfaz o con la API `POST /api/scenario/validate`.

## Escenarios válidos

Los archivos de `good/` deben ser aceptados con HTTP 200:

- `escenario_busqueda.json`: prueba de navegación con A*.
- `escenario_partida.json`: estado inicial para una partida por turnos.
- `escenario_adversarial.json`: estado preparado para Minimax y alfa-beta.

## Escenarios inválidos

Los archivos de `bad/` deben ser rechazados con HTTP 400. El nombre indica la
regla que se está demostrando:

- `dimensiones_inconsistentes.json`
- `terreno_desconocido.json`
- `posicion_fuera_del_mapa.json`
- `unidad_sobre_obstaculo.json`
- `base_sobre_obstaculo.json`
- `recurso_sobre_obstaculo.json`

Los escenarios válidos usan un mapa de 20 x 20, como exige la especificación.

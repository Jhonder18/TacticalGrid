# Escenarios de prueba

Estos archivos sirven para demostrar la validación de escenarios desde la
interfaz o con la API `POST /api/scenario/validate`.

## Escenarios válidos

Los archivos de `good/` deben ser aceptados con HTTP 200:

- `escenario_busqueda.json`: prueba de navegación con A*.
- `escenario_partida.json`: estado inicial para una partida por turnos.
- `escenario_adversarial.json`: estado preparado para Minimax y alfa-beta.
- `escenario_volcanico.json`: mapa de ceniza, lava y cráteres.
- `escenario_acuatico.json`: mapa de agua, orillas, puentes y rocas.
- `escenario_desertico.json`: mapa de arena, dunas, oasis y acantilados.

## Escenarios inválidos

Los archivos de `bad/` deben ser rechazados con HTTP 400. El nombre indica la
regla que se está demostrando:

- `dimensiones_inconsistentes.json`
- `terreno_desconocido.json`
- `posicion_fuera_del_mapa.json`
- `unidad_sobre_obstaculo.json`
- `base_sobre_obstaculo.json`
- `recurso_sobre_obstaculo.json`
- `portador_desincronizado.json`

Los ejemplos originales usan un mapa de 20 x 20. Los ejemplos temáticos
adicionales usan mapas de 10 x 10 para mostrar que la matriz y los terrenos
pueden variar mientras respeten el contrato y la validación.

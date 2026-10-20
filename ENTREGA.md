# Entrega final: TacticalGrid

Resumen de la entrega del proyecto. Reúne lo que incluye el repositorio, cómo
ejecutarlo y la evidencia de las tareas completadas.

## Qué es

Plataforma académica para ejecutar, observar y medir algoritmos de inteligencia
artificial sobre un tablero cuadriculado 2D: búsquedas (BFS, DFS, UCS, A*, Beam
Search), decisiones adversariales (Minimax y Alfa-Beta) y simulación de partidas
automáticas. Los algoritmos no contienen posiciones ni dimensiones codificadas:
todo se lee del JSON del escenario.

## Contenido del repositorio

- **Backend** (FastAPI): 8 endpoints, 7 algoritmos y verificación de resultados.
- **Frontend** (React + TypeScript + Vite): tablero dinámico, dashboard de
  métricas, árbol adversarial y reproducción de partidas.
- **Escenarios** (`examples/`): 11 casos demostrativos, escenarios temáticos,
  4 escenarios externos y 14 escenarios inválidos.
- **Reportes** (`examples/reportes/`): informe consolidado de los Casos 1 a 10 y
  reporte adversarial 6 a 10, reproducibles con scripts.
- **Pruebas**: 107 pruebas de backend en 12 archivos.
- **Documentación** (`docs/`): documento técnico, manual de usuario, heurísticas
  y utilidad, informe de resultados y prueba manual de la interfaz.

## Cómo ejecutar

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Pruebas

```powershell
python -m unittest discover -s backend/tests
```

```powershell
cd frontend
npm run lint
npm run build
```

## Documentación

- [Documento técnico](docs/documento_tecnico.md)
- [Manual de usuario](docs/manual_usuario.md)
- [Heurísticas y utilidad](docs/heuristicas_y_utilidad.md)
- [Informe de resultados: Casos 1 a 10](docs/informe_resultados_casos.md)
- [Prueba manual de la interfaz](docs/prueba_manual_interfaz.md)
- [Escenarios de prueba](examples/README.md)

## Evidencia de tareas

| Tarea | Descripción | Evidencia |
| --- | --- | --- |
| T-22 | Validación de escenarios externos | `examples/bad/`, `backend/models/scenario.py` |
| T-23 | Verificación de rutas y métricas | `backend/core/route_verification.py`, `backend/tests/test_route_verification.py` |
| T-24 | Comparación Minimax vs Alfa-Beta | `backend/core/adversarial_comparison.py`, `backend/tests/test_adversarial_comparison.py` |
| T-25 | Heurísticas y función de utilidad | `docs/heuristicas_y_utilidad.md`, `backend/tests/test_documentation_consistency.py` |
| T-26 | Informe de resultados Casos 1 a 10 | `docs/informe_resultados_casos.md`, `backend/scripts/generar_informe_casos.py` |
| T-27 | Compatibilidad con JSON externo | `examples/externo_*.json`, `backend/tests/test_external_scenario.py` |
| T-28 | Prueba manual completa de la interfaz | `docs/prueba_manual_interfaz.md` |
| T-29 | Documentación final y sustentación | `docs/documento_tecnico.md`, `docs/manual_usuario.md`, `README.md` |
| T-30 | Validación y entrega final | Este documento |

## Validación final

- Suite backend: **107 pruebas, todas OK** (también desde un clon limpio).
- Frontend: `npm run lint` y `npm run build` sin errores (incluye `tsc -b`).
- `git diff --check` limpio.
- Sin `venv`, `node_modules`, `__pycache__` ni `dist` versionados.
- Sin secretos en el repositorio.
- Escenarios públicos incluidos en `frontend/public/casos/`.

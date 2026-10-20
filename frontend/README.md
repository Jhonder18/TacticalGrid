# Frontend de TacticalGrid

Interfaz en React + TypeScript construida con Vite. Muestra el tablero, ejecuta
búsquedas y decisiones adversariales, y reproduce partidas automáticas
consumiendo la API del backend.

## Requisitos

- Node.js 18+

## Puesta en marcha

```powershell
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:5173`. Requiere el backend
en ejecución en `http://localhost:8000`.

## Estructura de `src/`

```text
src/
  App.tsx                 # Componente principal y flujo de la interfaz
  components/
    Grid.tsx              # Tablero dinámico
    ResultsDashboard.tsx  # Tabla de métricas de búsqueda
    AdversarialTree.tsx   # Árbol adversarial y nodos podados
    AdversarialComparison.tsx # Comparación Minimax vs Alfa-Beta
    ScenarioSummary.tsx   # Resumen del escenario
    terrainStyles.ts      # Colores por tipo de terreno
  services/api.ts         # Cliente HTTP de los endpoints
  hooks/                  # Hooks auxiliares (reservado)
  types/types.ts          # Tipos TypeScript del contrato
```

El flujo de uso se describe en [../docs/manual_usuario.md](../docs/manual_usuario.md).

## Scripts

```powershell
npm run dev            # Servidor de desarrollo
npm run build          # Compilación de producción
npm run preview        # Vista previa de la compilación
npm run lint           # ESLint
npm run lint:oxlint    # Oxlint
npm run format:check   # Verificación de formato
npm run format         # Aplicar formato
```

## Calidad de código

Antes de integrar cambios:

```powershell
npx tsc --noEmit
npx eslint --max-warnings=0 .
npx oxlint .
npx vite build
```

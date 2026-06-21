# Offer Helper Frontend

React + TypeScript + Vite frontend for the AI Offer Compensation Decision Engine.

## Features

- Offer recommendation workspace
- Data hub for organization, market salary, employee salary, and compensation strategy records
- Offer list and filtering board
- Model governance, rollback review, alert, and notification workflows
- Task console for market sync, model training, rollback, and governance jobs

## Local development

```powershell
pnpm install
pnpm dev --host 127.0.0.1 --port 5173
```

The dev server proxies `/api` to `http://127.0.0.1:8000` through `vite.config.ts`.

## Quality checks

```powershell
pnpm check
pnpm lint
pnpm test
pnpm build
```

## Runtime configuration

By default, browser requests use `/api/v1`, which works behind the included Nginx Docker image and with the Vite dev proxy.

To point the frontend to another API origin, set `VITE_API_BASE_URL` before building:

```powershell
$env:VITE_API_BASE_URL="https://your-api.example.com/api/v1"
pnpm build
```

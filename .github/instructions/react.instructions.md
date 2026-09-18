---
description: 'React frontend standards for CMPDI Intelligence: Vite, Tailwind, Motion, Lucide, receipt-linked evidence UI'
applyTo: 'frontend/src/**/*.{js,jsx,css}'
---

# React Frontend Development

React 18 SPA (Vite + React Router + Tailwind + `motion` + `lucide-react`), served as static `dist/` by the Flask backend. Paper/ink/amber palette, Archivo text, IBM Plex Mono numerals, light and dark themes via CSS variables.

## General Instructions

- Components own presentation only: no API clients, business rules, or large data transforms inside components. Put shared logic in `hooks/` or `api.js`.
- One component per screen under `src/pages/`; decompose large screens into focused children, never one enormous component.
- Every number, answer, and figure must link back to its source (`/doc/:id` viewer with page/sheet anchors). Reference/context values must be visually labeled as such — never presented as evidence.

## Best Practices

- Fetch through `getJSON`/`postJSON` from `src/api.js` (they throw on non-2xx, so use try/catch).
- Load screen data with `usePageData(url)` (`{data, error, reload}`); poll live endpoints with `usePolling(url, ms)`; sync URL filters with `useQueryParams()`.
- Wrap screens in `PageHeader`, `Rise`, `Loading`, `ErrorBox` from `components/ui.jsx`; always provide loading, empty, and error states.
- Canvas visuals must read colors from `cmpdiColors()` so they restyle instantly on theme flip.
- Store minimum state; derive the rest. No Redux or global stores.

## Code Standards

- Icons from `lucide-react`; animation from `motion/react`; conditional classes via `clsx`/`tailwind-merge`.
- Paginate or virtualize large datasets; aggregate on the backend; never send unused fields through the API.

## Validation

- Build: `npm run build` inside `frontend/` (Vite proxies the API to port 5000 in dev via `npm run dev`).
- Check the built screen in both themes and at mobile width before committing.

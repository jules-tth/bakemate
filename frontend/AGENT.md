# Frontend AGENT Guide

## Commands
- install: `npm install`
- lint: `npm run lint`
- test: `npm test`

## Tools & Libraries
- React + TypeScript via Vite
- Tailwind CSS for styling and layout
- Recharts for data visualization
- React Router for navigation
- Vitest + React Testing Library for unit tests
- TanStack Query for data fetching
- TanStack Table for tables and grouping
- react-hook-form + zod for forms and validation
- date-fns for date handling
- PapaParse for CSV export
- jsPDF + html2canvas for PDF export
- lucide-react for icons

## Style Standards
- **Colors**: use custom Tailwind theme tokens defined in `tailwind.config.js`
  - Brand: `brand.surface`, `brand.accent`, `brand.ink`
  - App surfaces: `app.bg`, `app.card`, `app.ring`, `app.text`, `app.muted`, `app.sidebar`, `app.sidebarHover`
  - Actions: `primary.DEFAULT`, `primary.hover`, `primary.foreground`
  - Charts: `chart.linePrimary`, `chart.lineSecondary`, `chart.fillFrom`, `chart.fillTo`, `chart.bar1`, `chart.bar2`, `chart.bar3`, `chart.grid`
  - Badges: `status.openBg`, `status.openFg`, `status.quotedBg`, `status.quotedFg`, `status.completedBg`, `status.completedFg`, `status.lateBg`, `status.lateFg`
- **Fonts**: Tailwind `font-sans` stack (Inter / system UI)
- Prefer a minimalist layout with generous whitespace and subtle shadows

## Page Guidelines
- Reuse existing card and chart components when possible.
- Keep components modular and colocate tests with source files.
- Ensure responsiveness: sidebar collapses on mobile; layouts adjust via Tailwind breakpoints.
- Run lint and tests before committing changes.
- Place new pages in `src/pages` and add matching links in the sidebar.


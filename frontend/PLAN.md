# Frontend Project Plan

This checklist tracks feature work needed to align the frontend with existing backend capabilities.

## API Layer
- [x] Expand `src/api` with typed client functions per endpoint group
- [x] Centralize error handling (401 redirects, toast notifications)

## Auth & User
- [x] Add user profile/settings page (`/users/me`)
- [x] Implement logout behavior
 - [x] Implement token refresh

## Feature Modules
 - [x] Recipes: CRUD forms and detail views
 - [x] Ingredients: list/edit/create with user association
 - [x] Orders & Quotes: list, detail, status updates, Stripe integration
- [x] Pricing: UI to calculate cost/price models
- [x] Calendar & Tasks: calendar view and task management
 - [x] Expenses, Mileage, Reports: finance and reporting dashboards
- [ ] Inventory: stock levels, adjustments, alerts
- [ ] Shop: public storefront and admin product management pages
- [ ] Marketing: campaign creation and metrics

## Routing & Navigation
- [ ] Extend sidebar navigation to cover new modules
- [ ] Ensure private routes guard authenticated areas

## State Management & UX
- [ ] Integrate React Query (or similar) for data fetching and caching
- [ ] Add loading/error states and basic form validation

## Testing & Tooling
- [x] Add unit tests for components (Jest/React Testing Library)
- [x] Add unit tests for API layer
- [x] Configure ESLint/formatter presets
 - [x] Plan for future Cypress end-to-end tests

## Documentation
- [ ] Update frontend README with setup commands and module structure
- [ ] Provide usage notes for each new feature

# Nexus Sandbox

## Overview
A complete educational sandbox implementation of the Nexus Global Payments scheme. This project demonstrates expertise in cross-border instant payments architecture, ISO 20022 message handling, and microservices.

**Source Repository**: https://github.com/siva-sub/nexus-sandbox

## Project Structure
- `services/demo-dashboard/` - React/Vite frontend dashboard (Mantine UI)
- `backend/` - Python FastAPI backend (Replit-native setup)
- `services/nexus-gateway/` - Python FastAPI backend gateway (Docker version)
- `services/fxp-simulator/` - FX Provider simulator
- `services/ips-simulator/` - Instant Payment System simulator
- `services/pdo-simulator/` - Payment Data Object simulator
- `services/psp-simulator/` - Payment Service Provider simulator
- `services/sap-simulator/` - SAP simulator
- `docs/` - Documentation and guides
- `migrations/` - Database migrations

## Running the Project
- Frontend: Port 5000 via Vite dev server
- Backend API: Port 8000 via Uvicorn
- Database: Replit Postgres (auto-configured via DATABASE_URL)

## Recent Changes
- 2026-02-05: Major UI overhaul with modern theme, gradients, and glassmorphism
- 2026-02-05: Enhanced Payment form with gradient cards, section headers, and metric displays
- 2026-02-05: Improved sidebar/header with gradient icons and glass effects
- 2026-02-05: Added fade/slide animations and quote card hover states
- 2026-02-05: Set up Replit Postgres database with auto-seeding
- 2026-02-05: Added centralized API error handling with retry logic (`apiClient.ts`)
- 2026-02-05: Created reusable Payment components (PaymentForm, QuoteSelector, LifecycleTracker)
- Updated vite.config.ts to use port 5000 and allow all hosts

## User Preferences
(None recorded yet)

## Tech Stack
- Frontend: React 19, Vite 7, TypeScript, Mantine UI
- Backend: Python FastAPI with SQLAlchemy (async)
- Database: PostgreSQL (Replit-hosted, Neon-backed)
- Testing: Playwright for E2E tests

## New Components (Ready for Integration)
- `src/components/Payment/PaymentForm.tsx` - Sender/recipient input form
- `src/components/Payment/QuoteSelector.tsx` - FX quote selection with PTD display
- `src/components/Payment/LifecycleTracker.tsx` - 17-step payment lifecycle visualization

## API Client Features
- `src/services/apiClient.ts` - Centralized error handling with:
  - Automatic retry with exponential backoff (3 retries)
  - 30-second timeout
  - Structured error types (ApiError)
  - Error formatting utilities

## UI Theme
- Professional color palette: sky (primary), emerald (success), amber (warning), slate (neutral)
- Clean, minimal card styling with subtle borders
- Solid accent colors instead of flashy gradients
- Fade animations for page transitions
- Quote card hover states with visual feedback
- Monospace font (JetBrains Mono) for code elements

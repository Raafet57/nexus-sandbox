# Nexus Sandbox

## Overview
A complete educational sandbox implementation of the Nexus Global Payments scheme. This project demonstrates expertise in cross-border instant payments architecture, ISO 20022 message handling, and microservices.

**Source Repository**: https://github.com/siva-sub/nexus-sandbox

## Project Structure
- `services/demo-dashboard/` - React/Vite frontend dashboard (Mantine UI)
- `services/nexus-gateway/` - Python FastAPI backend gateway
- `services/fxp-simulator/` - FX Provider simulator
- `services/ips-simulator/` - Instant Payment System simulator
- `services/pdo-simulator/` - Payment Data Object simulator
- `services/psp-simulator/` - Payment Service Provider simulator
- `services/sap-simulator/` - SAP simulator
- `docs/` - Documentation and guides
- `migrations/` - Database migrations

## Running the Project
The dashboard runs on port 5000 via Vite dev server.

## Recent Changes
- 2026-02-05: Pulled repository and configured for Replit environment
- Updated vite.config.ts to use port 5000 and allow all hosts

## User Preferences
(None recorded yet)

## Tech Stack
- Frontend: React 19, Vite 7, TypeScript, Mantine UI
- Backend: Python FastAPI (when running full stack via Docker)
- Testing: Playwright for E2E tests

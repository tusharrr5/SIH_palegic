# Validation record

Validated locally on 22 September 2026 with Node 22.22.2, Python 3.14.4, PostgreSQL/PostGIS, Next.js 15.5.25 and MapLibre GL JS 6.10.0.

- Production Next.js build and TypeScript checks passed.
- **33 Python tests passed**: anonymous/public/authority/admin boundaries; client role spoofing; CSRF Origin rejection; login throttle; HttpOnly/SameSite cookies; expiry; logout; revocation after role changes; optimistic review locking; both trigger paths and idempotency; recorded AIS import validation and absent-SAR cases; source hashes; gap-aware geodesic replay; circular course changes; ranking gates/coverage; particle displacement, units and repeatability.
- Added tests exercise admin-only account creation, case-insensitive duplicate emails, role spoofing rejection, password hashing, new-authority login and denied admin access; independent recorded replay, public denial, and exact report-to-source coordinate/time checks.
- Live preflight passed through the frontend gateway: database health, published archive, denied anonymous private access, documented admin authentication, source checksums, real AIS replay and local basemap.
- Browser walkthrough completed: public map, AIS-first creation, SAR-first creation, candidate rankings, animated replay, illustrative transport, persisted assessment, admin integrity/audit view. The recorded AIS library was checked for advancing timestamps, interpolated positions and a 79-minute interval with no vessel position; the new authority form was inspected. Account creation/sign-in/permissions are covered by isolated API integration tests.
- Desktop (1440×1000) and narrow (390×844) layout checks completed. An initial MapLibre CSS sizing conflict and mobile admin grid overflow were fixed and rechecked. The recorded replay navigation overflow on narrow screens was fixed and rechecked at 390×844. Final browser console check showed no errors.
- npm production dependency audit: **0 reported vulnerabilities** at validation time. The initial MapLibre and PostCSS advisories were addressed by upgrading MapLibre and overriding PostCSS to 8.5.28.
- Offline architecture checked: map geometry, coastlines, CSS, fonts (system fonts), MapLibre worker and scientific inputs are local. Source links and explicit refresh scripts are optional online actions. Initial dependency install requires network. The physical network adapter was not disabled during QA.

Two upstream test-library deprecation warnings (Starlette/httpx and AnyIO) are emitted; no test failures. Tests create and remove only their own temporary database schema.

These checks verify prototype behavior, not detection accuracy, legal attribution, or scientific hindcast validity. The dataset and method limitations remain as documented.

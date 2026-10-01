# Web App

The Web App sources are located in `packages/webapp`. Installations download and
serve pre-built static assets, so Node.js and local compilation are not
required on the target system.

## How installations get the Web App

The Web App is built into the `lauschkiste` wheel (`ci/build_wheels.sh`, run by the release
workflow), so package installations serve it from the package. A source checkout serves
`packages/webapp/build`: `install.sh --source` builds it with npm if available, else takes it from
the latest release wheel. The `Test Build Web App v3` workflow only checks the Web App (lint, unit
and browser tests); it publishes nothing.

## Develop the Web App

The Web App is a React application built with Vite. Use Node.js 22 and npm 10
or newer on a workstation or in the provided Docker environment:

```bash
cd ~/lauschkiste/packages/webapp
npm ci
npm run dev
```

The development server listens on port `3000` and proxies `/api/` to
`http://localhost:5556`. Set `API_PROXY_TARGET` to use another Lauschkiste API
server.

## Backend API

The Web App uses typed REST endpoints (`/api/v1/player/*`, `/api/v1/settings`,
`/api/v1/cards`, see `/docs` on the running server) for commands and
`WS /api/v1/events` for state updates. Both are served by FastAPI on the
configured API port, `5556`
by default -- the same server also serves the Web App's static build and
`/logs`, so everything is on one origin without a separate reverse proxy.
`GET /api/v1/health` reports API availability.

Library file management uses dedicated HTTP endpoints under
`/api/v1/library/`. Uploads send one raw file per
`PUT /api/v1/library/files` request, streamed directly to storage (via
Starlette's `request.stream()`) without buffering the complete file in
memory. Browser folder selections retain their relative paths; the Web App
creates the selected folder trees through the `folders` endpoint before
uploading their files sequentially. Raw directory listing, batch deletion,
and MPD refresh use the corresponding `entries` and `refresh` endpoints.
Uploads are exempt from the 1 MiB body-size cap that applies to RPC and other
JSON requests.

The old ZeroMQ-over-WebSocket endpoints on ports `5556` and `5557` were
intentionally removed early on. ZeroMQ itself is gone from the whole project now -- RPC, pub/sub,
and the C CLI client all moved to FastAPI/HTTP (see
`documentation/developers/roadmap-core-architecture.md`). There is no ZeroMQ-based client
compatibility anymore.

## Checks and production build

Run the same checks used by CI:

```bash
npm run lint
npm test
npx playwright install chromium
npm run test:e2e
npm run build
```

`npm run build` writes the production assets to `packages/webapp/build`. CI packages
that directory without source maps as the commit-addressed installation
bundle.

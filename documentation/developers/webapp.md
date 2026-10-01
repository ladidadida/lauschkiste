# Web App

The Web App sources are located in `packages/webapp`. Installations download and
serve pre-built static assets, so Node.js and local compilation are not
required on the target system.

## CI bundles

Every Web App bundle is addressed by its source commit:
`webapp-build-<first 10 commit characters>.tar.gz`. The installer accepts only
a bundle matching the checked-out commit. It checks the source repository and,
for forks, the upstream repository:

1. The `webapp-development` prerelease for development installs.
1. The release matching Lauschkiste version.

There is no fallback to a bundle from another commit. If no exact bundle is
available, publish or rerun the `Test Build Web App v3` workflow for that
commit, then rerun the installation. The legacy
`ENABLE_WEBAPP_PROD_DOWNLOAD=false` local-build mode is unsupported.

Pushes to any version 3 branch retain the exact bundle as a GitHub Actions
artifact for 14 days and publish it to the `webapp-development` prerelease.
Branch names are unrestricted: branches created from version 3 inherit this
workflow, while incompatible legacy branches do not contain it. The workflow
can also be run manually for a selected branch. Pull request workflows remain
read-only and do not publish bundles.

For a fork:

1. Open the fork's **Actions** tab and enable workflows. If GitHub lists
   `Test Build Web App v3` as disabled, enable that workflow as well. If the
   workflow is not listed, set the fork's default branch to `future3/develop`.
1. Under **Settings > Actions > General > Workflow permissions**, select
   **Read and write permissions** so the workflow can publish the bundle.
1. Push the commit to a branch with any name, or select that branch when
   starting `Test Build Web App v3` manually.
1. Wait for the workflow to complete before running the installer.

### Download a CI bundle manually

Signed-in developers can download a retained workflow artifact with the GitHub
CLI:

```bash
gh run download RUN_ID \
  --repo OWNER/lauschkiste \
  --name webapp-build-0123456789.tar.gz
```

GitHub Actions artifacts require authentication. The installer uses public
release or prerelease assets.

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

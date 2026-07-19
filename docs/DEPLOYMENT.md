# Deployment

PhysicsForge runs as FastAPI, a static React site, and PostgreSQL 15 or newer.
Use managed PostgreSQL in production and terminate TLS at the load balancer.

## Configuration

The API requires `DATABASE_URL` with the `postgresql+asyncpg://` scheme. Set
`OPENAI_API_KEY` for model generation. Optional variables are in `.env.example`.
Keep all secrets on the API; none belong in the frontend build or browser.

The frontend calls same-origin `/api/v1`. Its Nginx image proxies `/api/*` to
the API service, disables response buffering for server-sent events, and falls
back to `index.html` for React routes. Configure an external ingress with the
same routing if the images do not share a network. This avoids production CORS
issues and keeps server-sent events same-origin.

## Build and release

```bash
docker build -t registry.example/physicsforge-api:$GIT_SHA .
docker build -t registry.example/physicsforge-web:$GIT_SHA frontend
docker push registry.example/physicsforge-api:$GIT_SHA
docker push registry.example/physicsforge-web:$GIT_SHA
```

The API image migrates the database before starting. With multiple replicas,
run `alembic upgrade head` once as a release job and override the container
command to start Uvicorn directly. Never release the API before migration
success. Expose API port `8000` (or `PORT`) and frontend port `3000`.

- API liveness: `GET /api/v1/health`
- API readiness: `GET /api/v1/ready`
- Frontend liveness: `GET /`

Start with one API replica. Generation runs in the application process, so test
graceful shutdown and scaling before aggressive autoscaling. Back up PostgreSQL
and test restoration before launch.

## Local production image

```bash
docker build -t physicsforge-web frontend
docker run --rm -p 3000:3000 --add-host api:host-gateway physicsforge-web
```

The standalone command requires an API listening on the host at port `8000`.
`docker compose up --build` supplies the service network automatically and
remains the recommended full local workflow.

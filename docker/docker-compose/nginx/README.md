# Nginx Reverse Proxy with Custom Base Path

Deploy Entelechy API under `/entelechy` (or any custom path) using Nginx reverse proxy.

## Quick Start (Published Image - API Only)

```bash
docker-compose up
```

- **API:** http://localhost:8080/entelechy/docs
- **Control Plane:** http://localhost:9999 (direct access, not proxied)

## Full Stack with Custom Base Path (Requires Build)

**Important:** You cannot rebuild from the published image with build args. You must build from source.

### Build from Source with Custom Base Path

1. **Clone the repository** (if you haven't):
```bash
git clone https://github.com/garybense/entelechy.git
cd entelechy
```

2. **Build with base path**:
```bash
docker build \
  --build-arg NEXT_PUBLIC_BASE_PATH=/entelechy \
  -f docker/standalone/Dockerfile \
  -t entelechy:custom \
  .
```

3. **Update docker-compose.yml** to use your built image:
```yaml
services:
  entelechy:
    image: entelechy:custom  # ← Change this
    environment:
      ENTELECHY_API_BASE_PATH: /entelechy
      NEXT_PUBLIC_BASE_PATH: /entelechy
```

4. **Update nginx.conf** to handle Control Plane routes (see below)

5. **Run**:
```bash
docker-compose up
```

### Required nginx.conf for Full Stack

Replace the current `nginx.conf` with this to proxy both API and Control Plane:

```nginx
events { worker_connections 1024; }

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream entelechy_api { server entelechy:8888; }
    upstream entelechy_cp { server entelechy:9999; }

    server {
        listen 80;

        # API
        location ~ ^/entelechy/(docs|openapi\.json|health|metrics|v1|mcp) {
            proxy_pass http://entelechy_api;
            proxy_set_header Host $http_host;
        }

        # Control Plane static files
        location ~ ^/entelechy/_next/ {
            proxy_pass http://entelechy_cp;
            proxy_set_header Host $http_host;
        }

        # Control Plane UI
        location /entelechy {
            proxy_pass http://entelechy_cp;
            proxy_set_header Host $http_host;
        }

        location = / { return 301 /entelechy; }
    }
}
```

### Why Build is Required

Next.js requires `basePath` at **build time**. The published image was built without a custom base path, so you must rebuild from source with the `NEXT_PUBLIC_BASE_PATH` build arg to deploy the Control Plane under a subpath.

The API works without rebuild because `ENTELECHY_API_BASE_PATH` is a runtime environment variable.

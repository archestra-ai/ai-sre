# AI SRE Demo Application

A simple Todo CRUD API built with Flask and PostgreSQL, designed for demonstrating AI SRE capabilities including:

- **Observability**: Monitored via Grafana Cloud
- **GitOps**: Deployed via Argo CD
- **Failure Simulation**: Endpoints to trigger and remediate failures
- **Database Operations**: Full CRUD against PostgreSQL

## API Endpoints

### Todo CRUD

| Method | Endpoint      | Description         |
| ------ | ------------- | ------------------- |
| GET    | `/todos`      | List all todos      |
| POST   | `/todos`      | Create a new todo   |
| GET    | `/todos/<id>` | Get a specific todo |
| PUT    | `/todos/<id>` | Update a todo       |
| DELETE | `/todos/<id>` | Delete a todo       |

### Health & Status

| Method | Endpoint  | Description                       |
| ------ | --------- | --------------------------------- |
| GET    | `/`       | Service info and status           |
| GET    | `/health` | Health check (used by K8s probes) |

### Failure Simulation

| Method | Endpoint           | Description               |
| ------ | ------------------ | ------------------------- |
| POST   | `/trigger-failure` | Put app in failure mode   |
| POST   | `/remediate`       | Reset failure state       |
| POST   | `/crash`           | Immediately crash the app |

## Example Usage

```bash
# Create a todo
curl -X POST http://localhost:8080/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn AI SRE", "description": "Demo the AI SRE capabilities"}'

# List all todos
curl http://localhost:8080/todos

# Update a todo
curl -X PUT http://localhost:8080/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete a todo
curl -X DELETE http://localhost:8080/todos/1
```

## Environment Variables

| Variable            | Description                                    | Default           |
| ------------------- | ---------------------------------------------- | ----------------- |
| `PORT`              | HTTP server port                               | `8080`            |
| `FORCE_HEALTHY`     | Force healthy status (overrides failure state) | `false`           |
| `INJECT_FAILURE`    | Start app in failure mode (health checks fail) | `false`           |
| `DATABASE_HOST`     | PostgreSQL host                                | `ai-sre-postgres` |
| `DATABASE_PORT`     | PostgreSQL port                                | `5432`            |
| `DATABASE_NAME`     | Database name                                  | `todos`           |
| `DATABASE_USER`     | Database user                                  | `postgres`        |
| `DATABASE_PASSWORD` | Database password                              | `postgres`        |

### Failure Control via Environment Variables

- **`INJECT_FAILURE=true`**: The application starts healthy, then **after 60-90 seconds (random delay)** begins failing health checks. This delay allows Kubernetes to complete the rollout before the failure kicks in, simulating a realistic "bad deployment" scenario where the app passes initial checks but fails later.

- **`FORCE_HEALTHY=true`**: Forces health checks to pass regardless of failure state. Use this to remediate a broken deployment without restarting the app.

## Deployment

This application is deployed via **Argo CD** from the `k8s/` directory.

### Docker Build

Use the Makefile to build and push the Docker image (builds for `linux/amd64` for GKE compatibility):

```bash
# Build only
make build

# Push only
make push

# Build and push in one step
make build-push

# Show all available commands
make help
```

## Demo Flow

1. **Normal Operation**: App serves todo CRUD, health checks pass
2. **Trigger Failure**: `POST /trigger-failure` causes health checks to fail
3. **Observe**: Grafana alerts fire, notifications sent to MS Teams via OnCall
4. **Remediate**: Set `FORCE_HEALTHY=true` in ConfigMap or `POST /remediate`

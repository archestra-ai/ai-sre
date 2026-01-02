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

| Variable               | Description                                    | Default           |
| ---------------------- | ---------------------------------------------- | ----------------- |
| `PORT`                 | HTTP server port                               | `8080`            |
| `FORCE_HEALTHY`        | Force healthy status (overrides failure state) | `false`           |
| `ENABLE_BUGGY_FEATURE` | Enable buggy code that crashes app on startup  | `false`           |
| `DATABASE_HOST`        | PostgreSQL host                                | `ai-sre-postgres` |
| `DATABASE_PORT`        | PostgreSQL port                                | `5432`            |
| `DATABASE_NAME`        | Database name                                  | `todos`           |
| `DATABASE_USER`        | Database user                                  | `postgres`        |
| `DATABASE_PASSWORD`    | Database password                              | `postgres`        |

### Failure Simulation for AI SRE Demo

- **`ENABLE_BUGGY_FEATURE=true`**: Loads `buggy_feature.py` which contains an intentional bug. The app crashes **immediately on startup** with an `AttributeError`, causing Kubernetes to enter CrashLoopBackOff. This simulates a "bad deployment" scenario.

  **To remediate**: An AI agent must:

  1. Investigate logs to find the error (`AttributeError: 'NoneType' object has no attribute 'upper'`)
  2. Locate `buggy_feature.py` in the repository
  3. Fix the bug (initialize `data` variable properly)
  4. Push the fix to trigger ArgoCD deployment

- **`FORCE_HEALTHY=true`**: Forces health checks to pass regardless of failure state. Use for manual remediation.

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

### Option A: API-triggered failure (quick demo)

1. **Normal Operation**: App serves todo CRUD, health checks pass
2. **Trigger Failure**: `POST /trigger-failure` causes health checks to fail
3. **Observe**: Grafana alerts fire, notifications sent to MS Teams via OnCall
4. **Remediate**: `POST /remediate` or set `FORCE_HEALTHY=true` in ConfigMap

### Option B: Code-based failure (AI SRE demo)

1. **Normal Operation**: App is running healthy
2. **Trigger Failure**: Set `ENABLE_BUGGY_FEATURE=true` in ConfigMap, ArgoCD syncs
3. **App Crashes**: Pod enters CrashLoopBackOff due to bug in `buggy_feature.py`
4. **Observe**: Grafana alerts fire, AI agent receives alert
5. **AI Investigation**: Agent uses MCP tools to check logs, find error, locate code
6. **AI Fix**: Agent fixes bug in `buggy_feature.py`, pushes commit to repo
7. **ArgoCD Deploy**: ArgoCD detects change, deploys fixed code
8. **Recovery**: App starts successfully, alerts resolve

# AI SRE Demo Application

A simple Flask application designed for demonstrating AI SRE (Site Reliability Engineering) capabilities.

## Overview

This application can be triggered to fail, allowing testing of:
1. Grafana alerting and incident detection
2. Notifications via Microsoft Teams (Grafana OnCall)
3. Automated remediation workflows

## Repository Structure

```
ai-sre/
├── app/                    # Application source code
│   ├── main.py            # Flask application
│   ├── Dockerfile         # Container image definition
│   └── requirements.txt   # Python dependencies
├── k8s/                   # Kubernetes manifests (used by Argo CD)
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
```

## Deployment

This application is deployed via **Argo CD** using GitOps. Any changes pushed to the `main` branch will automatically trigger a deployment.

### Manual Docker Build

```bash
cd app

# Build for amd64 (GKE)
docker build --platform linux/amd64 -t europe-west1-docker.pkg.dev/friendly-path-465518-r6/archestra-public/ai_sre_demo:latest .

# Push to Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker push europe-west1-docker.pkg.dev/friendly-path-465518-r6/archestra-public/ai_sre_demo:latest
```

## API Endpoints

| Endpoint           | Method | Description                                              |
| ------------------ | ------ | -------------------------------------------------------- |
| `/`                | GET    | Returns application info and current status              |
| `/health`          | GET    | Health check endpoint (used by K8s liveness probe)       |
| `/trigger-failure` | POST   | Triggers failure mode - health checks will start failing |
| `/remediate`       | POST   | Clears failure state - application becomes healthy again |
| `/crash`           | POST   | Immediately crashes the application                      |

## Environment Variables

| Variable        | Default | Description                                                          |
| --------------- | ------- | -------------------------------------------------------------------- |
| `PORT`          | `8080`  | Port the application listens on                                      |
| `FORCE_HEALTHY` | `false` | When set to `true`, bypasses failure mode and always returns healthy |

## Remediation

When the AI SRE Agent needs to remediate a failing application:

```bash
# Option 1: Patch ConfigMap to force healthy state
kubectl patch configmap ai-sre-demo-config -n ai-sre \
  --type merge -p '{"data":{"FORCE_HEALTHY":"true"}}'

# Option 2: Restart deployment
kubectl rollout restart deployment/ai-sre-demo -n ai-sre
```

## Demo Flow

```
1. Application running normally → /health returns 200
2. POST /trigger-failure → /health starts returning 500
3. Kubernetes detects failed liveness probes → Pod restarts → CrashLoopBackOff
4. Grafana alert fires → OnCall creates alert group → MS Teams notification
5. AI Agent remediates by patching ConfigMap → FORCE_HEALTHY=true
6. New pod starts healthy → Alert resolves
```

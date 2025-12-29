"""
AI SRE Demo Application

A simple Flask application that can be triggered to fail for demonstrating
AI SRE capabilities. The application supports:
- Health checks that can be made to fail
- Triggering failure mode via API
- Remediation via environment variable or API
"""

import os
import sys
import logging
from flask import Flask, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Internal state for failure simulation
_failure_triggered = False


def is_healthy() -> bool:
    """
    Determine if the application should report as healthy.
    
    Returns True if:
    - FORCE_HEALTHY environment variable is set to "true" (case-insensitive)
    - OR failure has not been triggered
    """
    force_healthy = os.environ.get("FORCE_HEALTHY", "false").lower() == "true"
    if force_healthy:
        return True
    return not _failure_triggered


@app.route("/", methods=["GET"])
def index():
    """Basic info endpoint."""
    return jsonify({
        "service": "ai-sre-demo",
        "description": "Demo application for AI SRE demonstrations",
        "endpoints": {
            "/": "This info endpoint",
            "/health": "Health check endpoint",
            "/trigger-failure": "POST to trigger failure mode",
            "/remediate": "POST to reset failure state"
        },
        "status": "healthy" if is_healthy() else "unhealthy",
        "force_healthy": os.environ.get("FORCE_HEALTHY", "false")
    })


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    
    Returns 200 if healthy, 500 if in failure mode.
    Used by Kubernetes liveness probe.
    """
    if is_healthy():
        logger.info("Health check: OK")
        return jsonify({"status": "healthy"}), 200
    else:
        logger.warning("Health check: FAILING - failure mode is active")
        return jsonify({
            "status": "unhealthy",
            "reason": "Failure mode triggered. Set FORCE_HEALTHY=true or POST /remediate to recover."
        }), 500


@app.route("/trigger-failure", methods=["POST"])
def trigger_failure():
    """
    Trigger failure mode.
    
    After calling this endpoint:
    - Health checks will return 500
    - The application will crash after a few failed health checks
    - Kubernetes will restart the pod, eventually causing CrashLoopBackOff
    """
    global _failure_triggered
    _failure_triggered = True
    logger.error("FAILURE TRIGGERED - Application will start failing health checks")
    return jsonify({
        "status": "failure_triggered",
        "message": "Application is now in failure mode. Health checks will fail.",
        "remediation": "Set FORCE_HEALTHY=true in ConfigMap or POST /remediate"
    }), 200


@app.route("/remediate", methods=["POST"])
def remediate():
    """
    Reset failure state.
    
    This clears the internal failure flag, allowing health checks to pass again.
    Note: If FORCE_HEALTHY is set to true, health checks pass regardless.
    """
    global _failure_triggered
    _failure_triggered = False
    logger.info("REMEDIATION APPLIED - Failure state cleared")
    return jsonify({
        "status": "remediated",
        "message": "Failure state has been cleared. Application should now be healthy."
    }), 200


@app.route("/crash", methods=["POST"])
def crash():
    """
    Immediately crash the application.
    
    This is an alternative to trigger-failure that causes an immediate exit
    rather than waiting for health check failures.
    """
    logger.critical("CRASH REQUESTED - Exiting with code 1")
    sys.exit(1)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting AI SRE Demo application on port {port}")
    logger.info(f"FORCE_HEALTHY={os.environ.get('FORCE_HEALTHY', 'false')}")
    app.run(host="0.0.0.0", port=port)

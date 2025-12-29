"""
AI SRE Demo Application - Todo CRUD API

A Flask application with PostgreSQL backend that demonstrates:
- Todo CRUD operations against PostgreSQL
- Health checks that can be triggered to fail
- Failure simulation for AI SRE demonstrations
"""

import os
import sys
import logging
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Internal state for failure simulation
_failure_triggered = False


def get_db_connection():
    """Get a database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", "ai-sre-postgres"),
        port=os.environ.get("DATABASE_PORT", "5432"),
        dbname=os.environ.get("DATABASE_NAME", "todos"),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        cursor_factory=RealDictCursor
    )


def init_db():
    """Initialize the database schema."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database schema initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


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


# =============================================================================
# Info and Health Endpoints
# =============================================================================

@app.route("/", methods=["GET"])
def index():
    """Basic info endpoint."""
    return jsonify({
        "service": "ai-sre-demo",
        "description": "Todo CRUD API for AI SRE demonstrations",
        "endpoints": {
            "/": "This info endpoint",
            "/health": "Health check endpoint",
            "/todos": "GET all todos, POST to create a todo",
            "/todos/<id>": "GET, PUT, DELETE a specific todo",
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
        # Also check database connectivity
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            logger.info("Health check: OK (DB connected)")
            return jsonify({"status": "healthy", "database": "connected"}), 200
        except Exception as e:
            logger.warning(f"Health check: DB connection failed: {e}")
            return jsonify({
                "status": "degraded",
                "database": "disconnected",
                "error": str(e)
            }), 200  # Still return 200, app is healthy but DB may be starting
    else:
        logger.warning("Health check: FAILING - failure mode is active")
        return jsonify({
            "status": "unhealthy",
            "reason": "Failure mode triggered. Set FORCE_HEALTHY=true or POST /remediate to recover."
        }), 500


# =============================================================================
# Todo CRUD Endpoints
# =============================================================================

@app.route("/todos", methods=["GET"])
def get_todos():
    """Get all todos."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM todos ORDER BY created_at DESC")
        todos = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"todos": [dict(t) for t in todos]}), 200
    except Exception as e:
        logger.error(f"Failed to get todos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/todos", methods=["POST"])
def create_todo():
    """Create a new todo."""
    try:
        data = request.get_json()
        if not data or "title" not in data:
            return jsonify({"error": "Title is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO todos (title, description, completed)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (data["title"], data.get("description", ""), data.get("completed", False))
        )
        todo = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Created todo: {todo['id']}")
        return jsonify({"todo": dict(todo)}), 201
    except Exception as e:
        logger.error(f"Failed to create todo: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    """Get a specific todo by ID."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
        todo = cur.fetchone()
        cur.close()
        conn.close()

        if todo is None:
            return jsonify({"error": "Todo not found"}), 404

        return jsonify({"todo": dict(todo)}), 200
    except Exception as e:
        logger.error(f"Failed to get todo {todo_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """Update a todo by ID."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Build dynamic update query
        updates = []
        values = []
        if "title" in data:
            updates.append("title = %s")
            values.append(data["title"])
        if "description" in data:
            updates.append("description = %s")
            values.append(data["description"])
        if "completed" in data:
            updates.append("completed = %s")
            values.append(data["completed"])

        if not updates:
            return jsonify({"error": "No fields to update"}), 400

        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(todo_id)

        query = f"UPDATE todos SET {', '.join(updates)} WHERE id = %s RETURNING *"
        cur.execute(query, values)
        todo = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if todo is None:
            return jsonify({"error": "Todo not found"}), 404

        logger.info(f"Updated todo: {todo_id}")
        return jsonify({"todo": dict(todo)}), 200
    except Exception as e:
        logger.error(f"Failed to update todo {todo_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """Delete a todo by ID."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM todos WHERE id = %s RETURNING id", (todo_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if deleted is None:
            return jsonify({"error": "Todo not found"}), 404

        logger.info(f"Deleted todo: {todo_id}")
        return jsonify({"message": "Todo deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to delete todo {todo_id}: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================================
# Failure Simulation Endpoints
# =============================================================================

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


# =============================================================================
# Application Startup
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting AI SRE Demo application on port {port}")
    logger.info(f"FORCE_HEALTHY={os.environ.get('FORCE_HEALTHY', 'false')}")

    # Initialize database on startup
    init_db()

    app.run(host="0.0.0.0", port=port)

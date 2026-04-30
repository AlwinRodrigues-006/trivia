"""
Trivia Application - Packaged Entry Point.

Handles optional database creation / seeding, then starts the Flask server.
Designed to be bundled into a single executable with PyInstaller.

Usage
-----
First-time install (create DB + seed + run server):
    ./trivia --setup-db --db-password YOUR_PASSWORD

Subsequent runs (DB already exists):
    ./trivia --db-password YOUR_PASSWORD

For help:
    ./trivia --help
"""

import os
import sys
import argparse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_resource_path(relative_path: str) -> str:
    """Return the absolute path to a bundled resource.

    Works both when running from source and from a PyInstaller bundle
    (where resources are extracted to sys._MEIPASS at runtime).
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, relative_path)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Trivia API Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  First-time setup (create DB and start server):
    trivia --setup-db --db-password secret

  Start server only (DB already set up):
    trivia --db-password secret

  Custom host / port:
    trivia --setup-db --db-host 192.168.1.10 --db-port 5433 --db-password secret --port 8080
        """,
    )
    parser.add_argument("--db-host",     default="localhost", metavar="HOST",
                        help="PostgreSQL host (default: localhost)")
    parser.add_argument("--db-port",     default="5432",      metavar="PORT",
                        help="PostgreSQL port (default: 5432)")
    parser.add_argument("--db-user",     default="postgres",  metavar="USER",
                        help="PostgreSQL user (default: postgres)")
    parser.add_argument("--db-password", default="",          metavar="PASS",
                        help="PostgreSQL password")
    parser.add_argument("--db-name",     default="trivia",    metavar="NAME",
                        help="Database name (default: trivia)")
    parser.add_argument("--port",        default=5000,        type=int,
                        help="HTTP port the server listens on (default: 5000)")
    parser.add_argument("--setup-db",    action="store_true",
                        help="Create the database and load seed data before starting")
    return parser


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def setup_database(host: str, port: str, user: str, password: str, db_name: str) -> None:
    """Create the database (if absent) and execute the seed SQL script."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("ERROR: psycopg2 is not installed. Cannot set up the database.")
        sys.exit(1)

    print(f"Connecting to PostgreSQL at {host}:{port} as '{user}'...")
    try:
        # Connect to the built-in 'postgres' database so we can create ours
        admin_conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database="postgres",
            connect_timeout=10,
        )
    except psycopg2.OperationalError as exc:
        print(f"\nERROR: Could not connect to PostgreSQL.\n  {exc}")
        print("Make sure PostgreSQL is running and the credentials are correct.")
        sys.exit(1)

    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    admin_cur = admin_conn.cursor()

    # Create the target database if it does not already exist
    admin_cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if admin_cur.fetchone():
        print(f"Database '{db_name}' already exists — re-seeding data...")
    else:
        admin_cur.execute(f'CREATE DATABASE "{db_name}"')
        print(f"Database '{db_name}' created.")

    admin_cur.close()
    admin_conn.close()

    # Connect to our target database and execute the seed script
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=db_name,
    )
    conn.autocommit = True
    cursor = conn.cursor()

    sql_path = get_resource_path("trivia.psql")
    with open(sql_path, "r", encoding="utf-8") as fh:
        raw_sql = fh.read()

    # Execute each statement individually (psycopg2 does not support
    # multi-statement strings in a single cursor.execute() call).
    for stmt in raw_sql.split(";"):
        stmt = stmt.strip()
        # Skip empty chunks and pure comment blocks
        non_comment_lines = [
            ln for ln in stmt.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if non_comment_lines:
            cursor.execute(stmt)

    cursor.close()
    conn.close()
    print("Schema and seed data loaded successfully.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_arg_parser().parse_args()

    # Set environment variables BEFORE importing models.py, which reads them
    # at module-import time (via os.environ.get).  python-dotenv will NOT
    # overwrite values that are already present in the process environment.
    os.environ["DB_HOST"]     = f"{args.db_host}:{args.db_port}"
    os.environ["DB_NAME"]     = args.db_name
    os.environ["DB_USER"]     = args.db_user
    os.environ["DB_PASSWORD"] = args.db_password

    if args.setup_db:
        setup_database(
            args.db_host,
            args.db_port,
            args.db_user,
            args.db_password,
            args.db_name,
        )

    # Import the Flask factory now so models.py picks up our env vars above
    from app import create_app  # noqa: E402

    flask_app = create_app()

    # If the React build directory exists (bundled or built locally), serve it
    static_dir = get_resource_path("build")
    if os.path.isdir(static_dir):
        from flask import send_from_directory  # noqa: E402

        @flask_app.route("/", defaults={"path": ""})
        @flask_app.route("/<path:path>")
        def serve_frontend(path):  # type: ignore[return]
            target = os.path.join(static_dir, path)
            if path and os.path.isfile(target):
                return send_from_directory(static_dir, path)
            return send_from_directory(static_dir, "index.html")

        print(f"Frontend: http://localhost:{args.port}/")

    print(f"API:      http://localhost:{args.port}/questions")
    print("Press Ctrl+C to stop.\n")

    flask_app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()

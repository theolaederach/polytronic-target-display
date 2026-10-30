# Agent Guide

## Project shape

- `main.py` is the launcher. It loads `.env`, starts the TCP listener in a daemon thread, and starts the Flask server.
- `listener.py` parses semicolon-delimited target packets and dispatches them to `database.writer.InitTarget`.
- `server/app.py` creates the Flask app and registers the API and HTML route blueprints.
- `server/api/shots.py` exposes `GET /api/shots?target=N`; the public target number is 1-based and is converted to the zero-based target list index.
- `server/routes/app_routes.py` serves Jinja templates from `server/templates/`; browser assets live under `server/static/`.
- `database/connection.py`, `reader.py`, and `writer.py` contain MariaDB access and current-target state. The schema is `database/src/create structure.sql`.

## Setup and commands

Use Python 3.11+ and install dependencies with `pip install -r requirements.txt`. On Windows, activate `.venv\\Scripts\\activate` first.

- Run the application: `python main.py`
- Run without starting the TCP accept loop: `python main.py --web_server_only`
- Check Python syntax without connecting to MariaDB: `python -m compileall main.py listener.py server database`

The application still imports `listener.py` in web-only mode, and that module initializes target state through the database layer. A working `.env` and reachable MariaDB database are therefore required for normal startup. Required settings are documented in `.env.example` and [README.md](README.md).

There is currently no automated test suite. For route or frontend changes, use the running Flask app and verify the affected URL and browser polling behavior.

## Change guidance

- Preserve the packet field positions and target numbering conventions in `listener.py` and `server/api/shots.py`; changes can silently corrupt target routing or shot data.
- Keep SQL parameterized through the existing database helpers. Do not put credentials in source files or commit `.env`.
- Keep Flask route/template relationships consistent: templates use `url_for('static', filename=...)` for assets.
- Preserve the existing Python and vanilla JavaScript style unless a change requires a broader refactor. Keep public function names and API response fields stable.
- Make database schema changes in `database/src/create structure.sql` and update related reader/writer code together.
- Prefer focused validation with `compileall` for Python-only edits, then manually exercise the relevant endpoint or page when database/browser behavior is involved.

For fuller setup, data-flow, and extension notes, see [README.md](README.md) and [doc.md](doc.md). Treat those documents as supplementary: verify paths and commands against the current tree before relying on them.

# Project Documentation

This document provides a comprehensive guide to the **polytronic‑target‑display** project. It covers the overall architecture, directory layout, technology choices, data flow, API usage, key classes/functions, and how to run and extend the application.

---

## 1. Project Overview

The application visualises live target‑shooting data received over a TCP socket. Data packets are parsed, persisted in a MariaDB database, and then served to a lightweight front‑end via a Flask REST API. The front‑end displays SVG targets and updates them in real time using JavaScript.

- **Goal** – Show shot trajectories on multiple targets in a browser.
- **Language** – Python 3.11 (Flask) on the back‑end; vanilla JavaScript (ES6) on the front‑end.
- **DB** – MariaDB, accessed through the `mariadb` driver.

---

## 2. Architecture & File Hierarchy

```
polytronic-target-display/                 # Project root
├─ main.py                    # Entry point – starts Flask and the TCP listener
├─ listener.py                # TCP listener and semicolon-delimited packet parser
├─ database/                  # Data‑layer package
│  ├─ connection.py           # MariaDB connections and parameterized queries
│  ├─ reader.py               # Database read helpers for the API
│  ├─ writer.py               # InitTarget state manager and write helpers
│  └─ src/
│     └─ create structure.sql  # MariaDB schema
├─ server/                    # Flask application and browser interface
│  ├─ app.py                  # Flask app and blueprint registration
│  ├─ api/
│  │  └─ shots.py             # GET /api/shots endpoint
│  ├─ routes/
│  │  └─ app_routes.py        # HTML page routes
│  ├─ static/                 # Browser assets served by Flask
│  │  ├─ assets/              # Target images
│  │  ├─ js/
│  │  │  └─ update-target.js  # Polls the API and draws SVG crosshairs
│  │  ├─ favicon.ico
│  │  ├─ fullscreen.css
│  │  └─ style.css
│  └─ templates/              # Jinja2 templates
│     ├─ home.html
│     ├─ target.html
│     ├─ target_fs.html
│     └─ credits.html
├─ requirements.txt           # Python dependencies
├─ .gitignore                 # Git ignore rules
├─ .env.example               # Environment variable template
├─ README.md                  # Quick start guide
├─ AGENTS.md                  # AI‑friendly quick reference
└─ doc.md                     # Full documentation (this file)
```

### Data Flow

1. **TCP Listener** – `listener.listen()` runs in its own thread, bound to the port defined by `PORT_LISTENER`.
2. **Packet Parser** – Each incoming line is parsed by `analyse_data()` which dispatches to methods of an `InitTarget` instance.
3. **Database Persist** – `InitTarget` methods (`start_programm`, `start_serie`, `shot`, …) open a fresh connection via `_get_connection()`, perform inserts/updates, and commit.
4. **API** – `server.api.shots.get_shots()` reads the current series of a target using `database.reader.listLastShot()` and returns shot data as JSON.
5. **Front‑end** – `server/static/js/update-target.js` periodically fetches `/api/shots?target=X` and draws cross‑hair SVGs.

---

## 3. Technical Choices

| Component            | Reasoning                                                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Flask**            | Lightweight micro‑framework, fast to set up and enough for a small API.                                                 |
| **MariaDB**          | Relational DB with robust transaction support; the schema is simple and the `mariadb` Python driver is well maintained. |
| **Python‑Dotenv**    | Keeps configuration (ports, DB credentials) in a `.env` file.                                                           |
| **Vanilla JS + SVG** | No heavy front‑end framework is needed for rendering cross‑hairs; pure JS keeps bundle size small.                      |
| **Threading**        | The TCP listener is non‑blocking; using a separate thread keeps the Flask request thread free.                          |

---

## 4. Prerequisites & Dependencies

| Item                              | Version | Notes                                        |
| --------------------------------- | ------- | -------------------------------------------- |
| Python                            | ≥ 3.11  | Used throughout the repo.                    |
| pip                               | –       | Standard package manager.                    |
| MariaDB                           | ≥ 10.5  | Any compatible server; local or remote.      |
| `pip install -r requirements.txt` | –       | Installs Flask, mariadb, python‑dotenv, etc. |

### Environment Variables

All configuration is read from a `.env` file (example in `.env.example`). Required variables:

```text
DATABASE_URL=your_db_host
DATABASE_PORT=3306
DATABASE_USER=your_user
DATABASE_PASSWORD=your_pass
DATABASE_NAME=targetdb
URL_LISTENER=0.0.0.0
PORT_LISTENER=4000
NumberOfTarget=5
```

### Running the Application

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Ensure the database schema is ready
#   Create the database and run the SQL script:
mysql -u <user> -p <database_name> < database/src/create_structure.sql

# 3. Set up environment variables (copy .env.example to .env and edit)
cp .env.example .env

# 4. Start the server
python main.py
```

The Flask app will be reachable at `http://localhost:5000/`. The TCP listener will bind to the configured host/port.

---

## 5. API Usage

### Endpoint

```
GET /api/shots?target=<target_number>
```

- **Query Parameter** – `target` (required) must be an integer (1‑based index). `NumberOfTarget` in the config determines the maximum.

- **Response** – JSON array of shot objects, each with:
  - `x`: float (meters)
  - `y`: float (meters)
  - `number`: integer (shot sequence, 1 = most recent)

Example response for target 1:

```json
[
  {"x": -0.12, "y": 0.200, "number": 1},
  {"x": 0.01, "y": -0.04, "number": 2},
  …
]
```

- **Error Responses** – 400 if `target` missing or invalid, 404 if no data.

### How the Front‑end Consumes It

`server/static/js/update-target.js` performs a fetch every 2 s:

```js
fetch(`/api/shots?target=${targetId}`)
  .then((r) => r.json())
  .then((shots) => drawShotsOnSvg(svgElement, shots));
```

The SVG is updated by drawing cross‑hair lines and numbering each shot.

---

## 6. Core Classes & Functions

### `database.writer.InitTarget`

Represents the state of a single target. Instances are stored in the global `targets` list by `listener`. Key methods:

| Method                                                | Purpose                                                   |
| ----------------------------------------------------- | --------------------------------------------------------- |
| `start_programm(shooter_number, time, guid)`          | Inserts a new row in `programm` table.                    |
| `start_serie(serie_type, time, guid)`                 | Inserts a new series row linked to the current programme. |
| `serie_finish(time)`                                  | Marks the current series as finished (`show = 1`).        |
| `programm_finish()`                                   | Finalises the programme, sets base scores.                |
| `shot(pos_x, pos_y, score_10, score_100, time, guid)` | Inserts a shot into `shots` linked to the current series. |

All DB operations open a fresh connection via `_get_connection()` and commit/rollback as needed.

### `database.reader.listLastShot(target_number)`

Reads all shots of the _current_ series for the specified target, returning a list of `(x, y)` tuples. The list is reversed so that the most recent shot appears first.

### `listener.analyse_data(line)`

Parses a CSV line received on the TCP socket, determines the data type (`_SHOT`, `_GRPH`, etc.) and forwards it to the appropriate `InitTarget` method.

### `server.api.shots.get_shots()`

Flask view that extracts the `target` query param, calls `listLastShot`, and formats the result for the front‑end.

---

<!--
## 7. Extending & Debugging

| Task                         | Suggested Approach                                                                                                      |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Add new API endpoint**     | Create a route in `server/api/`, register the blueprint in `server/app.py`, and write a helper in `database/reader.py` or `database/writer.py` if DB access is needed. |
| **Implement authentication** | Add a simple token header check in `server.api.shots.get_shots` or integrate Flask‑Login / JWT.                         |
| **Add unit tests**           | Use `pytest` and `pytest-flask` to test routes; mock DB connections using `unittest.mock`.                              |
| **Improve logging**          | Replace `print` statements with Python's `logging` module; configure a file or stream handler.                          |
| **Dockerise**                | Create a `Dockerfile` that installs dependencies and runs `python main.py`.                                            |

---
-->

## 8. Roadmap (as of Oct 2026)

- [x] Register the shots into the database.
- [x] Display the shots on the target.
- [ ] Automatically change the taget type on the web UI
- [ ] Add a score table
- [ ] Add a diaporama of the sponsors
- [ ] add graphics for every shooters and global statisticals

---

_For any questions or further details, refer to the source code or contact the project maintainer._

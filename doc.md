# Polytronic Target Display – Technical Documentation

Nov 9, 2026 · @Théo Lädeach

## 1. Overview

Polytronic Target Display receives live shot data from the official Polytronic shooting-range software over TCP, stores it in MariaDB, and shows it in a browser: live impact positions per target, per-shooter statistics, and a history of every programme.

This document describes the `main` branch as read at commit `80c32ab`. Every statement was checked against the source code; `doc.md` was deliberately ignored. For the Polytronic software setup, a sample of raw packets and the discovered packet fields, see `README.md`. Section 5 only documents how the listener uses those fields.

| Layer | Technology |
| --- | --- |
| Language | Python 3.11 or newer |
| Web server | Flask (blueprints, Jinja2 templates), development server |
| Database | MariaDB 10.5+ through the `mariadb` driver and its connection pool |
| Configuration | `python-dotenv` (`.env` file) |
| Front end | Vanilla JavaScript, inline SVG, Chart.js loaded from a CDN |

`requirements.txt` lists three unpinned packages: `python-dotenv`, `flask`, `mariadb`. The `mariadb` package needs the MariaDB Connector/C library installed on the machine.

**Vocabulary used throughout**

| Term | Meaning |
| --- | --- |
| Target | One shooting lane. Zero-based index in code, one-based in URLs, the API query string and the UI. |
| Shooter | A person, identified by the number printed on the stand sheet (`shooter_number`). |
| Programm | One run by a shooter on a target. The double "m" is the spelling used in code, tables and URLs. |
| Series | A group of shots inside a programm. Has a numeric `type` sent by the Polytronic software. |
| Shot | One impact: x/y position in metres from the centre, plus a score on a 10 scale and a 100 scale. |
| Target type | The paper target face, currently `A10` or `B4` (images in `server/static/assets/`). |

## 2. Architecture

One Python process runs two cooperating parts: a TCP listener that writes shot data into MariaDB, and a Flask web server that reads it back for the browser. The database is the only thing they share that matters.

&#91;embedded content: architecture · 7 components, one shared database\]

The listener writes and the web server reads; the database holds everything they exchange.

| Component | Files | Role |
| --- | --- | --- |
| Launcher | `main.py` | Loads `.env`, parses CLI flags, starts the listener thread and the Flask server. |
| TCP listener | `listener.py` | Accepts connections from the Polytronic software, parses `;`-separated lines, calls the write layer. |
| Write layer | `database/writer.py` | One `InitTarget` object per target; inserts shooters, programms, series, shots; maintains the `current` table. |
| Read layer | `database/reader.py` | All SELECT queries used by the API and the HTML pages. |
| Connection pool | `database/connection.py` | A `mariadb.ConnectionPool` of 5 connections and the `execute_request` helper. |
| Web app | `server/app.py`, `server/api/`, `server/routes/` | Flask app with an `/api` blueprint (JSON) and an HTML blueprint (Jinja2 pages). |
| Browser code | `server/templates/`, `server/static/` | Pages that poll the API and draw impacts as SVG. |

### Run modes

`main.py` offers three modes. Passing both `--web_server_only` and `--listener_only` raises an error.

| Command | Listener | Web server |
| --- | --- | --- |
| `python main.py` | Daemon thread | Main thread |
| `python main.py --web_server_only` | Not started, `listener.py` not imported | Main thread |
| `python main.py --listener_only` | Main thread, blocking | Not started |

In the default mode the Flask server runs with `use_reloader=False`, so the listener thread is not started twice. The thread is a daemon: stopping the main thread (Ctrl+C) ends both.

### Threads and shared state

- The listener accept loop handles each accepted connection in its own daemon thread.
- Flask's development server serves each request in a thread of its own.
- `database.writer` builds a module-level list `targets` of `InitTarget` objects, indexed from 0, when it is first imported. The listener uses it to write, and `server/api/shots.py` uses it to know how many targets exist.
- The database is the source of truth for what is running right now: the `current` table stores, per target, the active programm and series. Readers always ask the database, never the in-memory objects.
- Importing `database.writer` opens the connection pool and creates the `current` rows. The web server imports it too, so the database must be reachable even with `--web_server_only`.

### Data flow

1. The Polytronic software connects to the listener port (4000 by default) and sends one packet per line.
2. The listener checks the client IP against an allowlist, decodes the line as latin-1 and splits it on `;`.
3. The packet type selects an `InitTarget` method, which writes to MariaDB and updates `current`.
4. The browser calls `GET /api/shots/targets/all` every 2000 ms.
5. The API reads the current series of each target from the database and returns JSON.
6. `update-target.js` draws a crosshair per shot on each target's SVG.

## 3. Repository layout

The backend lives in `database/` and `listener.py`, the web application in `server/`. The table below lists every tracked source file; the layout tree in `README.md` is slightly out of date (it names `routes/app_routes.py`, which no longer exists).

| Path | Role |
| --- | --- |
| `main.py` | Entry point: loads `.env`, parses flags, starts listener and/or web server. |
| `listener.py` | TCP server, allowlist, line parser and packet dispatch. |
| `database/connection.py` | Connection pool and `execute_request()` for SELECT queries. |
| `database/writer.py` | `InitTarget` class, `targets` list, `get_current()`, shooter lookup. |
| `database/reader.py` | Read helpers: last shots, scores, shooters, programms, series. |
| `database/src/create_structure.sql` | MariaDB schema (five tables). Drops and recreates them. |
| `server/app.py` | Creates the Flask app, registers the `/api` and `/` blueprints, `startWebServer()`. |
| `server/api/__init__.py` | The `api` blueprint: mounts `shots` at `/shots` and `shooter` at `/shooters`. |
| `server/api/shots.py` | Live shot endpoints. |
| `server/api/shooter.py` | Shooter list endpoint. |
| `server/routes/__init__.py` | The HTML blueprint: mounts `default_routes` at `/` and `statistics` at `/statistics`. |
| `server/routes/default_routes.py` | Home, target, fullscreen target and credits pages. |
| `server/routes/statistics.py` | Per-shooter statistics and per-programm detail pages. |
| `server/templates/base.html` | Layout: fixed sidebar navigation, `content` and `scripts` blocks. |
| `server/templates/target.html`, `target_fs.html` | Live target grid. `target.html` wraps `target_fs.html` with `{% include %}`. |
| `server/templates/statistics.html`, `programm.html` | Shooter statistics page, programm detail page. |
| `server/templates/home.html`, `credits.html` | Home page (empty block for now) and credits. |
| `server/static/style.css` | The site theme and the target grid. |
| `server/static/fullscreen.css` | An older fullscreen layout; no template in the current tree links it. |
| `server/static/js/update-target.js` | Polling, coordinate conversion and SVG drawing of shots. |
| `server/static/js/fit-grid.js` | Chooses the number of grid columns for the target page. |
| `server/static/js/statistics.js`, `graphs.js` | Shooter dropdown and the Chart.js line chart. |
| `server/static/assets/` | Target face images `target_A10.png` and `target_B4.png`. |
| `.env.example` | Template for the `.env` file (Section 4). |
| `README.md`, `AGENTS.md`, `bug_to_fix.md`, `doc.md` | Project notes. `bug_to_fix.md` is a French to-do list; `doc.md` is not covered here. |

## 4. Configuration

All settings come from environment variables, usually a `.env` file copied from `.env.example`, plus a few command-line flags. `main.py` calls `load_dotenv()` before importing the listener and database modules, which read their variables at import time. A variable already set in the real environment wins over the `.env` file (the `python-dotenv` default).

### Environment variables

| Variable | Code default | Read in | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | `localhost` | `database/connection.py` | MariaDB host name or IP (a host, not a URL). |
| `DATABASE_PORT` | `3306` | `database/connection.py` | MariaDB port. |
| `DATABASE_NAME` | `polytronic-target-display` | `database/connection.py` | Schema the pool connects to. |
| `DATABASE_USER` | none | `database/connection.py` | Database user. |
| `DATABASE_PASSWORD` | none | `database/connection.py` | Database password. |
| `PORT_LISTENER` | `4000` | `listener.py`, `main.py` | TCP port the listener binds. |
| `ALLOWED_IPS_LISTENER` | `127.0.0.1` | `listener.py` | Comma-separated client IPs allowed to connect. |
| `HOST_LISTENER` | `0.0.0.0` | `listener.py` | Default bind address of `listen()`; see the quirks below. |
| `URL_LISTENER` | `0.0.0.0` | `main.py` | Default of `--listen-ip`. Not listed in `.env.example`. |
| `HOST_WEB_SERVER` | `0.0.0.0` | `main.py` | Default of `--web_server-host`. |
| `PORT_WEB_SERVER` | `5000` | `main.py` | Default of `--web_server-port`. |
| `NumberOfTarget` | `5` | `database/writer.py`, `server/routes/default_routes.py` | Number of targets created and displayed. |

### Command-line flags

| Flag | Default | Effect |
| --- | --- | --- |
| `--web_server_only` | off | Skip the listener. |
| `--listener_only` | off | Skip the web server. |
| `--web_server-host` | `HOST_WEB_SERVER` or `0.0.0.0` | Flask bind address. |
| `--web_server-port` | `PORT_WEB_SERVER` or `5000` | Flask port. |
| `--listen-ip` | `URL_LISTENER` or `0.0.0.0` | Listener bind address. |
| `--listen-port` | `PORT_LISTENER` or `4000` | Listener port. |
| `--debug` | `False` | Parsed, but not used (see below). |

### Quirks to know about

- `main.py` always passes `--listen-ip` to `listen()`, and that flag defaults from `URL_LISTENER`, not `HOST_LISTENER`. Started through `main.py`, `HOST_LISTENER` has no effect.
- `main.py` calls `startWebServer(..., debug=True)` with a hard-coded value, so `--debug` changes nothing and the Flask debugger is always on.
- `ALLOWED_IPS_LISTENER` is split on commas without trimming spaces, and compared as exact strings. Write `127.0.0.1,192.168.1.100` with no spaces.
- `NumberOfTarget` is read in two places and both must agree. The route `/target/fullscreen` ignores it and always renders 5 targets.

## 5. TCP listener

`listener.py` turns each line sent by the Polytronic software into database writes. Six packet types are handled; every other type is ignored without a log entry.

### Transport

- `listen(host, port)` opens a TCP socket with `SO_REUSEADDR` and a backlog of 5, then loops on `accept()`.
- A client whose IP is not in `ALLOWED_IPS_LISTENER` gets a warning in the log and its connection is closed at once.
- Each accepted connection runs `handle_connection()` in a daemon thread. It reads the stream line by line, decodes each line as latin-1 and passes it to `analyse_data()`.
- No read timeout and no keep-alive option is set. A dead connection stays open until the operating system reports it.
- There is no authentication and no encryption. The IP allowlist is the only protection.

### Parsing

`analyse_data()` splits the line with `csv.reader(delimiter=";")`. The same positions apply to every handled packet type:

| Index | Content |
| --- | --- |
| `0` | Packet type: `_NAME`, `_PRCH`, `_GRPH`, `_SUBT`, `_PRST` or `_SHOT`. |
| `1` | Target number, zero-based. It must satisfy `0 <= n < len(targets)`, otherwise an error is logged and the packet is dropped. |
| `3` | Shooter number. |
| `6` | Time of day, when present. Otherwise the server clock is used, formatted `HH:MM:SS.ffffff`. |

The positions that differ per packet type:

| Packet | Extra fields used | Method called | Effect |
| --- | --- | --- | --- |
| `_NAME` | `5` shooter name | `write_shooter` | Inserts the shooter, or updates the name if the number exists. |
| `_PRCH` | `25` GUID | `start_programm` | Closes the previous programm, then inserts a new one. |
| `_GRPH` | `9` series type (int), `14` GUID | `start_serie` | Closes the previous series, then inserts a new one. |
| `_SHOT` | `10` score on 10, `11` score on 100, `14` x, `15` y, `20` GUID | `shot` | Inserts a shot into the current series. |
| `_SUBT` | none | `serie_finish` | Totals the scores of the current series and stamps its end. |
| `_PRST` | none | `programm_finish` | Totals the scores of the current programm and stamps its end. |

The sample packets in `README.md` have no field `6` for `_NAME` and `_PRST`, so those use the server clock. A normal session arrives as `_NAME`, `_PRCH`, then one or more blocks of `_GRPH`, several `_SHOT` and `_SUBT`, and finally `_PRST`.

### What each write does

- **`start_programm`**: calls `programm_finish` for the previous programm, looks up the shooter id from the shooter number, inserts the programm with target type `A10` (hard-coded default), then stores the new id in memory and in `current.programm_id`.
- **`start_serie`**: calls `serie_finish`, reads the active programm id from `current` (no programm: the packet is dropped with an error), inserts the series, then writes its id to `current.series_id`. If the insert fails, `current.series_id` is set to `NULL`.
- **`shot`**: reads the active series id from `current` (none: dropped with an error) and inserts the shot.
- **`serie_finish`**: sums the shot scores on both scales and updates the series with totals, `end_time` and `show = 1`.
- **`programm_finish`**: sums the series totals on both scales and updates the programm with totals and `end_time`.

A series of type `2` is created with `show = 0` and becomes visible (`show = 1`) when it finishes. While `show` is 0, the live API returns no shots for it.

### Errors and duplicates

- A line that raises inside a handler is logged with its traceback and dropped; the connection stays open.
- A repeated packet violates a unique index (Section 6). The writer logs the integrity error, rolls back and carries on.
- A failure at connection level is logged, the thread ends and the socket is closed.

## 6. Data model

Five tables hold the data. Four form a chain (`shooters` > `programm` > `series` > `shots`), and `current` records which programm and series are running on each target. The schema is `database/src/create_structure.sql`.

**Warning:** the script runs `DROP TABLE IF EXISTS` on every table before recreating it. Running it again on a live database erases all recorded data.

&#91;embedded content: data model · 5 tables, 4 in a chain\]

Each arrow reads one to many. `current` keeps one row per target and points at the programm and series that are running.

### Tables

| Table | Column | Type | Notes |
| --- | --- | --- | --- |
| `shooters` | `id` | INT, PK, auto-increment |  |
|  | `shooter_number` | INT, NOT NULL | Unique. The number from the stand sheet. |
|  | `name` | VARCHAR(100), NULL | Set by `_NAME` packets. |
| `programm` | `id` | INT, PK, auto-increment |  |
|  | `score_base10`, `score_base100` | SMALLINT UNSIGNED, NULL | Totals, filled when the programm finishes. |
|  | `target_number` | TINYINT, NOT NULL | Zero-based target index. |
|  | `shooters_id` | INT, NULL | Foreign key to `shooters.id`. |
|  | `target_type` | VARCHAR(4), NULL | `A10` by default. |
|  | `start_time`, `end_time` | TIME(2), NOT NULL / NULL | Time of day only. |
|  | `GUID` | VARCHAR(10), NOT NULL | From the packet. |
| `series` | `id` | INT, PK, auto-increment |  |
|  | `score_base10`, `score_base100` | SMALLINT UNSIGNED, NULL | Totals, filled when the series finishes. |
|  | `programm_id` | INT, NOT NULL | Foreign key to `programm.id`. |
|  | `type` | INT, NOT NULL | Series type sent by the Polytronic software. |
|  | `show` | TINYINT(1), NOT NULL | 0 hides the shots from the live view. |
|  | `start_time`, `end_time` | TIME(2), NULL |  |
|  | `GUID` | VARCHAR(10), NOT NULL |  |
| `shots` | `id` | INT, PK, auto-increment |  |
|  | `x`, `y` | DECIMAL(4,3), NOT NULL | Metres from the target centre, millimetre precision. |
|  | `time` | TIME(2), NULL |  |
|  | `score_base10`, `score_base100` | TINYINT, NULL | Score on a 10 scale and on a 100 scale. |
|  | `series_id` | INT, NOT NULL | Foreign key to `series.id`. |
|  | `GUID` | VARCHAR(10), NOT NULL |  |
| `current` | `target_number` | INT, PK | One row per target, created at start-up. |
|  | `programm_id`, `series_id` | INT, NULL | Foreign keys to `programm.id` and `series.id`. |

All foreign keys use `ON DELETE NO ACTION` and `ON UPDATE NO ACTION`.

### GUID uniqueness

The Polytronic system reuses GUIDs at other times and on other targets, so a GUID is not unique on its own. Uniqueness is scoped to the parent, through three unique indexes:

| Table | Unique index |
| --- | --- |
| `programm` | `(target_number, GUID, start_time)` |
| `series` | `(programm_id, GUID)` |
| `shots` | `(series_id, GUID)` |

A packet delivered twice is refused by the index. A GUID reused elsewhere is accepted.

### How `current` behaves

- `InitTarget.__init__` inserts a `current` row with two NULLs for each target that has none.
- `start_programm` writes `programm_id`. `start_serie` writes `series_id`, or NULL when the series insert fails.
- No code clears either column when a programm or series finishes. After the last `_PRST`, the live view keeps showing the last series of that target until a new `_GRPH` arrives.

### Data conventions

- Times have no date. The driver returns `TIME` values as `datetime.timedelta`, and `format_time()` in `reader.py` converts them to `HH:MM:SS` strings.
- Every shot and every total exists on two scales: `score_base10` and `score_base100`.

## 7. Database layer

The `database` package splits into three modules: a pooled connection, a writer used only by the listener, and a reader used by the web server. All SQL uses `?` placeholders for values.

### Connection (`database/connection.py`)

- Importing the module creates `mariadb.ConnectionPool` named `mariadb_pool` with 5 connections and `autocommit=False`. The listener threads and the Flask threads share this pool.
- `_get_connection()` takes a connection from the pool. On a `mariadb.Error` it logs a fatal message and re-raises.
- `execute_request(request, data)` runs one statement and returns all rows for a SELECT, or `None` when the statement returns no result set. It never commits, so it is for reads only.

### Writer (`database/writer.py`)

The module builds `targets`, a list of `InitTarget(i)` for `i` in `range(NumberOfTarget)`. Each object represents one target and writes through its own `_execute_write()`.

| Method or function | What it does |
| --- | --- |
| `get_current(target_number)` | Returns `(programm_id, series_id)` read from the `current` table. |
| `getShooterByNumber(n)` | Returns `(shooters.id, name)`, or `(0, "???")` when the number is unknown. |
| `InitTarget.write_shooter(number, name)` | Upsert into `shooters` with `ON DUPLICATE KEY UPDATE name`. |
| `InitTarget.start_programm(shooter_number, time, guid, target_type="A10")` | Closes the previous programm, inserts a new one, updates `current`. |
| `InitTarget.start_serie(serie_type, time, guid)` | Closes the previous series, inserts a new one, updates `current`. |
| `InitTarget.shot(x, y, score_10, score_100, time, guid)` | Inserts a shot into the series referenced by `current`. |
| `InitTarget.serie_finish(time)` | Writes series totals, `end_time` and `show = 1`. |
| `InitTarget.programm_finish(time)` | Writes programm totals and `end_time`. |

`_execute_write(query, params, get_id=False)` opens a pooled connection, executes, commits, and returns `LAST_INSERT_ID()` when `get_id` is true. On a `mariadb.IntegrityError` or any other `mariadb.Error` it logs, rolls back and returns `None`. A caller therefore sees the same `None` for a duplicate and for an unreachable database; only the log tells them apart.

Two details:

- The `write_shooter` query names the schema `polytronic-target-display` explicitly, so it does not follow `DATABASE_NAME`.
- `reader.py` imports `get_current` from `writer.py`, so the finish methods import `listScore` from `reader.py` inside the function body to avoid a circular import.

### Reader (`database/reader.py`)

| Function | Returns |
| --- | --- |
| `format_time(value)` | `"HH:MM:SS"`, or `""` for `None`. Accepts `time`, `datetime`, `timedelta` or text. |
| `listLastShot(target_number)` | Shots of the target's current series, newest first. `[]` when there is no series or its `show` is 0. |
| `getShotsBySeriesId(series_id)` | Dict `serie_id`, `total_base10`, `total_base100`, `type`, `start_time`, `end_time`, `shots`. Each shot is a tuple `(x, y, score_base10, score_base100, time)`, newest first. `{}` when the series has no shots. |
| `listScore(parent_id, type, max)` | Scores of the shots of a series (`type="shots"`) or the series of a programm (`type="series"`), on base 10 or 100. Any other value raises `ValueError`. |
| `getShooterNumberWithTarget(target_number)` | `shooters_id` of the target's current programm, or `None`. This is the database id, not the stand-sheet number. |
| `getShooterWithId(id)` | `(shooter_number, name)` or `None`. |
| `getScoreSeriesOnTarget(target_number)` | Sum of the base-10 shot scores of the current series, or `None` without a series. |
| `getTargetType(target_number)` | `target_type` of the current programm, `"A10"` by default. |
| `getAllShooters()` | Every row of `shooters` as `(id, shooter_number, name)`. |
| `getAllShots(shooter_id)` | Base-100 score of every shot of a shooter, with no explicit ordering. |
| `getAllProgramm(shooter_id)` | List of dicts `id`, `score_base10`, `score_base100`, `target_type`, `start_time`, `end_time`. `[{}]` when there are none. |
| `getProgrammById(id)` | Dict with times, scores, `target_number` and `shooter` (`id`, `number`, `name`). `{}` when missing. |
| `getAllSeriesIdByProgrammId(id)` | List of series ids of a programm. |

## 8. Web server and API

Flask serves HTML pages from one blueprint tree and JSON from another; `server/app.py` mounts both. The app runs on Flask's built-in development server through `startWebServer()`.

| Blueprint | Mounted at | Contains |
| --- | --- | --- |
| `api` | `/api` | `shots` at `/api/shots`, `shooter` at `/api/shooters` |
| `routes` | `/` | `default_routes` at `/`, `statistics` at `/statistics` |

### HTML pages

| URL | Template | Data passed to the template |
| --- | --- | --- |
| `/` | `home.html` | None. The content block is empty for now. |
| `/target` | `target.html` | `target_number` = `NumberOfTarget`. |
| `/target/fullscreen` | `target_fs.html` | `target_number` = 5, hard-coded. |
| `/credits` | `credits.html` | None. |
| `/statistics/` and `/statistics/<shooter_id>` | `statistics.html` | `data`: `None` without an id. Otherwise `shooter_number`, `shooter_name`, `shots` (base-100 score of every shot) and `programm` (list of programm dicts). |
| `/statistics/programm/<programm_id>` | `programm.html` | `data`: `programm` (see `getProgrammById`) and `series` (one `getShotsBySeriesId` dict per series). `None` when no id is given. |

In the statistics URLs, `shooter_id` is the database id (`shooters.id`), not the stand-sheet number.

### JSON API

All endpoints answer `GET` and return JSON.

**`/api/shots/targets?target=N`** returns the live state of one target. `N` is one-based. A missing, non-numeric or zero value returns HTTP 400 with `{"message": "ERROR, invalid target number", "target": <raw value>}`. The upper bound is not checked: a number above `NumberOfTarget` returns the same structure with `null` values and an empty `shots` list.

```json
{
  "shooter_number": 44,
  "target_type": "A10",
  "total_score": 28,
  "shots": [
    {"x": 0.051, "y": -0.054, "number": 3, "score": 9},
    {"x": 0.021, "y": 0.006, "number": 2, "score": 10},
    {"x": -0.062, "y": -0.022, "number": 1, "score": 9}
  ]
}
```

| Field | Meaning |
| --- | --- |
| `shooter_number` | `shooters.id` of the shooter of the target's current programm, or `null`. The name is misleading: it is the database id. |
| `target_type` | Target face of the current programm, `"A10"` when there is none. |
| `total_score` | Sum of the base-10 scores of the current series, or `null`. |
| `shots` | Shots of the current series, newest first; empty when the series is hidden or has no shots. |
| `shots[].x`, `shots[].y` | Position in metres from the centre. `y` is positive upwards. |
| `shots[].number` | Rank in the series: 1 is the first shot fired, so the newest shot has the highest number. |
| `shots[].score` | Base-10 score of the shot. |

(The values above are illustrative.)

**`/api/shots/targets/all`** returns `{"targets": [ ... ]}` with one object of the shape above per target. The array follows the `targets` list: element 0 is target 1. This is the endpoint the browser polls.

**`/api/shooters/name/all`** returns `{"shooters_number": [[id, shooter_number, name], ...]}`. Despite the key name, every row has all three columns.

**Cost:** one target needs up to about ten SQL queries per call (current ids, series, shots, programm, scores). The target page therefore costs roughly fifty queries every two seconds per open browser with five targets.

## 9. Front end

The browser code is server-rendered Jinja2 pages plus vanilla JavaScript. The live target view polls the JSON API every two seconds and redraws each impact as an SVG crosshair; the other pages are rendered once by the server.

### Templates

| Template | Role |
| --- | --- |
| `base.html` | Layout with a fixed 260 px sidebar. Navigation links come from a `pages` list; the link whose URL equals `request.path` gets `aria-current="page"`. Blocks: `title`, `content`, `scripts`. |
| `target.html` | Heading plus `{% include "target_fs.html" %}`. |
| `target_fs.html` | Loops over `range(1, target_number + 1)` to create one card per target: an `<h2>` and an `<svg id="svg-targetN" viewBox="0 0 1024 1024">` holding the target image. Loads `update-target.js` and `fit-grid.js`, and contains an inline script that starts the polling loop. |
| `statistics.html` | Shooter dropdown, a line chart of the shooter's shot scores, and a table of their programms that links to the detail page. Loads Chart.js from the jsDelivr CDN, so the browser needs internet access. |
| `programm.html` | Programm summary, then one card per series with a table of shots and an SVG target. The SVG carries its shots as JSON in a `data-shots` attribute. A Back link returns to the shooter. |

### `update-target.js`

This file is shared by the live view and the programm page.

| Constant | Value | Meaning |
| --- | --- | --- |
| `API_BASE_URL` | `/api/shots/targets/all` | Endpoint polled. |
| `REFRESH_INTERVAL` | 2000 | Milliseconds between polls. |
| `CONFIG.svgSize` | 1024 | Side of the SVG coordinate space. |
| `CONFIG.targetSizeM` | 1.0 | Metres covered by the whole target image. |
| `CONFIG.crossSize`, `strokeWidth` | 22, 8 | Crosshair arm length and line width. |

- **Coordinates.** `metersToSvg(x, y)` computes `512 + x * 1024` and `512 - y * 1024`. The target centre is the middle of the image, and a positive `y` moves a shot up the screen.
- **Drawing.** `drawShotsOnSvg(svg, shots)` first removes every `line` and `text.shot-number` it added earlier. It then draws two lines and the shot number for each shot. The first element of the array, the newest shot, is blue. Older shots are red and lose 10% opacity per position, down to a floor of 40%.
- **Polling.** `refreshAllTargets()` fetches the API and pairs the n-th entry of `targets` with the n-th `.target-container .element` on the page. It draws the shots, and when the target has at least one shot it sets the image to `/static/assets/target_<target_type>.png`.
- **Scheduling.** On `DOMContentLoaded`, a page that contains `.target-container` starts a loop built on a recursive `setTimeout`: the next request starts only after the previous one finished.
- **Static drawing.** `drawStaticShots()` finds every `svg[data-shots]`, parses the JSON rows `[x, y, score10, score100, time]`, and `shotsFromRows()` turns them into `{x, y, number}` objects, reversed so the newest comes first. The programm page uses this path.

### `fit-grid.js`

It picks the number of columns of `.target-container` so that the square targets come out as large as possible. For each candidate column count `c` it computes `rows = ceil(n / c)` and the largest square that fits a cell, after subtracting the title height. It keeps the best `c` and writes `--cols` and `--rows` as CSS custom properties on the container.

- Candidates are the divisors of `n`, so the grid is full: 6 targets give 1x6, 2x3, 3x2 or 6x1.
- When `n` is larger than 3 and has no divisors besides 1 and itself (5, 7, 11), every column count from 1 to `n` is allowed.
- It runs at load, on window resize and through a `ResizeObserver` on the container.

### Statistics page scripts

- `statistics.js` fills `#shooter_selector` from `/api/shooters/name/all`, using `row[0]` (id) as the value and `row[2]` (name) as the label. It intercepts the form submit and navigates to `/statistics/<id>`.
- `graphs.js` defines `create_line_charts(canvas, data)`: a Chart.js line chart with labels `1..n`, one dataset named "shot's score" in `#11A1E1`, and a y axis that starts at zero.

### Styling

`style.css` defines the colour theme as CSS variables, the fixed sidebar, cards (`.container`), clickable rows (`.page-link`), tables, the programm card grid (`.serie-card`) and the target grid. On the target page `.content` is pinned to the window height, with no page scroll. Media queries honour reduced motion, reduced transparency and increased contrast.

## 10. Installation and operations

The application needs Python 3.11+, a reachable MariaDB 10.5+ server with the MariaDB Connector/C library on the machine, and the official Polytronic software (Windows) configured to send its data to the listener.

### Installation

1. Clone the repository and create a virtual environment (`python -m venv .venv`, then activate it).
2. Install the dependencies: `pip install -r requirements.txt`.
3. Create the schema: `mysql -u <user> -p < database/src/create_structure.sql`. The README shows `database/create_structure.sql`, which is the wrong path. The script creates and selects the schema `polytronic-target-display`; keep that name, because `write_shooter` addresses it explicitly.
4. Copy `.env.example` to `.env` and fill in the database credentials, the listener allowlist and `NumberOfTarget` (Section 4).
5. Start with `python main.py`. The web interface is on port 5000 and the listener on port 4000 by default.
6. Point the Polytronic software at the machine and port of the listener, and add the IP of the Polytronic PC to `ALLOWED_IPS_LISTENER` (`127.0.0.1` when both run on the same PC).

The README also gives a Docker recipe for MariaDB; apply the same corrected path to its schema command.

### Checking that it works

- The log shows `[Thread] Connected <ip> : <port>` when the Polytronic software connects. Logging is set to `NOTSET`, so every level is printed.
- `http://localhost:5000/target` shows the target grid.
- `curl http://localhost:5000/api/shots/targets/all` returns the JSON that the page polls.

### Troubleshooting

| Symptom or log message | Likely cause |
| --- | --- |
| `Rejected connection from unauthorized IP` | The client IP is missing from `ALLOWED_IPS_LISTENER`, or the list contains spaces. |
| `target number invalid in the listener` | The packet's target index is not below `NumberOfTarget`. |
| `Serie without active programm`, `unable to insert a shot without active serie` | A `_PRCH` or `_GRPH` was missed or failed to save, for example when the server started in the middle of a session. Shots are dropped until the next `_GRPH`. |
| `Programm not save` | The insert failed: a duplicate `(target, GUID, start time)`, an unreachable database, or a shooter number the database does not know yet because no `_NAME` packet arrived first. |
| The live view shows an old series | `current` is not cleared when a series or programm ends (Section 6). |
| The statistics chart stays empty | The browser cannot reach the Chart.js CDN. |
| The process stops at start-up with a `mariadb` error | The pool is created on import, so wrong credentials or an unreachable server stop the process before it serves anything. |

### Security notes

- The Flask debugger is always on (Section 4) and the server binds `0.0.0.0` by default. The Werkzeug debugger allows remote code execution to anyone who can reach it, so keep the port on a trusted network or behind a firewall.
- Neither the web interface nor the listener has authentication. The listener's IP allowlist is the only filter.
- The server is Flask's development server; no production WSGI server is configured.
- `.env` holds the database password and must not be committed.

## 11. Extending the project

Most extensions touch one layer. The recipes below name the exact places to change, and the constraints that are easy to miss.

### Support a new target face

1. Add `server/static/assets/target_<TYPE>.png`, a square image drawn for the 1024 x 1024 viewBox. The scale assumes the image spans 1 m (`CONFIG.targetSizeM`).
2. No JavaScript change is needed: the browser builds the image URL from the `target_type` field of the API.
3. The value is stored in `programm.target_type`, a `VARCHAR(4)`, so it cannot exceed four characters.
4. Today the listener never passes a type: `start_programm` is called without one and falls back to `"A10"`. To get `B4` on screen, decode the type from the `_PRCH` packet and pass it as the `target_type` argument.

### Handle a new packet type

1. Add the type string to the lookup dict at the top of `analyse_data()`. Only types listed there get the common parsing of the target index and shooter number.
2. Add an `elif dataType == "..."` branch that reads the extra fields by index.
3. Add the matching method on `InitTarget` in `database/writer.py`, and write through `_execute_write()`.

### Add an API endpoint

1. Create a blueprint in `server/api/`, for example `api_xxx = Blueprint(...)`.
2. Register it in `server/api/__init__.py` with `api.register_blueprint(..., url_prefix="/xxx")`.
3. Put the SQL in `database/reader.py` and call it through `execute_request()` with `?` placeholders.

### Add a page

1. Add a route in `server/routes/default_routes.py`, or a new blueprint registered in `server/routes/__init__.py`.
2. Create a template that extends `base.html` and fills the `content` block (and `scripts` if needed).
3. Add a `(url, label)` pair to the `pages` list in `base.html` to show it in the sidebar.

### Change the number of targets

Set `NumberOfTarget` in `.env` and restart. New `current` rows are created on start-up and `fit-grid.js` adapts the layout. The `/target/fullscreen` route still renders 5 cards until its hard-coded value is changed.

### Change the schema

Edit `database/src/create_structure.sql` and the reader and writer code together. The script is destructive, so on a database that holds data apply the change with an `ALTER TABLE` instead of re-running it.

### Checks

There is no automated test suite. `python -m compileall main.py listener.py server database` checks syntax without a database. Importing `listener.py` imports `database.writer`, which connects to MariaDB, so testing `analyse_data()` needs either a database or a stub of `database.writer`.

## 12. Known limitations and observations

These points come from reading the code, not from running it against a live shooting session. They are listed so that nobody is surprised by them; none of them is fixed by this document.

### Data and timing

| Where | Observation | Consequence |
| --- | --- | --- |
| `writer.py` | `serie_finish` and `programm_finish` do not clear `current_serie_id` or `current_programm_id`. `start_serie` and `start_programm` call them again at the next start. | The `end_time` written at `_SUBT` or `_PRST` is overwritten by the start time of the next series or programm, and totals are recomputed. Only the last one keeps its true end. |
| `writer.py` | `current` is never cleared, and `start_programm` leaves `series_id` untouched. | After a programm ends, or while a new one has no series yet, the live view still shows the previous series. |
| `writer.py` | An unknown shooter number gives shooter id `0`. | The programm insert most likely fails on the foreign key until a `_NAME` packet has registered the shooter. |
| Schema | Every time column is `TIME(2)` with no date. | Statistics cannot be limited to a day. The README to-do list already plans a `date` column. |
| `reader.py` | `getAllShots` has no `ORDER BY`. | The order of points in the statistics chart is not guaranteed to be chronological. |
| `reader.py` | `getAllProgramm` calls `int()` on the score columns, which are `NULL` until a programm finishes. | The statistics page of a shooter with an unfinished programm is likely to fail with a `TypeError`. |
| `reader.py` | `getShotsBySeriesId` returns `{}` for a series without shots. | `programm.html` does not guard against that empty entry. |

### Interface and configuration

| Where | Observation | Consequence |
| --- | --- | --- |
| `target_fs.html`, `update-target.js` | Both start a polling loop on a page that has `.target-container`. | Each target page runs two loops and sends twice the requests. One of the two can be removed. |
| `main.py` | `debug=True` is hard-coded; `HOST_LISTENER` is unused. | See Section 4. |
| `base.html` | The active link is found by comparing `request.path` with the exact link URL. | Statistics routes are under `/statistics/`, with a trailing slash, so the Statistics link is not marked on those pages. |
| `server/api/shots.py` | The `target` parameter is not compared with `NumberOfTarget`. | An out-of-range number returns an empty target instead of an error. |
| `listener.py` | `analyse_data` catches `IndentationError`, which cannot occur there, and its log call passes `row` as a format argument. | That branch is dead code; failures go to the generic `except Exception`. |

### Documentation drift

- `README.md` and `AGENTS.md` name `server/routes/app_routes.py` and the endpoint `/api/shots?target=N`. The code has `default_routes.py`, `statistics.py` and `/api/shots/targets?target=N`.
- `bug_to_fix.md` marks as done several items that the current code does not show: a configurable debug flag, a socket timeout or keep-alive on the listener, use of `DATABASE_NAME` in `writer.py`, and a range check on `target` in the shots API.
- `README.md` says the schema script creates three tables; it creates five.

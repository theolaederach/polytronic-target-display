# polytronic‑target‑display

## Quick start

The project visualises live target‑shooting data received over a TCP socket. Data packets are parsed, stored in a MariaDB database, and served via a lightweight Flask API that a vanilla‑JS front‑end consumes.

---

## Prerequisites

| Item        | Minimum       | Notes                                            |
| ----------- | ------------- | ------------------------------------------------ |
| **Python**  | 3.11 or newer | The project is written in pure Python.           |
| **pip**     | –             | Python’s package manager.                        |
| **MariaDB** | 10.5+         | Any server compatible with the `mariadb` driver. |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/theolaederach/polytronic-target-display
cd polytronic-target-display

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

### Database setup

```bash
# Create the database and run the schema
# Replace <user> and <db_name> with your credentials
mysql -u <user> -p <db_name> < database/create_structure.sql
```

The SQL script creates the tables `programm`, `series`, and `shots`.

### Environment variables

Copy the example file and edit it with your own values:

```bash
cp .env.example .env
```

Required variables:

| Variable            | Description                                   |
| ------------------- | --------------------------------------------- |
| `DATABASE_URL`      | Hostname or IP of the MariaDB server          |
| `DATABASE_PORT`     | DB port (default 3306)                        |
| `DATABASE_USER`     | DB user                                       |
| `DATABASE_PASSWORD` | DB password                                   |
| `DATABASE_NAME`     | DB name                                       |
| `URL_LISTENER`      | IP to bind the TCP listener (e.g. `0.0.0.0`)  |
| `PORT_LISTENER`     | Port for the TCP listener (default `4000`)    |
| `NumberOfTarget`    | Number of targets to initialise (default `5`) |

---

## Running the application

```bash
# With the virtual environment activated
python app.py
```

- `app.py` starts a Flask web server (default on port 5000) **and** launches a background thread that listens on the TCP port defined by `PORT_LISTENER`.
- The front‑end is served at `http://localhost:5000/` and automatically polls the API for shot data.

### Stopping

Press `Ctrl+C` in the terminal that ran `app.py` – both the Flask server and the TCP listener will terminate.

---

## To do

- [x] make the target on the web page responsive
- [x] auto change the type of target on the webpage
- [ ] Add charts and statistics for each shooter
- [ ] Make the home page of the website
- [ ] Create an auto-install script
- [x] Make the web server and the listener independant
- [x] change the guid by the id of the shots/series/programm and add a table of the curreent shots/series/programm for each target.

---

## Project layout

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

---

## Contribution

Feel free to fork, create feature branches, and submit pull requests. Please keep the coding style consistent with the existing code (PEP‑8 for Python, camelCase for JS). Adding tests is appreciated.

---

> Made by [theolaederach](https://github.com/theolaederach) – co‑authored with AI.

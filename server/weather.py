# Title : weather
# Description : Fetch the current weather from OpenWeather and save it in weather.json.
#               The data is refreshed in a background thread.
#               Nothing here is used by the web interface yet.

import json
import logging
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Current weather endpoint, available with a free API key
API_URL = "https://api.openweathermap.org/data/2.5/weather"

# OpenWeather updates its data at most every 10 minutes, so asking more often
# gives the same answer. 10 minutes = 144 calls/day (~4400/month), far below
# the free plan limits (60 calls/minute, 1 000 000 calls/month).
UPDATE_INTERVAL_SECONDS = 600

# Do not let a dead network block the updater thread forever
REQUEST_TIMEOUT_SECONDS = 10

# weather.json is stored at the root of the project
WEATHER_FILE = Path(__file__).resolve().parent.parent / "weather.json"


def writeWeatherFile(content: dict) -> None:
    """
    Write a dict in weather.json. The file is created if it does not exist.
    The data is written in a temporary file first, then moved over weather.json,
    so a reader never sees a half-written file.

    Args :
        content (dict): the data to save as JSON.
    """
    temporary_file = WEATHER_FILE.with_suffix(".json.tmp")
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, ensure_ascii=False)
    # replace() is atomic: the old file is swapped in one step
    temporary_file.replace(WEATHER_FILE)


def readConfig() -> tuple[str, float, float] | None:
    """
    Read the OpenWeather settings from the environment (.env).
    Variables : OPENWEATHER_API_KEY, OPENWEATHER_LAT, OPENWEATHER_LON.

    Return :
        (api_key, latitude, longitude), or None if the key is missing
        or the coordinates are missing / invalid.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        logger.info("No OPENWEATHER_API_KEY in .env, weather is disabled")
        return None

    try:
        latitude = float(os.getenv("OPENWEATHER_LAT", ""))
        longitude = float(os.getenv("OPENWEATHER_LON", ""))
    except ValueError:
        logger.warning("OPENWEATHER_LAT / OPENWEATHER_LON are missing or not numbers")
        return None

    # A latitude goes from -90 to 90 and a longitude from -180 to 180
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        logger.warning("OPENWEATHER_LAT / OPENWEATHER_LON are out of range")
        return None

    return api_key, latitude, longitude


def fetchWeather(api_key: str, latitude: float, longitude: float) -> dict:
    """
    Call the OpenWeather API once.

    Args :
        api_key (str): the OpenWeather API key.
        latitude (float): latitude of the shooting range.
        longitude (float): longitude of the shooting range.

    Return :
        The JSON answer of the API (dict), temperatures in Celsius.

    Raises :
        urllib.error.URLError, TimeoutError or ValueError if the call fails.
    """
    query = urllib.parse.urlencode(
        {"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric"}
    )
    with urllib.request.urlopen(
        f"{API_URL}?{query}", timeout=REQUEST_TIMEOUT_SECONDS
    ) as response:
        return json.load(response)


def updateWeather(api_key: str, latitude: float, longitude: float) -> None:
    """
    Fetch the weather and save it in weather.json, with the time of the fetch.
    If the call fails, the error is logged and the previous file is kept,
    so old data is better than no data.

    Args :
        api_key (str): the OpenWeather API key.
        latitude (float): latitude of the shooting range.
        longitude (float): longitude of the shooting range.
    """
    try:
        data = fetchWeather(api_key, latitude, longitude)
        writeWeatherFile(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
        )
        logger.info("Weather updated")
    except Exception as error:
        # The URL (with the API key inside) is never logged, only the error type
        logger.warning("Weather update failed: %s: %s", type(error).__name__, error)


def weatherLoop(api_key: str, latitude: float, longitude: float) -> None:
    """
    Update the weather now, then again every UPDATE_INTERVAL_SECONDS.
    Never returns, it is meant to run in a daemon thread.

    Args :
        api_key (str): the OpenWeather API key.
        latitude (float): latitude of the shooting range.
        longitude (float): longitude of the shooting range.
    """
    # Event.wait() is used as a sleep: it returns False when the time is over
    # (and would return True if somebody called set(), which stops the loop)
    stop_event = threading.Event()
    while True:
        updateWeather(api_key, latitude, longitude)
        if stop_event.wait(UPDATE_INTERVAL_SECONDS):
            break


def startWeatherUpdater() -> threading.Thread | None:
    """
    Prepare weather.json and start the background refresh.
    - no API key (or bad coordinates): weather.json is emptied (`{}`), no thread.
    - API key ok: weather.json is created if missing (`{}` until the first
      answer), an existing file is kept until the first refresh succeeds.

    Return :
        The started thread, or None if the weather is disabled.
    """
    config = readConfig()

    if config is None:
        writeWeatherFile({})
        return None

    if not WEATHER_FILE.exists():
        writeWeatherFile({})

    # The first call is done in the thread, so the web server starts
    # even if OpenWeather is slow
    thread = threading.Thread(
        target=weatherLoop, args=config, name="weather-updater", daemon=True
    )
    thread.start()
    logger.info("Weather updater started (every %s s)", UPDATE_INTERVAL_SECONDS)
    return thread

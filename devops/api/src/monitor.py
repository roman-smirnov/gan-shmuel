import time
import threading
import requests
from datetime import datetime
from emails import notify_service_down, notify_service_recovered
import os

SERVICES = {
    "weighing": "http://prod-weight-app-1:5000/health",
    "billing": "http://prod-billing-app-1:5000/health",
}

CHECK_INTERVAL = 60  # seconds
TIMEOUT = 5          # seconds

# Per-service state
status = {
    name: {
        "up": True,
        "down_since": None,
        "fail_count": 0,
        "alert_sent": False,
    }
    for name in SERVICES
}

# Thread control
_STOP_EVENT = threading.Event()
_MONITOR_THREAD = None


def is_service_up(url: str) -> bool:
    try:
        r = requests.get(url, timeout=TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


def check_services():
    for name, url in SERVICES.items():
        up_now = is_service_up(url)
        svc = status[name]

        if not up_now:
            svc["fail_count"] += 1
            print(f"{name}: failure #{svc['fail_count']}")

            # First time we see it down
            if svc["up"]:
                svc["up"] = False
                svc["down_since"] = datetime.now()

            # Third consecutive failure → notify
            if svc["fail_count"] == 3 and not svc["alert_sent"]:
                notify_service_down(name)
                svc["alert_sent"] = True

            continue

        # Service is up here
        if not svc["up"]:
            # It was previously down → recovery
            downtime = int((datetime.now() - svc["down_since"]).total_seconds() / 60)
            if svc["alert_sent"]:
                notify_service_recovered(name, downtime)

            svc["up"] = True
            svc["down_since"] = None
            svc["fail_count"] = 0
            svc["alert_sent"] = False

        # Healthy and up
        svc["fail_count"] = 0
        print(f"{name}: healthy")


def _monitor_loop():
    print("Monitoring started. Checking services every", CHECK_INTERVAL, "seconds")

    # Loop until asked to stop
    while not _STOP_EVENT.is_set():
        check_services()
        # Wait for CHECK_INTERVAL seconds or until stop is signaled
        _STOP_EVENT.wait(CHECK_INTERVAL)


def start_monitoring():
    """
    Start the monitor in a background thread.
    Safe to call from your Flask app startup, etc.
    """
    if os.getenv("ENV") != "prod":
        print("Monitor disabled (ENV != prod)")
        return

    global _MONITOR_THREAD

    # Avoid starting multiple monitor threads
    if _MONITOR_THREAD is not None and _MONITOR_THREAD.is_alive():
        print("Monitor already running")
        return

    _STOP_EVENT.clear()
    _MONITOR_THREAD = threading.Thread(target=_monitor_loop, daemon=True)
    _MONITOR_THREAD.start()


def stop_monitoring():
    """
    Optional: call this if you want to stop the monitor cleanly.
    """
    _STOP_EVENT.set()
    if _MONITOR_THREAD is not None:
        _MONITOR_THREAD.join(timeout=5)


if __name__ == "__main__":
    # If you run this module directly, it behaves as a standalone script.
    start_monitoring()
    try:
        # Keep the main thread alive while the daemon thread runs
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        stop_monitoring()
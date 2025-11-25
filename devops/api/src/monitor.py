import time
import requests
from datetime import datetime
from emails import notify_service_down, notify_service_recovered
import os

if os.getenv("ENV") != "prod":
    print("Monitor disabled (ENV != prod)")
    exit()


SERVICES = {
    "weighing": "http://prod-weight-app-1:5000/health",
    "billing": "http://prod-billing-app-1:5000/health",
}

CHECK_INTERVAL = 60  
TIMEOUT = 5 

status = {
    name: {
        "up": True,
        "down_since": None,
        "fail_count": 0,         
        "alert_sent": False      
    }
    for name in SERVICES
}


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

    
            if svc["up"]:
                svc["up"] = False
                svc["down_since"] = datetime.now()

          
            if svc["fail_count"] == 3 and not svc["alert_sent"]:
                notify_service_down(name)
                svc["alert_sent"] = True

            continue

        if up_now and not svc["up"]:
            downtime = int((datetime.now() - svc["down_since"]).total_seconds() / 60)
            if svc["alert_sent"]:
                 notify_service_recovered(name, downtime)

            svc["up"] = True
            svc["down_since"] = None
            svc["fail_count"] = 0
            svc["alert_sent"] = False  

            

        if up_now:
            svc["fail_count"] = 0  
            print(f"{name}: healthy")


def start_monitoring():
    print("Monitoring started. Checking services every", CHECK_INTERVAL, "seconds")

    while True:
        check_services()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    start_monitoring()

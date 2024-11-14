# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from datetime import datetime, timedelta, timezone
from asyncio import create_task
import logging

from db import (
    get_alert_by_id,
    update_alert_next_tick,
    update_alert_notified_at,
    update_expiry_notification,
    update_added_notification,
)

from notification import send_notification


def get_key(alert, side, rule):
    type_key = f"type{side}"
    if rule[type_key] == "indicator":
        indicator_key = f"indicator{side}"
        output_key = f"output{side}"
        base = alert["settings"]["indicators"][rule[indicator_key]]["indicator"]["id"]
        output = rule[output_key]
        return f"{base}-{output}"
    elif rule[type_key] == "data":
        source = f"source{side}"
        name = f"name{side}"
        interval = f"interval{side}"
        key = f"key{side}"
        return f"{rule[source]}-{rule[name]}-{rule[interval]}-{rule[key]}"
    elif rule[type_key] == "value":
        return "value"


def evaluate(rules, operators):
    rules = ["True" if rule else "False" for rule in rules]

    expression = [None] * (len(rules) + len(operators))
    expression[::2] = rules
    expression[1::2] = operators

    expression = " ".join(expression)

    return eval(expression)


def get_change(previous, current):
    if current == previous:
        return 0.0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0.0


def alert_evaluate(dbconn, message, alert, data):

    alert = get_alert_by_id(dbconn, alert["id"])
    alert_message = alert["settings"]["message"]
    now = datetime.now(timezone.utc)

    if alert["expiry_notification_sent_at"] is None and alert["expire_date"] < now:
        update_expiry_notification(dbconn, alert["id"], now)
        send_notification(
            alert["settings"]["subscription"], f"Alert expired: {alert_message}"
        )

    if alert["expire_date"] < now:
        create_task(data["websocket_client"].close())
        data["in_progress"] = False
        return

    lastDataPoint = data["lastDataPoint"] if "lastDataPoint" in data else {}

    if alert["added_notification_sent_at"] is None and not lastDataPoint:
        update_added_notification(dbconn, alert["id"], now)
        send_notification(
            alert["settings"]["subscription"], f"Alert added: {alert_message}"
        )

    if message["type"] == "data_init":
        lastDataPoint.update(message["data"][-1])
    elif message["type"] == "indicator_init":
        lastDataPoint.update(message["data"][-1])
    elif message["type"] == "data_update":
        lastDataPoint.update(message["data"])
    elif message["type"] == "indicator_update":
        lastDataPoint.update(message["data"])
    data["lastDataPoint"] = lastDataPoint

    rules_evaluated = []

    rules = alert["settings"]["rules"]
    for rule in rules:
        k1 = get_key(alert, "1", rule)
        k2 = get_key(alert, "2", rule)

        if k1 not in ["value"] and k1 not in lastDataPoint:
            logging.info(f"do not have data {k1}; has keys {lastDataPoint.keys()}")
            return
        if k2 not in ["value"] and k2 not in lastDataPoint:
            logging.info(f"do not have data {k2}; has keys {lastDataPoint.keys()}")
            return

        if k1 == "value":
            v1 = float(f"{rule['value1']}")
        else:
            v1 = float(lastDataPoint[k1])

        if k2 == "value":
            v2 = float(f"{rule['value2']}")
        else:
            v2 = float(lastDataPoint[k2])

        if rule["comparator"] == "<":
            rules_evaluated.append(v1 < v2)
        elif rule["comparator"] == ">":
            rules_evaluated.append(v1 > v2)
        elif rule["comparator"] == "near":
            percent = float(rule["near"])
            rules_evaluated.append(get_change(v1, v2) < percent)

    result = evaluate(rules_evaluated, alert["settings"]["operators"])

    if result and alert["next_tick"] == 1:
        logging.info(f"alert {alert['id']} matched")
        update_alert_next_tick(dbconn, alert["id"], 0)

        send_notification(alert["settings"]["subscription"], alert_message)

    if not result and alert["next_tick"] == 0:
        update_alert_next_tick(dbconn, alert["id"], 1)

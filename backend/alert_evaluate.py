# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

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

from rules_evaluate import rules_evaluate


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

    rules = alert["settings"]["rules"]
    operators = alert["settings"]["operators"]
    indicators = alert["settings"]["indicators"]

    result, _ = rules_evaluate(rules, operators, indicators, lastDataPoint)

    if result and alert["next_tick"] == 1:
        logging.info(f"alert {alert['id']} matched")
        update_alert_next_tick(dbconn, alert["id"], 0)

        send_notification(alert["settings"]["subscription"], alert_message)

    if not result and alert["next_tick"] == 0:
        update_alert_next_tick(dbconn, alert["id"], 1)

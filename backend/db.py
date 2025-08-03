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

import sqlite3
import json
import logging
from datetime import datetime, timezone


from utils import resource_path
from indicators import get_indicator_data

indicators = get_indicator_data()


def populate_database_from_provider(database_path, provider):
    logging.info(f"Populating database from {type(provider).__name__}.")
    data = provider.get_dataset()

    logging.info("Inserting items into DB.")

    conn = create_connection(database_path)
    if conn is not None:
        create_tables(conn)  # Ensure the table exists

        data_entities = []
        for d in data:
            data_entity = {
                "id": f"{d['source']}-{d['name']}",
                "name": d["name"],
                "details": json.dumps(d),
                "type": "data",  # Set the type for this entry
            }
            data_entities.append(data_entity)

        insert_or_update_data_entities(conn, data_entities)

        # conn.close()
    else:
        logging.error("Error! cannot create the database connection.")

    logging.info("Done.")


def populate_database(database_path):
    """Populate the database with the initial set of data entities."""
    global indicators

    logging.info("Populating database with indicators.")

    conn = create_connection(database_path)
    if conn is not None:
        create_tables(conn)  # Ensure the table exists

        data_entities = []
        for _, indicator in indicators.items():
            d = {
                "categories": indicator["categories"],
                "library": indicator["path"].split(".")[1],
                "columns": indicator["klass"].columns,
                "inputs": [
                    {"name": i["name"], "default": i["default"]}
                    for i in indicator["klass"].inputs
                ],
                "outputs": [{**i} for i in indicator["klass"].outputs],
            }
            if hasattr(indicator["klass"], "optimization_strategies"):
                d["optimization_strategies"] = indicator[
                    "klass"
                ].optimization_strategies

            if hasattr(indicator["klass"], "mamode"):
                d["mamode"] = indicator["klass"].mamode

            if hasattr(indicator["klass"], "update_on"):
                d["update_on"] = indicator["klass"].update_on

            data_entity = {
                "id": indicator["path"],
                "name": indicator["name"],
                "details": json.dumps(d),
                "type": "indicator",  # Set the type for this entry
            }
            data_entities.append(data_entity)

        insert_or_update_data_entities(conn, data_entities)

        # conn.close()
    else:
        logging.error("Error! cannot create the database connection.")


def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(resource_path(db_file))
        return conn
    except Exception as e:
        logging.error(e)
    return conn


def get_alert_by_id(dbconn, id_):
    cursor = dbconn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE id = ?", (id_,))
    alert = cursor.fetchone()

    # Convert tuple to dictionary for better readability and convert strings to datetime
    if alert is not None:
        alert = {
            "id": alert[0],
            "settings": json.loads(alert[1]),
            "created_at": (
                datetime.strptime(alert[2], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[2]
                else None
            ),
            "next_tick": alert[3],
            "notified_at": (
                datetime.strptime(alert[4], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[4]
                else None
            ),
            "expiry_notification_sent_at": (
                datetime.strptime(alert[5], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[5]
                else None
            ),
            "expire_date": (
                datetime.strptime(alert[6], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[6]
                else None
            ),
            "added_notification_sent_at": (
                datetime.strptime(alert[7], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[7]
                else None
            ),
        }
    return alert


def get_metadata(dbconn, source, name):
    cursor = dbconn.cursor()
    cursor.execute(
        "SELECT details FROM data_entities WHERE id = ?", (f"{source}-{name}",)
    )
    d = cursor.fetchone()

    # Convert tuple to dictionary for better readability and convert strings to datetime
    if d is not None:
        data = json.loads(d[0])
    return data


def get_alerts(dbconn):
    create_tables(dbconn)  # make sure the table is existing

    cursor = dbconn.cursor()
    cursor.execute(
        "SELECT * FROM alerts WHERE datetime(expire_date) > datetime('now', 'utc')"
    )
    alerts = cursor.fetchall()

    # Convert them into list of dictionaries for better readability and convert strings to datetime
    alerts = [
        {
            "id": alert[0],
            "settings": json.loads(alert[1]),
            "created_at": (
                datetime.strptime(alert[2], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[2]
                else None
            ),
            "next_tick": alert[3],
            "notified_at": (
                datetime.strptime(alert[4], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[4]
                else None
            ),
            "expiry_notification_sent_at": (
                datetime.strptime(alert[5], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[5]
                else None
            ),
            "expire_date": (
                datetime.strptime(alert[6], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[6]
                else None
            ),
            "added_notification_sent_at": (
                datetime.strptime(alert[7], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                if alert[7]
                else None
            ),
        }
        for alert in alerts
    ]

    return alerts


def add_alert(dbconn, settings, expire_date):
    create_tables(dbconn)  # make sure the table is existing

    settings_str = json.dumps(settings)
    expire_date_str = expire_date.strftime(
        "%Y-%m-%d %H:%M:%S"
    )  # convert datetime object to a string

    cursor = dbconn.cursor()
    cursor.execute(
        "INSERT INTO alerts (settings, expire_date) VALUES (?, ?)",
        (settings_str, expire_date_str),
    )
    dbconn.commit()

    alert_id = cursor.lastrowid
    return {"id": alert_id, "settings": settings, "expire_date": expire_date}


def update_expiry_notification(dbconn, alert_id, expiry_notification_sent_at):
    # Convert datetime object to string
    expiry_notification_sent_at_str = expiry_notification_sent_at.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor = dbconn.cursor()
    cursor.execute(
        """
                   UPDATE alerts
                   SET expiry_notification_sent_at = ?
                   WHERE id = ?
                   """,
        (expiry_notification_sent_at_str, alert_id),
    )
    dbconn.commit()


def update_added_notification(dbconn, alert_id, added_notification_sent_at):
    # Convert datetime object to string
    added_notification_sent_at_str = added_notification_sent_at.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor = dbconn.cursor()
    cursor.execute(
        """
                   UPDATE alerts
                   SET added_notification_sent_at = ?
                   WHERE id = ?
                   """,
        (added_notification_sent_at_str, alert_id),
    )
    dbconn.commit()


def update_alert_next_tick(dbconn, alert_id, next_tick):
    cursor = dbconn.cursor()
    cursor.execute(
        """
                   UPDATE alerts
                   SET next_tick = ? 
                   WHERE id = ?
                   """,
        (next_tick, alert_id),
    )
    dbconn.commit()


def update_alert_notified_at(dbconn, alert_id, notified_at):
    # Convert datetime object to string
    notified_at_str = notified_at.strftime("%Y-%m-%d %H:%M:%S")

    cursor = dbconn.cursor()
    cursor.execute(
        """
                   UPDATE alerts
                   SET notified_at = ? 
                   WHERE id = ?
                   """,
        (notified_at_str, alert_id),
    )
    dbconn.commit()


def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    query = (
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    )
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone() is not None


def create_tables(conn):
    """Create table for storing data entities with specified field sizes."""
    try:
        existed = table_exists(conn, "data_entities")

        sql_create_table = """
        CREATE TABLE IF NOT EXISTS data_entities (
            id VARCHAR(256) PRIMARY KEY,
            name TEXT NOT NULL,
            details VARCHAR(512),
            type VARCHAR(256) NOT NULL
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql_create_table)

        sql_create_table = """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            settings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            next_tick INTEGER DEFAULT 1,
            notified_at TIMESTAMP NULL,
            expiry_notification_sent_at TIMESTAMP NULL,
            expire_date TIMESTAMP NULL,
            added_notification_sent_at TIMESTAMP NULL
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql_create_table)

        if not existed:
            logging.info("DB created.")

    except Exception as e:
        logging.error(e)


def insert_or_update_data_entities(conn, data_entities):
    """Insert new data entities into the data_entities table or update them if they already exist."""
    sql_check = """SELECT id FROM data_entities WHERE id = ?"""
    sql_insert = (
        """INSERT INTO data_entities(id, name, details, type) VALUES(?,?,?,?)"""
    )
    sql_update = (
        """UPDATE data_entities SET name = ?, details = ?, type = ? WHERE id = ?"""
    )

    cur = conn.cursor()

    for data_entity in data_entities:
        cur.execute(sql_check, (data_entity["id"],))
        exists = cur.fetchone()

        if not exists:
            cur.execute(
                sql_insert,
                (
                    data_entity["id"],
                    data_entity["name"],
                    data_entity["details"],
                    data_entity["type"],
                ),
            )
        else:
            cur.execute(
                sql_update,
                (
                    data_entity["name"],
                    data_entity["details"],
                    data_entity["type"],
                    data_entity["id"],
                ),
            )

    conn.commit()


def unserialize_data_entity(row):
    d = {"id": row[0], "name": row[1], "details": json.loads(row[2]), "type": row[3]}
    return d


def search_data_entities(conn, query, type="data", limit=100):
    """Search for indicators that match any of the words in the query with prioritization."""
    if not query.strip():  # Check if the query is empty or just whitespace
        # If the query is empty, return all rows ordered by ID
        cur = conn.cursor()
        cur.execute(
            f'SELECT * FROM data_entities WHERE type = "{type}" ORDER BY id LIMIT {limit}'
        )
        rows = cur.fetchall()
        return [unserialize_data_entity(r) for r in rows]

    terms = query.split()  # Split the query into terms
    scoring_select = []
    params = []
    base_score = (
        100  # Arbitrary base score to ensure any match boosts the item significantly
    )

    for term in terms:
        # For each term, add conditions that increase the score if the term is found in name or details
        scoring_select.append(f"(CASE WHEN name LIKE ? THEN {base_score} ELSE 0 END)")
        scoring_select.append(
            f"(CASE WHEN details LIKE ? THEN {base_score} ELSE 0 END)"
        )
        params.extend(["%" + term + "%", "%" + term + "%"])

    # Construct the SELECT clause to include scoring
    score_clause = " + ".join(scoring_select) + " AS score"
    query_string = f'SELECT *, {score_clause} FROM data_entities WHERE type = "{type}" AND score > 0 ORDER BY score DESC, id ASC LIMIT {limit}'

    cur = conn.cursor()
    cur.execute(query_string, params)
    rows = cur.fetchall()
    return [unserialize_data_entity(r) for r in rows]

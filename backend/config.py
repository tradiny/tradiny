# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from dotenv import load_dotenv
import os

load_dotenv()

# Metadata for configuration variables: (name, default, description)
CONFIG_FIELDS = [
    ("HOST", "0.0.0.0", "Server host address"),
    ("PORT", "8000", "Server port number"),
    ("DB", "db.sqlite3", "Database file or URI"),
    ("VAPID_KEY_PATH", "private_key.pem", "Path to VAPID private key"),
    ("CSV_FOLDER_PATH", "", "Path to CSV folder data source"),
    ("CSV_DATE_COLUMN", "timestamp", "CSV column name for date"),
    ("CSV_DATE_COLUMN_FORMATTER", "ISO-8601", "Formatter for date column"),
    (
        "BINANCE_API_KEY",
        "",
        'API key for Binance (if you don\'t have API key, use "test" to enable)',
    ),
    ("BINANCE_API_SECRET", "", "API secret for Binance"),
    ("POLYGON_IO_API_KEY", "", "API key for Polygon.io"),
    (
        "POLYGON_MARKETS",
        "options,indices,fx,stocks",
        "Markets for Polygon.io (CSV format)",
    ),
    ("OPENAI_API_KEY", "", "API key for OpenAI"),
    (
        "SMTP_EMAIL_FROM",
        "",
        "Your email address for sending notifications (leave empty to disable)",
    ),
    (
        "SMTP_EMAIL_TO",
        "",
        "Recipient's email address (use the same address as SMTP_EMAIL_FROM for instant alerts)",
    ),
    ("SMTP_PASSWORD", "", "Email password (in the case of Gmail, use App Password)"),
    ("SMTP_HOST", "smtp.gmail.com", "SMTP SSL hostname"),
    ("SMTP_PORT", "465", "SMTP SSL port"),
    ("ALERT_WORKERS", "5", "Number of alert worker threads"),
    ("INDICATOR_WORKERS", "5", "Number of indicator worker threads"),
    ("MAX_REQUESTS_PER_IP_PER_HOUR", "100", "Max requests per hour per IP"),
    (
        "MAX_SIMULTANEOUS_CONNECTIONS_PER_IP",
        "50",
        "Max simultaneous connections per IP",
    ),
    ("MAX_DATA_REQUESTS_PER_IP_PER_HOUR", "300", "Max data requests per IP per hour"),
    (
        "MAX_OPENAI_REQUESTS_PER_IP_PER_HOUR",
        "100",
        "Max OpenAI requests per IP per hour",
    ),
    ("EXPIRE_ALERT_IN_MINUTES", str(60 * 24), "Expire alerts after minutes"),
    ("MAX_ALERTS_PER_IP_PER_DAY", "10", "Max alerts per IP per day"),
    (
        "WHITELIST_IP",
        "127.0.0.1",
        "Whitelisted IPs (no limitations apply for these IPs, CSV format)",
    ),
]


class Config:
    pass


def update_config_vars():
    global Config

    # Reflect the most recent .env changes
    load_dotenv(override=True)

    # Dynamically add attributes to the Config class
    for field_name, default, _ in CONFIG_FIELDS:
        # Use setattr to add attributes to the Config class with loaded environment values
        setattr(Config, field_name, os.getenv(field_name, default))


update_config_vars()

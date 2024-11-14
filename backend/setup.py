# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.
from multiprocessing import freeze_support, set_start_method
set_start_method("spawn")
from pathlib import Path
from config import CONFIG_FIELDS, Config, update_config_vars

def main():
    freeze_support()

    env_file = Path(".env")

    EXCLUDED_FIELDS = [
        "HOST",
        "PORT",
        "DB",
        "VAPID_KEY_PATH",
        "CSV_DATE_COLUMN",
        "CSV_DATE_COLUMN_FORMATTER",
        "POLYGON_MARKETS",
        "ALERT_WORKERS",
        "INDICATOR_WORKERS",
        "MAX_REQUESTS_PER_IP_PER_HOUR",
        "MAX_SIMULTANEOUS_CONNECTIONS_PER_IP",
        "MAX_DATA_REQUESTS_PER_IP_PER_HOUR",
        "MAX_OPENAI_REQUESTS_PER_IP_PER_HOUR",
        "EXPIRE_ALERT_IN_MINUTES",
        "MAX_ALERTS_PER_IP_PER_DAY",
        "WHITELIST_IP",
    ]

    # Welcoming and informative setup message
    print(
        "Welcome to Tradiny Setup!\n"
        "Tradiny is a lightweight yet full-featured, highly-extensible, WebGL-powered, open-source charting platform.\n"
        "\n"
        "Let's configure your settings and prepare your database.\n"
        "Note:\n"
        "1. If you press enter without typing anything, the default value will be used.\n"
        "2. If you do not specify anything for fields without a default, the option will be disabled.\n"
    )

    configuration = {}

    for field_name, default, description in CONFIG_FIELDS:
        if field_name in EXCLUDED_FIELDS:
            continue  # Skip fields in the exclusion list

        # Get the current/default value from the Config class
        existing_value = getattr(Config, field_name, default)

        prompt = f"{description} [{existing_value}]: "
        input_value = input(prompt).strip() or existing_value
        configuration[field_name] = input_value

    with env_file.open("w") as f:
        for key, value in configuration.items():
            f.write(f"{key}={value}\n")

    print(".env file created successfully!")

    update_config_vars()

    from populate import main as populate

    populate()


if __name__ == "__main__":
    main()

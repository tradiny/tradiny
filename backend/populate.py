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

import db
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
# Set format for timestamp to be YYYY-MM-DD HH:MI:SS
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

from config import Config


def populate_from_provider(api_key, provider_class):
    if api_key:
        provider = provider_class()
        db.populate_database_from_provider(Config.DB, provider)


def main():

    providers = [
        (Config.CSV_FOLDER_PATH, "data_providers.csv.CSVProvider"),
        (Config.POLYGON_IO_API_KEY, "data_providers.polygon.PolygonProvider"),
        (Config.BINANCE_API_KEY, "data_providers.binance.BinanceProvider"),
    ]

    for api_key, provider_path in providers:
        module_name, class_name = provider_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        provider_class = getattr(module, class_name)
        populate_from_provider(api_key, provider_class)

    db.populate_database(Config.DB)

    logging.info("Populate done.")


if __name__ == "__main__":
    main()

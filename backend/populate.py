# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

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
        (Config.CSV_FILE_PATH, "data_providers.csv.CSVProvider"),
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

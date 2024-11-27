# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import uvicorn
import db
import os
import sys

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

from websocket_server import app, register_provider, register_startup_action
from vapid import generate as generate_vapid_keys


def initialize_provider(config_key, provider_module, provider_class):
    if getattr(Config, config_key):
        provider = getattr(
            __import__(provider_module, fromlist=[provider_class]), provider_class
        )()
        logging.info(f"Starting process for provider {provider.key}.")
        provider.start()
        return provider
    else:
        return None


def initialize_providers():
    providers = []
    provider_configs = [
        ("CSV_FOLDER_PATH", "data_providers.csv", "CSVProvider"),
        ("POLYGON_IO_API_KEY", "data_providers.polygon", "PolygonProvider"),
        ("BINANCE_API_KEY", "data_providers.binance", "BinanceProvider"),
    ]

    for env_key, config_path, provider_class in provider_configs:
        provider = initialize_provider(env_key, config_path, provider_class)
        if provider:
            providers.append(provider)

    return providers


def main(on_startup=None):

    providers = initialize_providers()

    async def startup_event():
        generate_vapid_keys()

        for provider in providers:
            register_provider(provider)

        if on_startup:
            on_startup()

    register_startup_action(startup_event)
    uvicorn.run(app, host=Config.HOST, port=int(Config.PORT), workers=1)


if __name__ == "__main__":
    main()

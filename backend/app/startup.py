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

import logging
import asyncio

from provider import register_provider, initialize_providers
from vapid import generate as generate_vapid_keys
from . import app
from .periodic import run_periodic_tasks
from .globals import startup_actions
from alert import init as alert_init
from scanner import init as scanner_init


def register_startup_action(action):
    startup_actions.append(action)


def register_startup_actions(on_startup):
    providers = initialize_providers()

    async def startup_event():
        generate_vapid_keys()

        for provider in providers:
            register_provider(provider)

        if on_startup:
            on_startup()

        alert_init()
        scanner_init()

    register_startup_action(startup_event)


@app.on_event("startup")
async def custom_startup():
    logging.info("Starting up...")
    # Execute all registered startup actions
    for action in startup_actions:
        await action()
    # Start periodic tasks
    app.state.periodic_task_runner = asyncio.create_task(run_periodic_tasks())


@app.on_event("shutdown")
async def custom_shutdown():
    logging.info("Shutting down...")
    # Cancel periodic tasks on shutdown
    app.state.periodic_task_runner.cancel()
    await app.state.periodic_task_runner

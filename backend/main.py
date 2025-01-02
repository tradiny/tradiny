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

from multiprocessing import freeze_support, set_start_method

set_start_method("spawn")


def main():
    from config import Config
    from utils import find_free_port, get_private_ip

    free_port = find_free_port(Config.HOST, 8000)
    Config.PORT = free_port

    def start_browser():
        import webbrowser

        webbrowser.open(f"http://{get_private_ip()}:{Config.PORT}")

    from server import main as server

    server(start_browser)


if __name__ == "__main__":
    freeze_support()  # required for pyinstaller on Windows
    main()

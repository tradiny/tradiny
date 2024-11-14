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

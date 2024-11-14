# Building a Windows Application Using pyinstaller

To create the Windows application, follow these steps:

1. **Build the Frontend:**

    Navigate to the `frontend` directory and run the following commands to install dependencies and build the frontend:

    ```bash
    npm install
    npm run build
    ```

1. **Copy Built Files:**

    - Copy the built frontend files into the `dist` directory located in the `backend` folder:

        ```bash
        cp -r dist/ ../backend/
        ```

1. **Set Up the Backend:**

    - Move to the `backend` directory.
        Remove existing `db.sqlite3` and `private_key.pem` if present: `rm db.sqlite3 private_key.pem`.

        Initialize empty DB and private key.
        Simply run the `server.py` script and exit (note that before running this command you need to install dependencies: `pip3 install -r requirements.txt`):

        ```bash
        python3 server.py
        ```

        You should see:

        ```
        2024-11-04 14:59:02 - INFO - DB created.
        2024-11-04 14:59:02 - INFO - New VAPID keys generated and saved.
        ```

1. **Build the Application:**

    - Install PyInstaller using the command:

        ```bash
        pip install pyinstaller
        ```

    - Run the PyInstaller command to compile the application:

        ```bash
        python3 -m PyInstaller --distpath ./out --clean tradiny.spec
        ```

This will generate the Windows application in the `out` directory.

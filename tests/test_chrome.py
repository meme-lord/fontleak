import time
import subprocess
import tempfile
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os


def test_secret_leak():
    # Start server process in the background
    print("Starting server...")
    server_process = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "fontleak.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "4242",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Give the server time to start
    time.sleep(2)

    # Debug: Check if server started correctly
    if server_process.poll() is not None:
        # Server exited prematurely
        stdout, stderr = server_process.communicate()
        print(f"Server exited prematurely with code {server_process.returncode}")
        print(f"Server stdout: {stdout.decode('utf-8', errors='replace')}")
        print(f"Server stderr: {stderr.decode('utf-8', errors='replace')}")
        raise RuntimeError("Server process failed to start")

    driver = None
    temp_dir = None

    try:
        # Create a unique temporary directory for Chrome user data
        unique_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_data_{unique_id}_")
        print(f"Created temporary directory: {temp_dir}")

        # Set up Chrome with minimal options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")

        print(f"Chrome options: {chrome_options.arguments}")

        # Initialize Chrome
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Visit the page
        print("Loading test page...")
        driver.get("http://127.0.0.1:4242/test")
        time.sleep(15)

        # Check server output
        server_process.terminate()
        stdout, stderr = server_process.communicate()
        stdout = stdout.decode("utf-8", errors="replace")
        stderr = stderr.decode("utf-8", errors="replace")

        # Print for debugging
        print(f"Server stdout: {stdout}")
        print(f"Server stderr: {stderr}")

        # Check for the secret
        assert "The quick brown fox jumps over the lazy dog" in stdout

    finally:
        # Clean up
        if driver:
            driver.quit()

        if temp_dir:
            try:
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to clean temp directory: {e}")

        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

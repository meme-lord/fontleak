import time
import subprocess
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os


def test_secret_leak():
    # Start server process
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
        text=True,
    )
    
    driver = None
    temp_dir = None

    try:
        # Create a temporary directory for Chrome user data
        temp_dir = tempfile.mkdtemp()
        
        # Set up Chrome with unique user data directory
        chrome_options = Options()
        chrome_options.add_argument(os.environ["CHROME_OPTIONS"])
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        driver = webdriver.Chrome(options=chrome_options)

        # Visit the page
        driver.get("http://localhost:4242/test")
        time.sleep(5)  # Wait for potential leak

        # Check server output
        stdout, _ = server_process.communicate(timeout=5)
        assert (
            "window.secret = 'The quick brown fox jumps over the lazy dog';" in stdout
        )

    finally:
        # Clean up
        if driver:
            driver.quit()
        if temp_dir:
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
        server_process.terminate()
        server_process.wait()

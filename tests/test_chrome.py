import time
import subprocess
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import uuid


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
        # Create a unique temporary directory for Chrome user data
        unique_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_data_{unique_id}_")
        print(f"Created temporary directory: {temp_dir}")
        
        # Set up Chrome with more specific options
        chrome_options = Options()
        for option in os.environ["CHROME_OPTIONS"].split():
            chrome_options.add_argument(option)
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        
        # Add more debug info
        print(f"Launching Chrome with options: {chrome_options.arguments}")
        
        # Use webdriver manager to handle chromedriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

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
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()

import time
import subprocess
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import uuid
import socket
import time


def wait_for_port(port, host='localhost', timeout=10.0):
    """Wait until a port is open on a host."""
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            if time.time() - start_time >= timeout:
                return False
            time.sleep(0.1)


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
    
    # Wait for the server to start
    print("Waiting for server to start...")
    if not wait_for_port(4242, host='localhost', timeout=10.0):
        server_process.terminate()
        server_process.wait()
        raise RuntimeError("Server failed to start within the timeout period")
    print("Server started successfully")
    
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

        # In Docker, localhost may not work correctly, use the Docker internal network
        print("Attempting to navigate to test page...")
        driver.get("http://0.0.0.0:4242/test")
        time.sleep(5)  # Wait for potential leak
        print("Page loaded successfully")

        # Check server output for the leaked info
        print("Checking server output...")
        # Use communicate with a timeout
        try:
            stdout, stderr = server_process.communicate(timeout=1)
            print(f"Server stdout: {stdout}")
            print(f"Server stderr: {stderr}")
            assert "window.secret = 'The quick brown fox jumps over the lazy dog';" in stdout
        except subprocess.TimeoutExpired:
            # If timeout, we need to read from pipes without closing them
            stdout = server_process.stdout.read()
            stderr = server_process.stderr.read()
            print(f"Server stdout (from read): {stdout}")
            print(f"Server stderr (from read): {stderr}")
            assert "window.secret = 'The quick brown fox jumps over the lazy dog';" in stdout

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

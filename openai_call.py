#!/usr/bin/env python3
"""
Example OpenAI API call that will be intercepted by the OpenAI Codegen Adapter.
"""

from openai import OpenAI
import os
import logging
import sys
import time
import threading

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set environment variable to point to our local server
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8001/v1"

print("Creating OpenAI client...")
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="my_api_key",
    base_url="http://127.0.0.1:8001/v1",
    timeout=30.0  # Set a 30-second timeout
)

# Define a function to run the API call in a separate thread
def run_api_call():
    try:
        print("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4-turbo-2025-08-01",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, GPT"}
            ],
            max_tokens=1024
        )
        print("Response received!")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Create and start the thread
api_thread = threading.Thread(target=run_api_call)
api_thread.start()

# Wait for the thread to complete or timeout
timeout = 30  # 30 seconds
start_time = time.time()
while api_thread.is_alive() and time.time() - start_time < timeout:
    time.sleep(1)
    print("Waiting for response...")

if api_thread.is_alive():
    print(f"Request timed out after {timeout} seconds")
    print("The server may not be responding properly. Check server logs for details.")
    # We can't forcibly terminate the thread in Python, but we can exit the program
    print("Exiting program...")
    sys.exit(1)

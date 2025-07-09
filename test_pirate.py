import requests


def chat_with_openai(api_key, messages):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-3.5-turbo",  # Specify the model you want to use
        "messages": messages,
    }

    response = requests.post(
        "http://127.0.0.1:8000/v1/chat/completions", headers=headers, json=data
    )

    if response.status_code == 200:
        return response.json()
    else:
        return f"Failed to get response. Status code: {response.status_code}, Response: {response.text}"


# Example usage
api_key = "your_openai_api_key"  # Replace with your actual API key
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"},
]

response = chat_with_openai(api_key, messages)
print(response)


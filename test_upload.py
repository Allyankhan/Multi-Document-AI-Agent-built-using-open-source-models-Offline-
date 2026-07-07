# test_upload.py
import requests

# 1. Create a quick dummy file to upload
with open("sample_doc.txt", "w") as f:
    f.write("This is a test document about LangChain and Ollama.")

# 2. Point to our FastAPI upload endpoint
url = "http://127.0.0.1:8000/upload"

# 3. Format the file for a multipart/form-data request
files = [
    ("files", ("sample_doc.txt", open("sample_doc.txt", "rb"), "text/plain"))
]

print("Uploading file to FastAPI...")
response = requests.post(url, files=files)

# 4. Print the result from the server
print(f"Status Code: {response.status_code}")
print("Response JSON:")
print(response.json())
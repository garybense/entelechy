import subprocess
import os

env = os.environ.copy()
env["ENTELECHY_API_LLM_PROVIDER"] = "vertexai"
env["ENTELECHY_API_LLM_VERTEXAI_SERVICE_ACCOUNT_KEY"] = "/tmp/gcp-credentials.json"
env["ENTELECHY_API_LLM_MODEL"] = "google/gemini-2.5-flash-lite"

# Create a fake creds file
with open('/tmp/gcp-credentials.json', 'w') as f:
    f.write('')

try:
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/test_server_integration.py::test_list_banks", "-v"],
        env=env,
        capture_output=True,
        text=True
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("RC:", result.returncode)
except Exception as e:
    print(f"Error: {e}")

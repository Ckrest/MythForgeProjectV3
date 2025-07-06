import requests
import json
import sys

def send_workflow():
    workflow_path = r"C:\Users\Ckrest\Documents\Gemini\Anime Random Workflow v1 exported.json"
    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # ComfyUI API endpoint
        url = "http://127.0.0.1:8001/prompt"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, data=json.dumps({"prompt": workflow}))
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        
        print(f"API call successful! Response: {response.json()}")
        
    except FileNotFoundError:
        print(f"Error: Workflow file not found at {workflow_path}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to ComfyUI. Is it running and accessible at http://127.0.0.1:8001?")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API call: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in workflow file at {workflow_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    send_workflow()

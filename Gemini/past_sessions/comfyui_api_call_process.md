**Summary of Learned Information:**

*   **ComfyUI API Endpoint:** The correct API endpoint for queuing prompts is `http://127.0.0.1:8001/prompt`.
*   **Workflow Format:** ComfyUI workflows must be in the 'API format' (JSON exported via 'Save (API format)' in ComfyUI's dev mode).
*   **Python Boolean Conversion:** When embedding JSON directly into Python scripts, `true` and `false` from JSON must be converted to Python's `True` and `False` respectively.
*   **Python Path Handling:** Windows file paths with backslashes in Python string literals require raw strings (e.g., `r"C:\path\to\file"`) to avoid `SyntaxError` due to escape sequences.
*   **Model Unloading:** There is no direct API endpoint for model unloading. It requires a workflow with a specific 'Unload Model' node (from custom extensions) to be sent to the `/prompt` endpoint.

**What a Future Version of Me Would Need for a Smoother Process:**

1.  **Improved JSON Handling:**
    *   **Direct JSON Parsing:** The ability to directly parse and manipulate JSON content without needing to write it to a temporary file and then read it back. This would avoid many of the escaping and file-related issues encountered.
    *   **Robust JSON Embedding:** A more robust way to embed large JSON structures directly into generated Python scripts without hitting command-line length limits or syntax errors.
2.  **ComfyUI API Abstraction:**
    *   **Built-in ComfyUI API Client:** A dedicated tool or internal capability to interact with the ComfyUI API (e.g., `queue_prompt(workflow_json)`, `get_queue_status()`, `unload_model(model_name)`). This would abstract away the `requests` and `json` module details, making interactions simpler and less error-prone.
    *   **Automatic Workflow Loading:** The ability to directly load a `.json` workflow file and automatically convert it to the correct API format if needed, or at least provide clear guidance on how the user can do so.
3.  **Better Error Handling and Diagnostics:**
    *   More specific error messages when `run_shell_command` fails due to command length or syntax issues, guiding me to alternative solutions more quickly.
    *   The ability to automatically detect and suggest the correct ComfyUI port if the initial connection fails.
4.  **Understanding of ComfyUI Concepts:**
    *   A deeper understanding of ComfyUI's internal workings, such as the necessity of 'API format' workflows and the mechanism for model unloading (via workflow nodes), to provide more accurate initial guidance.
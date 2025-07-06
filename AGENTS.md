# Project Context for Gemini

MythForgeProjectV3 is an AI CLI environment designed to automate, monitor, and control local AI services: KoboldCpp (text generation), ComfyUI (image synthesis), and SillyTavern (frontend). Gemini offloads micromanagement by executing, diagnosing, and repairing workflows via an Observer and a playbook system.


## Gemini’s Operational Context
- **Home Directory:**  
  `C:\Users\Ckrest\Documents\MythForgeProjectV3\Gemini` — full read/write/create/delete access.


## Project Overview
- **MythForgeProjectV3**
- **Purpose:** Centralized monitoring and control of AI services.  
- **Technologies:** Python, local shell commands, JSON-based IPC.  
- **Architecture:** Multi-subsystem unified by `Observer/observer.py`.


## Key Files
- `..\ComfyUI\`  
- `..\Koboldcpp\`  
- `..\SillyTavern\`  
- `..\Observer\observer.py`  
- `..\Observer\status.json`  
- `..\Observer\commands.json`  
- `gemini_playbooks.json`  
- `gemini_playbook_examples.md` ← detailed playbook reference


## Playbook Management
- **Playbook File:**  
  `gemini_playbooks.json`, organized by subsystem keys: `koboldcpp`, `comfyui`, `sillytavern`, `system`.

- **Search Before Action:**  
  On any task or error, search the relevant subsystem array for matching `tags` or `conditions`. If found, execute its `steps` exactly.


### Handling New Errors (The Learning Loop)
1. **Manual Intervention:** Diagnose and resolve the issue manually.  
2. **Document the Fix:** Once stable, create a new entry or edit the current entry in `gemini_playbooks.json` for that subsystem.  
3. **Create the Entry:** Include:
   - `task`
   - `tags`
   - `conditions`
   - `requierments`
   - `steps`
   - `observations`
4. **Append Under Subsystem:** Add the entry to the array for `koboldcpp`, `comfyui`, `sillytavern`, or `system`.  
5. **Failure Handling:** If an existing playbook entry fails:
   - Mark `last_result: "failure"` with timestamp  
   - Do **not** retry until manual review  
6. **Detailed Help:** Consult `gemini_playbook_examples.md` for concrete examples and templates.


## Usage
- **Read Status:** Read `Observer/status.json`.
- **Send Command:** Write one JSON object into `Observer/commands.json`, e.g.:
{"command":"restart_kobold"}

pgsql
Copy
Edit
Observer executes and clears the file.

## Session & Temp Files
- **Session Management:** Say “save session” to dump a summary into `past_sessions\{your_note}.md`.
- **Temp Files:** Use `Gemini\temp_files\`—auto-deleted when no longer needed.

## Debugging Guidelines
- **Monitored Execution:** For debugging purposes, all shell commands should be executed via the `monitor.bat` script located at `C:\Users\Ckrest\Documents\MythForgeProjectV3\Debugging\tools\monitor.bat`. This script logs output and ensures auto-termination.
  - **Usage:** `C:\Users\Ckrest\Documents\MythForgeProjectV3\Debugging\tools\monitor.bat <your_command_here>`

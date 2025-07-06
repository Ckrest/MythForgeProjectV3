import json
import os
import subprocess
import threading
import time
from datetime import datetime

# --- Configuration ---
# NOTE: Assumes this script is in the 'Observer' directory,
# and Koboldcpp, ComfyUI, etc., are in sibling directories.
# Adjust these paths if your directory structure is different.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KOBOLDCPP_PATH = os.path.join(BASE_DIR, 'Koboldcpp', 'koboldcpp.exe')
COMFYUI_PATH = os.path.join(BASE_DIR, 'ComfyUI', 'main.py') # Assuming comfy is run with python
SILLYTAVERN_PATH = os.path.join(BASE_DIR, 'SillyTavern', 'start.bat')

# Files for communication with the Gemini CLI
STATUS_FILE = os.path.join(os.path.dirname(__file__), 'status.json')
COMMAND_FILE = os.path.join(os.path.dirname(__file__), 'commands.json')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'observer.log')

# --- Global State ---
# This dictionary holds the real-time status of all monitored processes.
# It's the "single source of truth" that gets written to status.json.
process_status = {
    "observer": {
        "status": "running",
        "last_update": datetime.now().isoformat(),
        "pid": os.getpid()
    },
    "koboldcpp": {
        "status": "stopped",
        "pid": None,
        "last_output": "",
        "last_output_time": None,
        "start_time": None,
        "exit_code": None
    },
    "comfyui": {
        "status": "stopped",
        "pid": None,
        "last_output": "",
        "last_output_time": None,
        "start_time": None,
        "exit_code": None
    },
    "sillytavern": {
        "status": "stopped",
        "pid": None,
        "last_output": "",
        "last_output_time": None,
        "start_time": None,
        "exit_code": None
    }
}
process_objects = {
    "koboldcpp": None,
    "comfyui": None,
    "sillytavern": None
}

# Track whether a shutdown was requested for each process.
expected_shutdown = {
    "koboldcpp": False,
    "comfyui": False,
    "sillytavern": False
}

# --- Utility Functions ---

def log_message(message):
    """Writes a message to the console and the log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + '\n')

def update_status_file():
    """Atomically writes the current process_status to status.json."""
    process_status["observer"]["last_update"] = datetime.now().isoformat()
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(process_status, f, indent=4)
    except IOError as e:
        log_message(f"ERROR: Could not write to status file: {e}")

# --- Process Management ---

def start_process(name, command):
    """Starts a given process and updates its status."""
    if process_status[name]["status"] in ("running", "starting"):
        log_message(f"Process {name} is already running or starting.")
        return

    log_message(f"Attempting to start {name}...")
    try:
        # For .py files, we need to run them with python.
        if command.endswith('.py'):
            executable = [os.sys.executable, command]
        else:
            executable = [command]

        proc = subprocess.Popen(
            executable,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

        process_objects[name] = proc
        expected_shutdown[name] = False
        process_status[name].update({
            "status": "starting",
            "pid": proc.pid,
            "start_time": datetime.now().isoformat(),
            "exit_code": None
        })
        log_message(f"{name} started with PID: {proc.pid}")

        threading.Thread(target=monitor_output, args=(name, proc), daemon=True).start()
        threading.Thread(target=monitor_startup, args=(name, proc), daemon=True).start()

    except FileNotFoundError:
        log_message(f"ERROR: Command not found for {name}: {command}")
        process_status[name]["status"] = "error_not_found"
    except Exception as e:
        log_message(f"ERROR: Failed to start {name}: {e}")
        process_status[name]["status"] = "error_failed_to_start"

def stop_process(name):
    """Stops a given process by its name."""
    proc = process_objects.get(name)
    if proc and proc.poll() is None:
        expected_shutdown[name] = True
        log_message(f"Stopping {name} (PID: {proc.pid})...")
        try:
            subprocess.run(f"TASKKILL /F /T /PID {proc.pid}", check=True, capture_output=True)
            proc.wait(timeout=5)
            log_message(f"{name} stopped.")
        except subprocess.TimeoutExpired:
            log_message(f"WARNING: {name} did not terminate gracefully, forcing kill.")
            proc.kill()
        except Exception as e:
            log_message(f"ERROR: Could not stop {name}: {e}")

    process_status[name].update({
        "status": "stopped",
        "pid": None,
        "start_time": None,
        "exit_code": None
    })
    process_objects[name] = None
    expected_shutdown[name] = False


def monitor_output(name, proc):
    """
    Reads stdout from a process line-by-line in a separate thread.
    This is crucial for not blocking the main loop.
    """
    log_message(f"Started monitoring output for {name}.")
    for line in iter(proc.stdout.readline, ''):
        clean_line = line.strip()
        if clean_line:
            process_status[name]["last_output"] = clean_line
            process_status[name]["last_output_time"] = datetime.now().isoformat()
            log_message(f"[{name}] {clean_line}")

    proc.stdout.close()
    error_output = proc.stderr.read().strip()
    if error_output:
        log_message(f"[{name} ERROR] {error_output}")
        process_status[name]["last_output"] = error_output

    exit_code = proc.poll()
    process_status[name]["exit_code"] = exit_code

    if expected_shutdown[name]:
        log_message(f"{name} stopped with exit code {exit_code}")
        process_status[name]["status"] = "stopped"
    else:
        log_message(f"{name} crashed with exit code {exit_code}")
        process_status[name]["status"] = "crashed"

    process_status[name]["pid"] = None
    expected_shutdown[name] = False


def monitor_startup(name, proc, timeout=10):
    """Verify a process is still running after a short delay."""
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            # Process exited during startup
            exit_code = proc.returncode
            process_status[name].update({
                "status": "error_startup",
                "pid": None,
                "exit_code": exit_code
            })
            log_message(f"{name} failed to start. Exit code {exit_code}")
            return
        time.sleep(1)

    if process_status[name]["status"] == "starting":
        process_status[name]["status"] = "running"
        log_message(f"{name} startup verified.")


# --- Command Handling ---

def handle_command(command_obj):
    """Executes an action based on the command received."""
    command = command_obj.get("command")
    log_message(f"Received command: {command}")

    if command == "restart_kobold":
        stop_process("koboldcpp")
        time.sleep(2) # Give it a moment to release resources
        start_process("koboldcpp", KOBOLDCPP_PATH)
    elif command == "stop_kobold":
        stop_process("koboldcpp")
    elif command == "start_kobold":
        start_process("koboldcpp", KOBOLDCPP_PATH)

    elif command == "restart_comfyui":
        stop_process("comfyui")
        time.sleep(2)
        start_process("comfyui", COMFYUI_PATH)
    elif command == "stop_comfyui":
        stop_process("comfyui")
    elif command == "start_comfyui":
        start_process("comfyui", COMFYUI_PATH)

    elif command == "restart_sillytavern":
        stop_process("sillytavern")
        time.sleep(2)
        start_process("sillytavern", SILLYTAVERN_PATH)
    elif command == "stop_sillytavern":
        stop_process("sillytavern")
    elif command == "start_sillytavern":
        start_process("sillytavern", SILLYTAVERN_PATH)

    elif command == "status":
        # Just forces an immediate update of the status file
        update_status_file()
    elif command == "shutdown_all":
        stop_process("koboldcpp")
        stop_process("comfyui")
        stop_process("sillytavern")
    else:
        log_message(f"Unknown command: {command}")


def command_listener():
    """Periodically checks for and processes commands from commands.json."""
    log_message("Command listener started.")
    while True:
        try:
            if os.path.exists(COMMAND_FILE) and os.path.getsize(COMMAND_FILE) > 0:
                with open(COMMAND_FILE, 'r+') as f:
                    try:
                        command_obj = json.load(f)
                        handle_command(command_obj)
                        # Clear the file after processing
                        f.seek(0)
                        f.truncate()
                    except json.JSONDecodeError:
                        log_message("ERROR: commands.json is corrupted or empty. Clearing.")
                        f.seek(0)
                        f.truncate()
        except FileNotFoundError:
            # This is fine, it just means no command has been issued yet.
            pass
        except Exception as e:
            log_message(f"ERROR in command listener: {e}")

        time.sleep(2) # Check for commands every 2 seconds

# --- Main Execution ---

def main():
    """Main function to initialize and run the observer."""
    log_message("--- Gemini Observer Initializing ---")

    # Initial update to clear out any old data
    update_status_file()

    # Start the command listener in a separate thread
    cmd_thread = threading.Thread(target=command_listener, daemon=True)
    cmd_thread.start()

    # Initial startup of all services
    log_message("Performing initial startup of all services...")
    start_process("koboldcpp", KOBOLDCPP_PATH)
    time.sleep(1) # Stagger startups slightly
    start_process("comfyui", COMFYUI_PATH)
    time.sleep(1)
    start_process("sillytavern", SILLYTAVERN_PATH)

    # Main loop to keep the script alive and update the status file
    try:
        while True:
            update_status_file()
            time.sleep(5) # Update status file every 5 seconds
    except KeyboardInterrupt:
        log_message("--- Shutdown signal received ---")
    finally:
        log_message("Stopping all monitored processes...")
        stop_process("koboldcpp")
        stop_process("comfyui")
        stop_process("sillytavern")
        update_status_file() # Final status update
        log_message("--- Gemini Observer Shutdown Complete ---")


if __name__ == "__main__":
    main()

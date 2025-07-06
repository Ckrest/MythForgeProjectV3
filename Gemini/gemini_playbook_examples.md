# Gemini Playbook Examples

This file provides concrete, machine-readable playbook entries organized by subsystem.  
Use it when you need step-by-step guidance or to seed `gemini_playbooks.json`.

## koboldcpp

### Restart After Memory Spike
- **Tags:** restart, memory, crash  
- **Conditions:** memory >6GB, no output for 30s  
- **Steps:**
  1. kill koboldcpp.exe
  2. wait 2
  3. start koboldcpp.exe
- **Observations:** memory stabilizes at ~1.3GB

## comfyui

### Fix UI Freeze During Batch
- **Tags:** freeze, batch, restart  
- **Conditions:** no log update >15s, stuck on "executing node"  
- **Steps:**
  1. kill comfyui.exe
  2. rm -rf comfyui\temp\*
  3. start comfyui.exe
- **Observations:** batch completes without hang

## sillytavern

### Resolve Socket Stall
- **Tags:** stall, frontend  
- **Conditions:** no chat output, UI active  
- **Steps:**
  1. kill SillyTavern process
  2. restart SillyTavern
- **Observations:** chat responds normally

## system

### Recover Corrupted status.json
- **Tags:** observer, json, corrupt  
- **Conditions:** parse error on status.json  
- **Steps:**
  1. rename status.json to status_broken_TIMESTAMP.json
  2. restart observer.py
- **Observations:** new valid status.json generated

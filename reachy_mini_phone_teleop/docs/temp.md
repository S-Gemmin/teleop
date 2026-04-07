# Reachy Mini Phone Teleop - Action & Controller Documentation

## Overview

This document describes how to use `actions.py` and `controller.py` for the Reachy Mini phone teleoperation system.

## Important: Action Safety

**YOU MUST USE `play_category()` FOR ALL ANIMATIONS**

There is no lock protecting individual actions from being called concurrently. If you call `nod()`, `shake()`, or any other action directly while another action is running, you risk race conditions and undefined behavior.

Always use `play_category()` which uses an internal lock (`_action_lock`) to prevent concurrent execution:

```python
from reachy_mini_phone_teleop.actions import play_category

play_category(mini, "YES")  # Plays a random YES animation
play_category(mini, "NO")   # Plays a random NO animation
```

## Available Categories

Use these category names with `play_category()`:

| Category | Description | Animations |
|----------|-------------|-------------|
| `"LIMP"` | Disables motors temporarily | (built-in) |
| `"YES"` | Nodding animations | `yes1`, `yes_sad1` |
| `"NO"` | Head shaking animations | `no1`, `no_excited1`, `no_sad1` |
| `"RESET"` | Reset to home position | (built-in) |
| `"CONFUSED"` | Confused/lost expressions | `confused1`, `lost1`, `uncertain1`, `curious1` |
| `"WOW"` | Surprised expressions | `surprised1`, `surprised2` |
| `"HAPPY"` | Happy/cheerful animations | `success1`, `cheerful1`, `enthusiastic1` |
| `"SAD"` | Sad/fearful animations | `sad1`, `fear1`, `scared1` |
| `"ALIGN"` | Align body to head | (built-in) |
| `"LAUGH"` | Laughing animations | `laughing1`, `laughing2` |

### Special Categories

- `"LIMP"`: Disables motors for 3 seconds, then re-enables
- `"RESET"`: Returns to neutral pose
- `"ALIGN"`: Rotates body to match current head yaw

## Message Format

The controller expects messages from the phone app in this format:

```python
{
    "head": [roll, pitch, yaw],           # Head rotation (optional)
    "antennas": [right, left],             # Antenna positions (optional)
    "turnLeft": bool,                      # Turn body left (optional)
    "turnRight": bool,                     # Turn body right (optional)
    "rightJoystickInput": bool,            # Right joystick active (optional)
    "leftJoystickInput": bool,             # Left joystick active (optional)
}
```

### Field Details

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `head` | list[float] | -1.0 to 1.0 | [roll, pitch, yaw] - scaled by `ROTATION_SCALE` |
| `antennas` | list[float] | -180 to 180 degrees | [right, left] antenna angles |
| `turnLeft` | bool | - | Enable left turn |
| `turnRight` | bool | - | Enable right turn |
| `rightJoystickInput` | bool | - | Enable right antenna control |
| `leftJoystickInput` | bool | - | Enable left antenna control |

## Controller Usage

```python
from reachy_mini_phone_teleop.controller import TeleopController

controller = TeleopController(logger=logger)

# In your main loop:
controller.update(mini)  # Apply current state to robot

# When receiving a message from phone:
controller.process_message(message)
```

## Example: Handling Action Requests

```python
def handle_message(message: dict):
    # Check for action requests
    if "action" in message:
        category = message["action"]
        play_category(mini, category)
        return
    
    # Otherwise, pass to controller for continuous control
    controller.process_message(message)
```

## Checking if Action is Running

```python
from reachy_mini_phone_teleop.actions import is_action_running

if is_action_running():
    # Don't start a new action
    pass
```

## Architecture

1. **controller.py**: Handles continuous teleoperation (head rotation, antenna control, body turning). Uses a lock for thread-safe state updates.

2. **actions.py**: Handles discrete animations. Uses `_action_lock` to prevent concurrent animations. All animations should go through `play_category()`.
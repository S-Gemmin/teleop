# Reachy Mini Phone Teleop

## actions.py - Playing Animations

Use `play_category()` to play animations (handles thread locking automatically):

```python
from reachy_mini import ReachyMini
from reachy_mini_phone_teleop.actions import play_category

with ReachyMini() as mini:
    play_category(mini, "YES")
    play_category(mini, "NO")
    play_category(mini, "WAVE")
    play_category(mini, "HAPPY")
    play_category(mini, "SAD")
    play_category(mini, "CONFUSED")
    play_category(mini, "WOW")
    play_category(mini, "LAUGH")
    play_category(mini, "LIMP")
    play_category(mini, "RESET")
    play_category(mini, "ALIGN")
```

---

## controller.py - Processing Phone Input

### Message Format

| Key | Type | Description |
|-----|------|-------------|
| `head` | list[3] | [roll, pitch, yaw] in radians |
| `antennas` | list[2] | [right, left] antenna positions |
| `turnLeft` | bool | turn body left |
| `turnRight` | bool | turn body right |
| `rightJoystickInput` | bool | right joystick active |
| `leftJoystickInput` | bool | left joystick active |

### Usage

```python
from reachy_mini import ReachyMini
from reachy_mini_phone_teleop.controller import TeleopController

controller = TeleopController()
# On message received:
controller.process_message(message)
# In control loop:
controller.update(mini)

# Pause teleop during animation:
controller.action_running = True
play_category(mini, "HAPPY")
controller.action_running = False
```

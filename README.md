### Reachy Mini Phone Teleop
#### Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m reachy_mini_phone_teleop.main
```

#### Sim
```
# Make sure other terminal you run daemon w/ the --sim arg
python -m reachy_mini_phone_teleop.main --sim
```

For IOS, make sure to use Safari!!!

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

# Python: Garmin Connect

> **Note:** Garmin has made significant changes to their authentication and API infrastructure.
> The old `garth`-based OAuth/cookie login no longer works. This library now authenticates
> using the same mobile SSO flow as the official Garmin Connect Android app, obtaining native
> DI OAuth Bearer tokens. Saved tokens are stored in a new format (`garmin_tokens.json`) —
> a fresh login is required after upgrading.
> All existing API methods remain unchanged — no code changes needed on your end,
> except when you store/handle tokens in your own project.

The Garmin Connect API library comes with two examples:

- **`example.py`** - Simple getting-started example showing authentication, token storage, and basic API calls
- **`demo.py`** - Comprehensive demo providing access to **130+ API methods** organized into **13 categories** for easy navigation

```bash
$ ./demo.py
🏃‍♂️ Full-blown Garmin Connect API Demo - Main Menu
==================================================
Select a category:

  [1] 👤 User & Profile
  [2] 📊 Daily Health & Activity
  [3] 🔬 Advanced Health Metrics
  [4] 📈 Historical Data & Trends
  [5] 🏃 Activities & Workouts
  [6] ⚖️ Body Composition & Weight
  [7] 🏆 Goals & Achievements
  [8] ⌚ Device & Technical
  [9] 🎽 Gear & Equipment
  [0] 💧 Hydration & Wellness
  [a] 🔧 System & Export
  [b] 📅 Training plans
  [c] ⛳ Golf

  [q] Exit program

Make your selection:
```

## API Coverage Statistics

- **Total API Methods**: 130+ unique endpoints (snapshot)
- **Categories**: 13 organized sections
- **User & Profile**: 4 methods (basic user info, settings)
- **Daily Health & Activity**: 9 methods (today's health data)
- **Advanced Health Metrics**: 12 methods (fitness metrics, HRV, VO2, training readiness, running tolerance)
- **Historical Data & Trends**: 9 methods (date range queries, weekly aggregates)
- **Activities & Workouts**: 35 methods (comprehensive activity, workout management, typed workout uploads, scheduling, import)
- **Body Composition & Weight**: 8 methods (weight tracking, body composition)
- **Goals & Achievements**: 15 methods (challenges, badges, goals)
- **Device & Technical**: 7 methods (device info, settings)
- **Gear & Equipment**: 7 methods (gear management, tracking)
- **Hydration & Wellness**: 12 methods (hydration, nutrition, blood pressure, menstrual)
- **System & Export**: 4 methods (reporting, logout, GraphQL)
- **Training Plans**: 2 methods
- **Golf**: 3 methods (scorecard summary, scorecard detail, shot data)

### Interactive Features

- **Enhanced User Experience**: Categorized navigation with emoji indicators
- **Smart Data Management**: Interactive weigh-in deletion with search capabilities
- **Comprehensive Coverage**: All major Garmin Connect features are accessible
- **Error Handling**: Robust error handling with user-friendly prompts
- **Data Export**: JSON export functionality for all data types

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

A comprehensive Python3 API wrapper for Garmin Connect, providing access to health, fitness, and device data.

## 📖 About

This library enables developers to programmatically access Garmin Connect data including:

- **Health Metrics**: Heart rate, sleep, stress, body composition, SpO2, HRV
- **Activity Data**: Workouts, typed workout uploads (running, cycling, swimming, walking, hiking), workout scheduling, exercises, training status, performance metrics, import-style uploads (no Strava re-export)
- **Nutrition**: Daily food logs, meals, and nutrition settings
- **Golf**: Scorecard summaries, scorecard details, shot-by-shot data
- **Device Information**: Connected devices, settings, alarms, solar data
- **Goals & Achievements**: Personal records, badges, challenges, race predictions
- **Historical Data**: Trends, progress tracking, date range queries

Compatible with all Garmin Connect accounts. See <https://connect.garmin.com/>

## 📦 Installation

Install from PyPI:

```bash
pip install --upgrade garminconnect curl_cffi
```

## Run demo software (recommended)

```bash
python3 -m venv .venv --copies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install pdm
pdm install --group :example

# Run the simple example
python3 ./example.py

# Run the comprehensive demo
python3 ./demo.py
```


## 🛠️ Development

Set up a development environment for contributing:

> **Note**: This project uses [PDM](https://pdm.fming.dev/) for modern Python dependency management and task automation. All development tasks are configured as PDM scripts in `pyproject.toml`. The Python interpreter is automatically configured to use `.venv/bin/python` when you create the virtual environment.

**Environment Setup:**

> **⚠️ Important**: On externally-managed Python environments (like Debian/Ubuntu), you must create a virtual environment before installing PDM to avoid system package conflicts.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv --copies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install PDM (Python Dependency Manager)
pip install pdm

# 3. Install all development dependencies
pdm install --group :all

# 4. Install optional tools for enhanced development experience
pip install "black[jupyter]" codespell pre-commit

# 5. Setup pre-commit hooks (optional)
pre-commit install --install-hooks
```

**Alternative for System-wide PDM Installation:**
```bash
# Install PDM via pipx (recommended for system-wide tools)
python3 -m pip install --user pipx
pipx install pdm

# Then proceed with project setup
pdm install --group :all
```

**Available Development Commands:**
```bash
pdm run format      # Auto-format code (isort, black, ruff --fix)
pdm run lint        # Check code quality (isort, ruff, black, mypy)
pdm run codespell   # Check spelling errors (install codespell if needed)
pdm run test        # Run test suite
pdm run testcov     # Run tests with coverage report
pdm run all         # Run all checks
pdm run clean      # Clean build artifacts and cache files
pdm run build      # Build package for distribution
pdm run publish    # Build and publish to PyPI
```

**View all available commands:**
```bash
pdm run --list     # Display all available PDM scripts
```

**Code Quality Workflow:**
```bash
# Before making changes
pdm run lint       # Check current code quality

# After making changes
pdm run format     # Auto-format your code
pdm run lint       # Verify code quality
pdm run codespell  # Check spelling
pdm run test       # Run tests to ensure nothing broke
```

Run these commands before submitting PRs to ensure code quality standards.

## 🔐 Authentication

Authentication uses the same mobile SSO flow as the official Garmin Connect Android app.
No browser is needed.

**How it works:**

1. **First login**: Authenticates via `sso.garmin.com/mobile/api/login` using the Android
   app's client ID. If MFA is required, a callback (`prompt_mfa`) prompts for the one-time code.
2. **Token exchange**: The service ticket is exchanged for DI OAuth Bearer tokens
   (`access_token` + `refresh_token`) via `diauth.garmin.com`. Tokens are stored at
   `~/.garminconnect/garmin_tokens.json`.
3. **Auto-refresh**: Before each API request the library checks whether the DI token is about
   to expire and refreshes it automatically — no user interaction required.

**Session lifetime:**
- DI tokens auto-refresh indefinitely as long as the refresh token remains valid.
- A full re-login with credentials (and possibly MFA) is only needed if the refresh token
  itself expires or is revoked.

**Token storage:**
```bash
~/.garminconnect/garmin_tokens.json   # saved automatically, mode 0600
```

## 🧪 Testing

**Prerequisites:**

Run `example.py` once to create saved tokens in `~/.garminconnect`.

```bash
# Install development dependencies
pdm install --group :all
```

**Run Tests:**

```bash
pdm run test        # Run all tests
pdm run testcov     # Run tests with coverage report
```

Optional: keep test tokens isolated

```bash
export GARMINTOKENS="$(mktemp -d)"
python3 ./example.py   # create a fresh token file for tests
pdm run test
```

**Note:** Tests use VCR cassettes to record/replay API responses. If tests fail with
authentication errors, ensure valid tokens exist in `~/.garminconnect` (run
`example.py` first).

## 📦 Publishing

For package maintainers:

**Setup PyPI credentials:**

```bash
pip install twine
# Edit with your preferred editor, or create via here-doc:
# cat > ~/.pypirc <<'EOF'
# [pypi]
# username = __token__
# password = <PyPI_API_TOKEN>
# EOF
```

```ini
[pypi]
username = __token__
password = <PyPI_API_TOKEN>
```

Recommended: use environment variables and restrict file perms

```bash
chmod 600 ~/.pypirc
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="<PyPI_API_TOKEN>"
```

**Publish new version:**

```bash
pdm run publish    # Build and publish to PyPI
```

**Alternative publishing steps:**

```bash
pdm run build      # Build package only
pdm publish        # Publish pre-built package
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- **Report Issues**: Bug reports and feature requests via GitHub issues
- **Submit PRs**: Code improvements, new features, documentation updates
- **Testing**: Help test new features and report compatibility issues
- **Documentation**: Improve examples, add use cases, fix typos

**Before Contributing:**
1. Set up development environment (`pdm install --group :all`)
2. Execute code quality checks (`pdm run format && pdm run lint`)
3. Test your changes (`pdm run test`)
4. Follow existing code style and patterns

**Development Workflow:**
```bash
# 1. Setup environment (with virtual environment)
python3 -m venv .venv --copies
source .venv/bin/activate
pip install pdm
pdm install --group :all

# 2. Make your changes
# ... edit code ...

# 3. Quality checks
pdm run format     # Auto-format code
pdm run lint       # Check code quality
pdm run test       # Run tests

# 4. Submit PR
git commit -m "Your changes"
git push origin your-branch
```

### Jupyter Notebook

Explore the API interactively with our [reference notebook](https://github.com/cyberjunky/python-garminconnect/blob/master/docs/reference.ipynb).

### Python Code Examples

```python
import os
from datetime import date
from garminconnect import Garmin

# First run: logs in and saves tokens to ~/.garminconnect
# Subsequent runs: loads saved tokens and auto-refreshes
client = Garmin(
    os.getenv("EMAIL"),
    os.getenv("PASSWORD"),
    prompt_mfa=lambda: input("MFA code: "),
)
client.login("~/.garminconnect")

# Get today's stats
today = date.today().isoformat()
stats = client.get_stats(today)

# Get heart rate data
hr_data = client.get_heart_rates(today)
print(f"Resting HR: {hr_data.get('restingHeartRate', 'n/a')}")
```

### Typed Workouts (Pydantic Models)

The library includes optional typed workout models for creating type-safe workout definitions:

```bash
pip install garminconnect[workout]
```

```python
from garminconnect.workout import (
    RunningWorkout, WorkoutSegment,
    create_warmup_step, create_interval_step, create_cooldown_step,
    create_repeat_group,
)

# Create a structured running workout
workout = RunningWorkout(
    workoutName="Easy Run",
    estimatedDurationInSecs=1800,
    workoutSegments=[
        WorkoutSegment(
            segmentOrder=1,
            sportType={"sportTypeId": 1, "sportTypeKey": "running"},
            workoutSteps=[create_warmup_step(300.0)]
        )
    ]
)

# Upload and optionally schedule it
result = client.upload_running_workout(workout)
client.schedule_workout(result["workoutId"], "2026-03-20")

# Delete a workout or remove it from the calendar
client.delete_workout(workout_id)
client.unschedule_workout(scheduled_workout_id)
```

**Available workout classes:** `RunningWorkout`, `CyclingWorkout`, `SwimmingWorkout`, `WalkingWorkout`, `HikingWorkout`, `MultiSportWorkout`, `FitnessEquipmentWorkout`

**Helper functions:** `create_warmup_step`, `create_interval_step`, `create_recovery_step`, `create_cooldown_step`, `create_repeat_group`

### Additional Resources
- **Simple Example**: [example.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/example.py) - Getting started guide
- **Comprehensive Demo**: [demo.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/demo.py) - All 130+ API methods
- **API Documentation**: Comprehensive method documentation in source code
- **Test Cases**: Real-world usage examples in `tests/` directory

## 🙏 Acknowledgments

Special thanks to all contributors who have helped improve this project:

- **Community Contributors**: Bug reports, feature requests, and code improvements
- **Issue Reporters**: Helping identify and resolve compatibility issues
- **Feature Developers**: Adding new API endpoints and functionality
- **Documentation Authors**: Improving examples and user guides

This project thrives thanks to community involvement and feedback.

## 💖 Support This Project

If you find this library useful for your projects, please consider supporting its continued development and maintenance:

### 🌟 Ways to Support

- **⭐ Star this repository** - Help others discover the project
- **💰 Financial Support** - Contribute to development and hosting costs
- **🐛 Report Issues** - Help improve stability and compatibility
- **📖 Spread the Word** - Share with other developers

### 💳 Financial Support Options

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

**Why Support?**
- Keeps the project actively maintained
- Enables faster bug fixes and new features
- Supports infrastructure costs (testing, AI, CI/CD)
- Shows appreciation for hundreds of hours of development

Every contribution, no matter the size, makes a difference and is greatly appreciated! 🙏

[releases-shield]: https://img.shields.io/github/release/cyberjunky/python-garminconnect.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/python-garminconnect/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/python-garminconnect.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/python-garminconnect/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/python-garminconnect.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-cyberjunky-blue.svg?style=for-the-badge

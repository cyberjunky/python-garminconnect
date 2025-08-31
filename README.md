# Python: Garmin Connect

The Garmin Connect API demo (`example.py`) provides comprehensive access to **101 API methods** organized into **11 categories** for easy navigation:

```bash
$ ./example.py
🏃‍♂️ Garmin Connect API Demo - Main Menu
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

  [q] Exit program

Make your selection: 
```

### API Coverage Statistics

- **Total API Methods**: 101 unique endpoints
- **Categories**: 11 organized sections
- **User & Profile**: 4 methods (basic user info, settings)
- **Daily Health & Activity**: 8 methods (today's health data)
- **Advanced Health Metrics**: 10 methods (fitness metrics, HRV, VO2)
- **Historical Data & Trends**: 6 methods (date range queries)
- **Activities & Workouts**: 20 methods (comprehensive activity management)
- **Body Composition & Weight**: 8 methods (weight tracking, body composition)
- **Goals & Achievements**: 15 methods (challenges, badges, goals)
- **Device & Technical**: 7 methods (device info, settings)
- **Gear & Equipment**: 6 methods (gear management, tracking)
- **Hydration & Wellness**: 9 methods (hydration, blood pressure, menstrual)
- **System & Export**: 4 methods (reporting, logout, GraphQL)

### Interactive Features

- **Enhanced User Experience**: Categorized navigation with emoji indicators
- **Smart Data Management**: Interactive weigh-in deletion with search capabilities
- **Comprehensive Coverage**: All major Garmin Connect features accessible
- **Error Handling**: Robust error handling and user-friendly prompts
- **Data Export**: JSON export functionality for all data types

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

A comprehensive Python 3 API wrapper for Garmin Connect, providing access to health, fitness, and device data.

## 📖 About

This library enables developers to programmatically access Garmin Connect data including:

- **Health Metrics**: Heart rate, sleep, stress, body composition, SpO2, HRV
- **Activity Data**: Workouts, exercises, training status, performance metrics  
- **Device Information**: Connected devices, settings, alarms, solar data
- **Goals & Achievements**: Personal records, badges, challenges, race predictions
- **Historical Data**: Trends, progress tracking, date range queries

Compatible with all Garmin Connect accounts. See <https://connect.garmin.com/>

## 📦 Installation

Install from PyPI:

```bash
pip3 install garminconnect
```

## Run demo software (recommended)

```
python3 -m venv .venv --copies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install pdm
pdm install --group :example
./example.py
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
pip install pdm "black[jupyter]" codespell

# 3. Install all development dependencies
pdm install --group :all

# 4. Install pre-commit hooks (optional)
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

The library uses the same OAuth authentication as the official Garmin Connect app via [Garth](https://github.com/matin/garth).

**Key Features:**
- Login credentials valid for one year (no repeated logins)
- Secure OAuth token storage 
- Same authentication flow as official app

**Advanced Configuration:**
```python
# Optional: Custom OAuth consumer (before login)
import garth
garth.sso.OAUTH_CONSUMER = {'key': 'your_key', 'secret': 'your_secret'}
```

**Token Storage:**
Tokens are automatically saved to `~/.garminconnect` directory for persistent authentication.

## 🧪 Testing

Run the test suite to verify functionality:

**Prerequisites:**

Create tokens in ~/.garminconnect by running the example program.

```bash
# Install development dependencies
pdm install --group :all
```

**Run Tests:**
```bash
pdm run test        # Run all tests
pdm run testcov     # Run tests with coverage report
```

**Note:** Tests automatically use `~/.garminconnect` as the default token file location. You can override this by setting the `GARMINTOKENS` environment variable. Run `example.py` first to generate authentication tokens for testing.

## 📦 Publishing

For package maintainers:

## 📦 Publishing

For package maintainers:

**Setup PyPI credentials:**
```bash
pip install twine
vi ~/.pypirc
```
```ini
[pypi]
username = __token__
password = <PyPI_API_TOKEN>
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
Explore the API interactively with our [reference notebook](https://github.com/cyberjunky/python-garminconnect/blob/master/reference.ipynb).

### Python Code Examples
```python
from garminconnect import Garmin

# Initialize and login
client = Garmin('your_email', 'your_password')
client.login()

# Get today's stats
stats = client.get_stats('2023-08-31')
print(f"Steps: {stats['totalSteps']}")

# Get heart rate data
hr_data = client.get_heart_rates('2023-08-31')
print(f"Resting HR: {hr_data['restingHeartRate']}")
```

### Additional Resources
- **Source Code**: [example.py](https://raw.githubusercontent.com/cyberjunky/python-garminconnect/master/example.py)
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

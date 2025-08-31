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

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)

A comprehensive Python 3 API wrapper for Garmin Connect, providing access to health, fitness, and device data.

## About

This library enables developers to programmatically access Garmin Connect data including:

- **Health Metrics**: Heart rate, sleep, stress, body composition, SpO2, HRV
- **Activity Data**: Workouts, exercises, training status, performance metrics  
- **Device Information**: Connected devices, settings, alarms, solar data
- **Goals & Achievements**: Personal records, badges, challenges, race predictions
- **Historical Data**: Trends, progress tracking, date range queries

Compatible with all Garmin Connect accounts. See <https://connect.garmin.com/>

## Installation

Install from PyPI:

```bash
pip3 install garminconnect
```

## Authentication

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

## Testing

Run the test suite to verify functionality:

**Prerequisites:**
```bash
# Set token directory (uses example.py credentials)
export GARMINTOKENS=~/.garminconnect

# Install pytest (if needed)
sudo apt install python3-pytest
```

**Run Tests:**
```bash
make install-test
make test
```

**Note:** Test files use credential tokens created by `example.py`, so run the example script first to generate authentication tokens.

## Development

Set up a development environment for contributing:

**Environment Setup:**
```bash
make .venv
source .venv/bin/activate

pip3 install pdm ruff
pdm init
```

**Development Tools:**
```bash
# Install code quality tools
sudo apt install pre-commit isort black mypy
pip3 install pre-commit
```

**Code Quality Checks:**
```bash
make format    # Format code
make lint      # Lint code  
make codespell # Check spelling
```

Run these commands before submitting PRs to ensure code quality standards.

## Publishing

For package maintainers:

**Setup PyPI credentials:**
```bash
sudo apt install twine
vi ~/.pypirc
```
```ini
[pypi]
username = __token__
password = <PyPI_API_TOKEN>
```

**Publish new version:**
```bash
make publish
```

## Contributing

We welcome contributions! Here's how you can help:

- **Report Issues**: Bug reports and feature requests via GitHub issues
- **Submit PRs**: Code improvements, new features, documentation updates  
- **Testing**: Help test new features and report compatibility issues
- **Documentation**: Improve examples, add use cases, fix typos

**Before Contributing:**
1. Run development setup (`make .venv`)
2. Execute code quality checks (`make format lint codespell`) 
3. Test your changes (`make test`)
4. Follow existing code style and patterns

## Usage Examples

### Interactive Demo
Run the comprehensive API demonstration:
```bash
pip3 install -r requirements-dev.txt
./example.py
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

## Acknowledgments

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

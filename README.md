# PyVersionTracker

PyVersionTracker is a Python utility for tracking and managing Python versions. It provides functionality to fetch and parse information about Python releases from the official [Official Python](https://www.python.org/downloads).

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
  - [Retrieving the Latest Version](#retrieving-the-latest-version)
  - [Retrieving All Versions](#retrieving-all-versions)
  - [Retrieving Active Versions](#retrieving-active-versions)
  - [Retrieving Unsupported Versions](#retrieving-unsupported-versions)
  - [Validating a Version](#validating-a-version)
  - [Check if a Version is Deprecated](#check-if-a-version-is-deprecated)
  - [Check if a Version is Within a Specified Range](#check-if-a-version-is-within-a-specified-range)
  - [Check if a system meets the required minimum python version](#check-if-a-system-meets-the-required-minimum-python-version)
- [Requirements](#requirements)
- [Author](#author)
- [Version](#version)

## Installation

To use PyVersionTracker in your Python project, you can install it via pip. Open your terminal or command prompt and run the following command:
```bash
pip install py-version-tracker
```

## Features

- **Version Checker: Ensures System Compatibility**
  - Verify if the current Python version meets the specified minimum requirements in real-time, ensuring optimal functionality.
  - Defaults to the minimum version obtained from [Official Python](https://www.python.org/downloads)

- **Version Information Retrieval: Stay Updated**
  - Fetch details about the latest Python version and comprehensive information regarding stable and active versions.

- **Validation: Ensuring Correct Format**
  - Validate and verify the format of Python version strings, providing confidence in the accuracy of the input.

- **Deprecation Check: Identify Deprecated Versions**
  - Identify whether a specific Python version is deprecated, allowing proactive management of software versions.

- **Version Range: Flexible Versioning**
  - Obtain a range of Python versions based on a specified version, facilitating compatibility assessments and version range queries.
---

## Usage
```python
from py_version_tracker import PyVersionTracker
```
### Retrieving the Latest Version

You can use the `latest_version` property to retrieve the latest Python version available for download.

```python
tracker = PyVersionTracker()
latest_version = tracker.latest_version
print(f"The latest Python version is: {latest_version}")
```
---

### Retrieving All Versions

You can use the `all_versions` property to retrieve all available Python versions.

```python
tracker = PyVersionTracker()
all_versions = list(tracker.all_versions)
print("All available Python versions:")
for version in all_versions:
    print(version)
```
---

### Retrieving Active Versions

You can use the `active_versions` method to retrieve active Python versions along with their status, start date, end date, and schedule.

```python
tracker = PyVersionTracker()
active_versions = list(tracker.active_versions())
print("Active Python versions:")
for version in active_versions:
    print(version)
```
---

### Retrieving Unsupported Versions

You can use the `unsupported_versions` method to identify unsupported Python versions.

```python
# Identify all unsupported versions
unsupported = list(PyVersionTracker.unsupported_versions())
print("Unsupported Python versions:")
for version in unsupported:
    print(version)
```
---

### Validating a Version

You can use the `is_version` method to validate a given Python version.

```python
valid_version = "3.8.1"
is_valid = PyVersionTracker.is_version(valid_version)
print(f"Is {valid_version} a valid Python version? {is_valid}")
```


### Check if a version is deprecated
You can use the `is_deprecated` method to identify deprecated Python versions.
```python
# Check if a version is deprecated
version_to_check = '2.8.0'
if py_version_tracker.is_deprecated(version_to_check):
    print(f'The Python version {version_to_check} is deprecated.')
```

### Check if a version is within a specified range
You can use the `version_range` method to identify deprecated Python versions.
```python
# Check if a version is within a specified range
target_version = '3.0.1'
version_range = py_version_tracker.version_range(target_version, above=True)
print(f'Python versions above {target_version}: {version_range}')
```
---

### Check if a system meets the required minimum python version
You can use the `version_checker` method.
```python
py_version_tracker.version_checker(sys.version, minimum_version='3.8')
```

## Requirements

- Python 3.8+
- aiohttp
- beautifulsoup4

## Author

Yousef Abuzahrieh
Email: yousef.zahrieh17@gmail.com

## Version

0.0.1

---
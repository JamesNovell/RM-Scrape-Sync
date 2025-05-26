# SMB Toolkit - Log Collection Utility

## Overview

This project is a Python-based tool designed to connect to remote SMB shares, retrieve log files, and extract identifying information like serial numbers. It supports features like date filtering, regex-based filename matching, and temporary storage for local analysis.

## Purpose

The goal of this project is to evolve into a **modular**, **maintainable**, and **professional-grade** logging utility that adheres to Python best practices and is easy to scale for additional features.

## Current Features

* Connect to SMB shares with fallback credentials
* Download files with date and regex filters
* Extract serial numbers from the latest log files
* Temporary file handling and cleanup
* Command-line interface with `argparse`

## In Progress

This project is being actively refactored toward the following intended structure:

```
smb_toolkit/
│
├── smb_toolkit/                  # Core package
│   ├── __init__.py
│   ├── cli.py                    # Argument parsing & CLI
│   ├── runner.py                 # Task orchestration
│   ├── smb_utils.py              # SMB connection abstraction
│   ├── log_parser.py             # File parsing logic
│   └── config.py                 # Constants and defaults
│
├── tasks/                        # High-level operational flows
│   └── log_download.py
│
├── tests/                        # Unit tests
│   └── test_log_parser.py
│
├── requirements.txt              # Dependencies
├── pyproject.toml                # (optional) Build metadata
├── README.md                     # Project overview
└── main.py                       # Entry point
```

## Future Plans

* Add unit tests for SMB logic and parsing
* Implement a plugin system for new device types
* Support multiple share types and platforms
* Convert to `click` or `typer` for richer CLI
* Provide Docker support or PyInstaller packaging

## Usage Example (WIP)

```bash
python main.py \
  --ip 192.168.1.100 \
  --user TIDEL\\Tservice \
  --regex "^Log_.*\\.zip$" \
  --days-back 3
```

## Author Notes

This is a work in progress toward a professional-grade utility, with refactoring in progress to separate universal logic from application-specific logic.

Contributions, structure feedback, or extensions are welcome!

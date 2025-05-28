## 📦 Python Utilities Toolkit

### Overview

This repository contains a modular collection of **Python-based utility tools**, originally focused on SMB log retrieval and now expanding toward a broader set of **system operations**, **file parsing**, and **automation** tasks. The goal is to create a **reusable toolkit** for internal engineering and infrastructure workflows.

---

### Purpose

The repo is evolving into a **multi-purpose utility suite** with professional structure and Python best practices. It aims to serve as a foundation for:

* System administration automation
* Log extraction and analysis
* Environment-specific tool development
* General internal scripting needs

---

### Current Features

* Fetch VPN IPs for devices from a remote management system
* Connect to SMB shares using multiple credentials
* Retrieve and filter log files by date and pattern
* Extract serial numbers and odometer-like data from reports
* Run via CLI with automatic fallback behavior
* Uses `argparse` with optional serial overrides

---

### Repository Layout (Planned)

```
my_utils/
│
├── RM_scraper.py                # VPN portal interaction
├── smb_utils.py                 # SMB connection logic
├── log_parser.py                # File parsing and serial extraction
├── odo_fetch.py                 # Entry script for pulling device logs
├── runner.py                    # Orchestrator (optional future split)
│
├── tests/                       # (Optional) Unit tests
│
├── requirements.txt
├── README.md
```

---

### Future Goals

* Standardize all tools into callable CLI modules
* Migrate to `typer` or `click` for better CLI UX
* Add test coverage for all utilities
* Integrate `.env` loading for flexible configuration
* Add additional utilities (e.g., remote config pull, health checks)

---

### Example Usage

```bash
python odo_fetch.py             # Uses default serial
python odo_fetch.py N4R99999    # Uses a specific serial
```

---

### Author Notes

This is a work in progress toward a professional-grade internal toolkit. Contributions, ideas for structural improvements, and additional modules are welcome.

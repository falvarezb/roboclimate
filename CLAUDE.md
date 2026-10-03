# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Roboclimate evaluates the accuracy of meteorological weather forecast models by comparing actual OpenWeather API measurements against forecasts across 10 global cities and 5 weather variables (temperature, pressure, humidity, wind speed, wind direction).

## Commands

**Tests:**
```bash
pytest --cov-branch --cov-report html --cov=roboclimate tests/
```

Run a single test file:
```bash
pytest tests/metrics_test.py
```

**Linting:**
```bash
pylint roboclimate/
```

**Type checking:**
```bash
mypy roboclimate/
```

**Streamlit dashboard:**
```bash
streamlit run roboclimate/streamlit_app.py
```

**Java data analysis module** (in `roboclimate/data_analysis/`):
```bash
javac -source 22 --enable-preview -d out src/roboclimate/*.java
java --enable-preview -cp out roboclimate.Main
```

**Terraform deployment** (in `terraform/`):
```bash
./artifact_prep.sh        # build Lambda deployment packages
terraform apply -var-file ../secrets.tfvars
```

**Before any `terraform plan`/`apply`, update `my_ip` in `secrets.tfvars`** to the current public IP of this machine in CIDR form (`"<ip>/32"`, e.g. from `curl -s https://checkip.amazonaws.com`). It restricts SSH ingress to the NAT instance (`terraform/main.tf`), and the IP changes over time, so a stale value locks out SSH access. `secrets.tfvars` is gitignored — never commit it or print its other values.

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPEN_WEATHER_API` | OpenWeather API key |
| `ROBOCLIMATE_HOME` | Project root directory |
| `ROBOCLIMATE_CSV_FILES_PATH` | Path to CSV data directory |
| `S3_BUCKET_NAME` | S3 bucket for backups |

## Architecture

### Data Flow
1. **Collect**: AWS Lambda functions fetch data from OpenWeather API on a schedule (EventBridge Scheduler) and append to CSV files on EFS
2. **Analyze**: Data analysis module joins measurements with forecasts (`join_*.csv`) and computes error metrics (`metrics_*.csv`)
3. **Visualize**: Streamlit dashboard reads CSV files and displays forecast accuracy metrics

### Key Modules
- `roboclimate/config.py` — city list, weather variable definitions, file paths
- `roboclimate/common.py` — shared HTTP/retry logic, CSV I/O, OpenWeather API calls
- `roboclimate/metrics.py` — error metric implementations (MAE, RMSE, MEDAE, MASE)
- `roboclimate/data_analysis.py` — Python join/metric calculation (legacy; replaced by Java module)
- `roboclimate/data_analysis/` — Java 22 reimplementation of data analysis (faster)
- `roboclimate/streamlit_app.py` — interactive dashboard
- `roboclimate/*_spider_lambda.py` — AWS Lambda handlers for data collection
- `roboclimate/backup_lambda.py` — Lambda handler that backs up EFS data to S3

### AWS Infrastructure (Terraform)
- Lambda functions run in a private VPC subnet; a NAT instance in a public subnet provides internet access
- EFS is the primary data store (mounted by Lambda and an EC2 instance for file operations)
- S3 is used for backups via `backup_lambda.py`
- All Lambda schedules are managed by EventBridge Scheduler

### CSV File Naming Convention
- `weather_{city}.csv` — raw measurements
- `forecast_{city}.csv` — raw forecasts
- `join_{variable}_{city}.csv` — measurements joined with forecasts (input to metrics)
- `metrics_{variable}_{city}.csv` — computed error metrics

### Forecast Horizons
Forecasts are evaluated at five horizons labeled `t1`–`t5` (each step is 3 hours ahead).

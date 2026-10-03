# Lambda dependency, build and release procedure — design

Date: 2026-10-03
Status: approved design, pending implementation plan

## Background

Upgrading the four Lambda functions (weather, forecast, uvi, backup) from python3.8 to python3.13 on 2026-10-03 exposed several gaps between development and operations:

1. **Incomplete requirements.** `lambda_backup_requirements.txt` listed only boto3/botocore, but `backup_lambda.py` imports `common.py`, which imports `requests` and `tenacity` at module level. The previous package (v1, May 2024) happened to bundle both; rebuilding strictly from the file produced a package that failed with `No module named 'requests'`.
2. **Only top-level dependencies are pinned.** Transitive dependencies (`certifi`, `idna`, `charset_normalizer`, `urllib3`, `botocore`'s tree) are resolved fresh on every build, so two builds of the same commit can differ.
3. **Packages were tested in a shared environment.** Lambda code was tested with the spider and backup dependencies installed together, so the backup handler borrowed `requests` from the spider set and the gap went unnoticed.
4. **Packaging depended on the dev venv.** `artifact_prep.sh` ran whatever `pip` was on `PATH`; a stale venv broke it.
5. **Deploy and release are separate, but nothing said so.** EventBridge schedules invoke pinned, published versions (`terraform/main.tf`, `module "eventbridge_scheduler"`), not `$LATEST`. Deploying published new versions that no schedule called; the runtime upgrade only took effect after the pins were bumped (#13).

## Goals

- What ships is fully pinned and reproducible from the repo.
- A package that cannot import or fails its tests never reaches `terraform apply`.
- Each function's package contains only what that function imports.
- Releasing a new version to the schedules is an explicit, verified step.
- Everything runs on the laptop today and can be called unchanged from a future CI job.

## Non-goals

- CI/CD (GitHub Actions, VCS-driven HCP Terraform runs). The scripts are written so a later CI job can call them, but setting that up is a separate piece of work.
- Monitoring and alerting (CloudWatch alarms, log-based error metrics). Separate piece of work.
- Writing new unit tests for the forecast and backup handlers (they have none today; see Testing).
- Refactoring `common.py` beyond extracting the logger.
- Automatic releases (Lambda aliases, traffic shifting).

## Decisions

| Topic | Decision |
|---|---|
| Where builds run | Laptop now; same scripts callable from CI later |
| Locking tool | `uv pip compile`, resolving for Linux x86_64 / Python 3.13 |
| Testing against shipped deps | Unit tests run inside the official Lambda image with only the package's locked deps |
| Dependency updates | Manual, triggered by GitHub Dependabot security alerts or by choice |
| Script structure | Extend the existing bash scripts (repo convention) |

## Design

### 1. Lock files

New directory `lambda/`, replacing `lambda_spider_requirements.txt` and `lambda_backup_requirements.txt`:

```
lambda/
  spider.in        # top-level deps of the 3 spiders: requests, tenacity
  spider-requirements.txt      # generated: every package pinned, with hashes
  backup.in        # top-level deps of backup: boto3
  backup-requirements.txt      # generated
  lock.sh          # regenerates the *-requirements.txt lock files
```

- `.in` files record intent; the generated `*-requirements.txt` lock files record exactly what ships. Both are committed. The lock files use pip's requirements format and a `*requirements*.txt` name so GitHub Dependabot can read them.
- Existing pins are carried over into the `.in` files (`requests==2.28.2`, `tenacity==8.2.2`, `boto3==1.34.109`, `botocore==1.34.109`) so the first lock changes only the unpinned transitive deps. Loosening them is a later, deliberate upgrade.
- `lock.sh` runs, for each `.in`:
  `uv pip compile lambda/<name>.in -o lambda/<name>-requirements.txt --python-platform x86_64-manylinux2014 --python-version 3.13 --generate-hashes`
  and passes through `--upgrade` or `--upgrade-package <pkg>` when given.
- Hashes make `pip`/`uv` reject any file that does not match what was locked.
- boto3 stays bundled in the backup package rather than relying on the runtime-provided copy, which AWS updates without notice.
- Updating a dependency: `./lambda/lock.sh --upgrade-package requests` (or `--upgrade`), then build + verify, then commit the `.in` and lock file in a PR.
- Enable GitHub Dependabot **security alerts** (not version-update PRs) for the repo; it scans the lock files and alerts on known vulnerabilities in any pinned package, including transitive ones.

### 2. Build and verify (`terraform/artifact_prep.sh`)

Interface: `./artifact_prep.sh <weather_spider|forecast_spider|uvi_spider|backup|all>`. Runs build then verify for each function, stops at the first failure, exits non-zero on any failure.

**Function manifest.** One table in the script maps each function to its handler, source files, lock file and tests:

| Function | Handler | Source files | Lock | Tests |
|---|---|---|---|---|
| weather_spider | `weather_spider_lambda.weather_handler` | `weather_spider_lambda.py`, `common.py`, `log_config.py` | `spider-requirements.txt` | `tests/weather_spider_lambda_test.py` |
| forecast_spider | `forecast_spider_lambda.forecast_handler` | `forecast_spider_lambda.py`, `common.py`, `log_config.py` | `spider-requirements.txt` | none |
| uvi_spider | `uvi_spider_lambda.handler` | `uvi_spider_lambda.py`, `common.py`, `log_config.py` | `spider-requirements.txt` | `tests/uvi_spider_lambda_test.py` |
| backup | `backup_lambda.handler` | `backup_lambda.py`, `log_config.py` | `backup-requirements.txt` | none |

Handler names must match `var.handler_name` passed to each Lambda module in `terraform/main.tf`.

**Build**, per function:
1. Delete and recreate `terraform/<function>_pkg/`; copy in the manifest's source files from `$ROBOCLIMATE_HOME/roboclimate/`.
2. `uv pip install --target <pkg> -r lambda/<lock> --no-deps --require-hashes --python-platform x86_64-manylinux2014 --python-version 3.13`.
   `--no-deps` ensures only locked packages are installed; an incomplete lock yields an incomplete package that verification then rejects.
3. Requires only `uv` and the repo — no dev venv.

**Verify**, per function, in `public.ecr.aws/lambda/python:3.13` run with `--platform linux/amd64`, package mounted read-only at `/var/task`, Python started in isolated mode (`-I`) with only `/var/task` added to `sys.path`, and a logging handler pre-installed (as the Lambda runtime does, so `log_config` does not try to write a log file):
1. **Import check:** import the handler module and assert the handler attribute is callable.
2. **Unit tests** (where the manifest lists any): pytest is installed into a separate directory outside the package, mounted read-only and appended to `sys.path` *after* `/var/task`, so it cannot supply a missing runtime dependency. The repo's `tests/` directory (test modules and their `json_files`/`csv_files` fixtures) is mounted read-only alongside. Tests run against the package's source files and locked deps only.
3. Output: one `PASS`/`FAIL` line per function per check.

The Docker image is pulled once and reused; verification needs no network beyond that.

### 3. Deploy, then release

Documented in `lambda/README.md`; CLAUDE.md gets a short summary and a pointer.

**Deploy** (publishes new versions; schedules unaffected):
1. `./artifact_prep.sh all` — build + verify; stop on failure.
2. Refresh `my_ip` in `secrets.tfvars` (existing CLAUDE.md rule), then `terraform plan`. It must show only the intended function changes and no schedule changes.
3. Apply. Record the new version numbers (`aws lambda list-versions-by-function`).

**Release** (points schedules at the new versions), in its own PR:
1. **Pre-release check:** `lambda/prerelease_check.sh <function> <version>` downloads that published version, checks its SHA-256 against the version's `CodeSha256`, and runs it in the Lambda Runtime Interface Emulator (`public.ecr.aws/lambda/python:3.13`) with real OpenWeather calls (key read from the environment, redacted from all output), writing to a throwaway copy of the CSVs mounted at `/mnt/efs`. It reports errors, warnings, files written and rows added per CSV. Required before every release.
   - **Spiders:** the run must write every city with no `[ERROR]` lines.
   - **Backup** writes to S3, so the emulator runs it with no AWS credentials: it must import, list the CSVs and fail only at the first `put_object` call with a credentials error. After release, one live invocation of the released version confirms the S3 path (as was done for `:3` on 2026-10-03); this overwrites `s3://roboclimate/backup/` with the current EFS files, exactly as the nightly run does.
2. Bump the version number(s) in `terraform/main.tf`. The plan must show only schedule targets and the scheduler IAM policy — no function changes (a function change would publish another version and invalidate the pinned numbers).
3. Apply. Confirm each schedule's target ARN and that version's runtime.
4. **First-run check:** `lambda/verify_run.sh <function> <since>` reports, for runs since the given time: the log stream versions, the `INIT_START Runtime Version`, number of writes, `[ERROR]`/`Traceback`/timeout lines, and the scheduler's `TargetErrorCount`. A release is complete when each released function's first scheduled run shows the expected runtime, the expected writes and no errors.

**Rollback:** revert the version-number change and apply; previous versions remain published.

### 4. Decouple backup from the spider code

- New `roboclimate/log_config.py` containing the logging setup moved verbatim from `common.py` (if a root handler exists — the Lambda case — set level INFO; otherwise `basicConfig(..., filename='weather.log')`). Exposes `logger`.
- `common.py`: replace its logging setup with `from log_config import logger`. Existing `from common import logger` imports (spiders, `tests/weather_spider_lambda_test.py`) keep working.
- `backup_lambda.py`: `from log_config import logger` instead of `from common import logger`.
- Packaging per the manifest in section 2: backup ships `backup_lambda.py` + `log_config.py` only.
- `lambda/backup.in` contains only `boto3==1.34.109` and `botocore==1.34.109`; the `requests`/`tenacity` lines added in #12 are dropped.

## Testing

- **This work's acceptance test** is its own first use:
  1. `./artifact_prep.sh all` passes for all four functions.
  2. Negative control: temporarily restore `from common import logger` in `backup_lambda.py`; the backup import check must fail. Revert.
  3. Negative control: delete `requests` from `spider-requirements.txt` in a scratch copy; the weather import check must fail.
  4. Deploy, then release the new backup version (and any spider versions whose packages changed) through section 3, including the first scheduled run check.
- Existing unit tests (31) keep passing in the dev venv.
- Known gap, out of scope: forecast and backup have no unit tests, so they get the import check only.

## Files

| File | Change |
|---|---|
| `lambda/spider.in`, `lambda/backup.in` | new |
| `lambda/spider-requirements.txt`, `lambda/backup-requirements.txt` | new, generated |
| `lambda/lock.sh` | new |
| `lambda/prerelease_check.sh`, `lambda/verify_run.sh` | new (from the ad-hoc scripts used on 2026-10-03) |
| `lambda/README.md` | new: lock, build, deploy, release, rollback |
| `lambda_spider_requirements.txt`, `lambda_backup_requirements.txt` | deleted |
| `terraform/artifact_prep.sh` | rewritten: manifest, uv build, Docker verify, `all` |
| `roboclimate/log_config.py` | new |
| `roboclimate/common.py`, `roboclimate/backup_lambda.py` | import logger from `log_config` |
| `CLAUDE.md` | deploy ≠ release summary, pointer to `lambda/README.md`, updated commands |
| `README.md` | replace the `lambda_requirements.txt` paragraph with a pointer to `lambda/README.md` |

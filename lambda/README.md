# Lambda dependencies, build and release

Four Lambda functions: `weather`, `forecast`, `uvi` (the spiders) and `backup`.

**Deploying publishes a new version; it does not change what runs.** EventBridge schedules invoke
pinned versions set in `terraform/main.tf` (`module "eventbridge_scheduler"`). Changing those numbers
is the release.

## Dependencies

| File | Purpose |
|---|---|
| `spider.in`, `backup.in` | Top-level deps — edit these |
| `spider-requirements.txt`, `backup-requirements.txt` | Generated locks: every package pinned, with hashes — never edit by hand |
| `verify-tools.in` / `verify-tools-requirements.txt` | pytest, used only to run tests inside the Lambda image |

Locks are resolved for the Lambda runtime (Linux x86_64, Python 3.13), so they are correct even when generated on macOS.

```bash
lambda/lock.sh                             # re-lock after editing a .in file
lambda/lock.sh --upgrade-package requests  # upgrade one package
lambda/lock.sh --upgrade                   # upgrade everything the .in files allow
```

Updates are manual: when a GitHub Dependabot security alert fires, or by choice. Commit the `.in` and lock changes in a PR.

## Build and verify

```bash
terraform/artifact_prep.sh all     # or one of: weather_spider forecast_spider uvi_spider backup
```

Builds each `terraform/<function>_pkg/` from its source files and lock only (`--no-deps --require-hashes`), then,
inside `public.ecr.aws/lambda/python:3.13`, imports the handler in isolation and runs the function's unit tests
against the locked deps. Any failure stops the script. Requires `uv` and Docker.

Each package contains only the source files its function imports (see the manifest in `artifact_prep.sh`):
the spiders ship `common.py` and `log_config.py`; backup ships `log_config.py` only.

## Deploy (publishes versions)

1. `terraform/artifact_prep.sh all` — must end with `ALL CHECKS PASSED`.
2. Update `my_ip` in `secrets.tfvars`, then from `terraform/`:
   `TF_CLOUD_ORGANIZATION=fjab76-org terraform plan -var-file ../secrets.tfvars -out=deploy.tfplan`
   — only the intended `aws_lambda_function` changes; no schedule changes.
3. `terraform apply deploy.tfplan`, then note the new versions:
   `AWS_PROFILE=myadmin aws lambda list-versions-by-function --function-name t_roboclimate_<name> --query 'Versions[-1].[Version,Runtime]'`

Deploy only from an up-to-date `master`, so what runs on AWS always matches reviewed code.

## Release (points schedules at new versions) — in its own PR

1. Pre-release check, for each new version:
   `AWS_PROFILE=myadmin OPEN_WEATHER_API=... lambda/prerelease_check.sh <weather|forecast|uvi|backup> <version>` — must print `PASS`.
   (Download fresh seed data first: `terraform/download_csv_files_from_s3.sh myadmin csv_files`.)
2. Bump the version numbers in `terraform/main.tf`. `terraform plan` must show only `aws_scheduler_schedule` targets and
   `aws_iam_policy.eventbridge` — no function changes (one would publish another version and invalidate the pins).
3. Apply; confirm each schedule's target:
   `AWS_PROFILE=myadmin aws scheduler get-schedule --name <name>-lambda-schedule --query Target.Arn`
4. After each released function's next scheduled run (UTC: weather every 3 h, forecast 22:00, backup 23:00, uvi 02:00):
   `AWS_PROFILE=myadmin lambda/verify_run.sh <name> <YYYY-MM-DDTHH:MM:SS just before the run>` — must print `PASS`
   with the expected `INIT_START Runtime Version`.
5. For backup only: one live invocation of the released version confirms the S3 path
   (`aws lambda invoke --function-name t_roboclimate_backup:<version> out.json`); it overwrites `s3://roboclimate/backup/`
   with the current EFS files, exactly as the nightly run does.

Note: the spiders catch per-city exceptions and only log them, so a run that failed for every city still reports
success to Lambda. Always judge a run by its writes and `[ERROR]` lines (as both check scripts do), not its status.

## Rollback

Revert the version-number change in `terraform/main.tf` and apply. Previous versions stay published.

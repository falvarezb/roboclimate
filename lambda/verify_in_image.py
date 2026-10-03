"""Verify a Lambda package from inside the official Lambda image.

Run as: python3 -I /opt/verify_in_image.py --handler <module.function> [--tests tests/x_test.py ...]
Mounts expected: package at /var/task, pytest at /opt/verify-tools, repo tests/ at /src/tests.
"""
import argparse
import importlib
import logging
import os
import shutil
import sys

PACKAGE_DIR = '/var/task'
TOOLS_DIR = '/opt/verify-tools'
TESTS_SRC = '/src/tests'
WORK_DIR = '/tmp/work'


def import_check(handler):
    module_name, func_name = handler.rsplit('.', 1)
    try:
        module = importlib.import_module(module_name)
        if not callable(getattr(module, func_name)):
            raise TypeError(f"{handler} is not callable")
    except Exception as ex:  # report any import-time failure as a check failure
        print(f"FAIL import {handler}: {type(ex).__name__}: {ex}")
        return False
    print(f"PASS import {handler}")
    return True


def run_tests(tests):
    # pytest goes AFTER the package on sys.path so it can never supply a missing runtime dependency
    sys.path.append(TOOLS_DIR)
    import pytest  # pylint: disable=import-outside-toplevel
    shutil.copytree(TESTS_SRC, os.path.join(WORK_DIR, 'tests'))  # tests write to tests/temp, so copy to a writable dir
    os.chdir(WORK_DIR)
    exit_code = pytest.main(['-q', '-p', 'no:cacheprovider', *tests])
    print(f"{'PASS' if exit_code == 0 else 'FAIL'} tests {' '.join(tests)}")
    return exit_code == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--handler', required=True)
    parser.add_argument('--tests', nargs='*', default=[])
    args = parser.parse_args()

    sys.path.insert(0, PACKAGE_DIR)
    # The Lambda runtime installs a root log handler before loading the handler; mimic it so
    # log_config does not try to write weather.log into the read-only package directory.
    logging.getLogger().addHandler(logging.StreamHandler())

    ok = import_check(args.handler)
    if ok and args.tests:
        ok = run_tests(args.tests)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

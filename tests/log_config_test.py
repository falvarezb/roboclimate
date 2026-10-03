import os
import subprocess
import sys

ROBOCLIMATE_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'roboclimate')


def _modules_loaded_after_import(module_name, cwd):
    """Import module_name in a fresh interpreter and return the set of top-level modules it loaded."""
    code = f"import sys, {module_name}; print(','.join(sorted(sys.modules)))"
    env = dict(os.environ, PYTHONPATH=ROBOCLIMATE_SRC)
    out = subprocess.run([sys.executable, '-c', code], cwd=cwd, env=env, capture_output=True, text=True, check=True)
    return set(out.stdout.strip().split(','))


def test_backup_lambda_does_not_load_spider_dependencies(tmp_path):
    loaded = _modules_loaded_after_import('backup_lambda', tmp_path)
    assert 'common' not in loaded
    assert 'requests' not in loaded
    assert 'tenacity' not in loaded


def test_common_still_exposes_logger(tmp_path):
    code = "import common, log_config; assert common.logger is log_config.logger"
    env = dict(os.environ, PYTHONPATH=ROBOCLIMATE_SRC)
    subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env, check=True)

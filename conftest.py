from datetime import datetime
from pathlib import Path
import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """ Dynamic log file name with date """
    now = datetime.now()
    # custom report file
    logs_path = f"./logs/logs{now}.log"
    # adjust plugin options
    config.option.log_file = logs_path
    config.option.self_contained_log_file = True
"""Disk admission for new heavy jobs; no verification or acceptance decisions."""
import math
import os
from pathlib import Path
import shutil
import sys


def threshold(value, env, default):
    try:
        number = float(value if value is not None else os.environ.get(env, default))
    except (TypeError, ValueError):
        raise ValueError('disk floors must be finite nonnegative numbers of GB') from None
    if not math.isfinite(number) or number < 0:
        raise ValueError('disk floors must be finite nonnegative numbers of GB')
    return number


def admit(path, job, hard_gb=None, soft_gb=None, allow_low_disk=False):
    hard = max(3, threshold(hard_gb, 'SKYRIM_LANE_MIN_FREE_GB', '3'))
    soft = max(hard, threshold(soft_gb, 'SKYRIM_SOFT_FREE_GB', '10'))
    path = Path(path).resolve()
    while not path.exists():
        path = path.parent
    free = shutil.disk_usage(path).free / 1_000_000_000
    if free < hard:
        raise ValueError(f'insufficient free disk space for {job}: {free:.2f} GB free; need {hard:g} GB '
                         '(hard floor; cannot override below 3 GB)')
    if free < soft:
        message = (f'low disk space for {job}: {free:.2f} GB free; soft floor {soft:g} GB; '
                   'free space or explicitly pass --allow-low-disk')
        print('WARNING: ' + message, file=sys.stderr)
        if not allow_low_disk:
            raise ValueError(message)
    return free

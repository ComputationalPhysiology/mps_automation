#!/usr/bin/env python

"""Tests for `mps_automation` package."""
import sys
from pathlib import Path
from unittest import mock

from tests.generate_dummy_data import get_dummy_analysis_data

mps_mock = mock.MagicMock()
mps_mock.analysis.analyze_mps_func = get_dummy_analysis_data
sys.modules["mps"] = mps_mock

from mps_automation import collect  # noqa: E402

here = Path(__file__).absolute().parent


def test_main(test_folder):
    experiment = "200720_HCQ_doseEscalation"
    folder = Path(test_folder).joinpath(experiment)
    config = here.joinpath("config_files").joinpath(experiment).with_suffix(".yaml")
    collect.main(folder, config)
    assert Path(folder.joinpath("data.xlsx")).is_file()

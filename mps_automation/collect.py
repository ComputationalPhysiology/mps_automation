import os
from pathlib import Path
from typing import Any, Dict

import mps
import numpy as np
import yaml
from mps_data_parser import PathMatcher
from sqlalchemy import create_engine
from sqlalchemy.orm.session import Session as SessionType
from sqlalchemy.orm.session import sessionmaker

from . import model
from .view import View


def check_valid_dose(dose_str: str):
    # Implement logic here to check for valid doses
    pass


def check_valid_drug(drug_str: str):
    # Implement logic here to check for valid drugs
    pass


def check_valid_chip(chip_str: str):
    # Implement logic here to check for valid chips
    pass


def check_valid_media(media_str: str):
    # Implement logic here to check for valid chips
    pass


def check_valid_pacing(pacing_str: str):
    if pacing_str == "":
        raise ValueError
    # Implement logic here to check for valid pacing frequencies
    pass


def check_valid_trace_type(trace_type_str: str):
    if trace_type_str not in ["calcium", "voltage", "brightfield"]:
        raise ValueError(f"{trace_type_str} is not a valid trace type")


def check_valid_path(path: str):
    pass


def _get_x(session: SessionType, x_str: str, cls_str, check_func):
    x = (
        session.query(getattr(model, cls_str))
        .filter(getattr(model, cls_str).value == x_str)
        .one_or_none()
    )

    if x is None:
        check_func(x_str)
        x = getattr(model, cls_str)(value=x_str)
        session.add(x)

    return x


def get_dose(session: SessionType, dose_str: str):
    return _get_x(session, dose_str, "Dose", check_valid_dose)


def get_drug(session: SessionType, drug_str: str):
    return _get_x(session, drug_str, "Drug", check_valid_drug)


def get_pacing(session: SessionType, pacing_str: str):
    return _get_x(session, pacing_str, "Pacing", check_valid_pacing)


def get_chip(session: SessionType, chip_str: str):
    return _get_x(session, chip_str, "Chip", check_valid_chip)


def get_media(session: SessionType, media_str: str):
    return _get_x(session, media_str, "Media", check_valid_media)


def get_trace_type(session: SessionType, trace_type_str: str):
    return _get_x(session, trace_type_str, "TraceType", check_valid_trace_type)


def get_recording(session: SessionType, path: str):
    return _get_x(session, path, "Recording", check_valid_path)


def add_data_to_database(session, data, analysis=None):
    if analysis is None:
        analysis = {}
    recording = get_recording(session, data.get("path", ""))

    drug = get_drug(session, data.get("drug", ""))
    chip = get_chip(session, data.get("chip", ""))
    media = get_media(session, data.get("media", ""))
    dose = get_dose(session, data.get("dose", ""))
    pacing = get_pacing(session, data.get("pacing_frequency", ""))
    trace_type = get_trace_type(session, data.get("trace_type", ""))

    recording.analysis = analysis
    recording.dose = dose
    recording.drug = drug
    recording.pacing = pacing
    recording.trace_type = trace_type
    recording.chip = chip
    recording.media = media
    session.add(recording)
    session.commit()


def serialize_numpy_dict(d):
    new_d = {}
    for k, v in d.items():
        if isinstance(v, dict):
            new_d[k] = serialize_numpy_dict(v)
        elif isinstance(v, np.ndarray):
            new_d[k] = v.tolist()
        elif isinstance(v, np.float64):
            new_d[k] = float(v)
        elif isinstance(v, np.int32):
            new_d[k] = int(v)
        else:
            new_d[k] = v
    return new_d


def get_analysis(data) -> Dict[str, Any]:
    # By default we assume that it might be a folder next to the
    # raw data with a `data.npy` file containing the analysis

    path = Path(data.get("path", ""))
    outdir = path.parent.joinpath(path.stem)
    if outdir.joinpath("data.npy").is_file():
        return serialize_numpy_dict(
            np.load(outdir.joinpath("data.npy"), allow_pickle=True).item()
        )

    # Run analyis
    try:
        mps_data = mps.MPS(path)
        d = serialize_numpy_dict(mps.analysis.analyze_mps_func(mps_data))
    except Exception:
        d = {}
    return d


def run(folder, config_file):
    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    pathmatcher = PathMatcher(config, folder)
    sqlite_filepath = folder.joinpath("database.db")

    engine = create_engine(f"sqlite:///{sqlite_filepath}")
    model.Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session: SessionType = Session()

    for root, dirs, files in os.walk(folder):
        for f in files:
            path = Path(root).joinpath(f)
            if path.suffix != ".nd2":
                continue

            data = pathmatcher(path).to_dict()
            analysis = get_analysis(data)
            add_data_to_database(session, data, analysis)

    v = View(session)
    print(v.info)
    v.to_excel(
        folder.joinpath("data.xlsx"),
        info={
            "folder": folder.absolute(),
            "database": sqlite_filepath.absolute(),
            "config_file": config_file.absolute(),
        },
    )

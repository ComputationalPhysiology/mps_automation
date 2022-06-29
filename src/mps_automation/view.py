import datetime
import itertools as it
import logging
from collections import namedtuple
from pathlib import Path
from textwrap import dedent

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import and_
from sqlalchemy import engine

from . import model

logger = logging.getLogger(__name__)

DistinctValues = namedtuple(
    "DistinctValues",
    ["doses", "drugs", "pacing", "media", "chips", "trace_types", "repeats"],
)


class View:
    def __init__(self, session):
        self.session = session

    def _format_str(self, x, lst):
        if len(lst) == 0 or (len(lst) == 1 and lst[0] == ""):
            return ""
        return ", ".join(
            [
                f"{y}: ({t})"
                for y, t in zip(lst, get_recordings_for_x(self.session, x, lst))
            ],
        )

    def get_number_of_recordings(self):
        chips_nr = self._format_str("chip", self.distinct_values.chips)
        pacing_nr = self._format_str("pacing", self.distinct_values.pacing)
        doses_nr = self._format_str("dose", self.distinct_values.doses)
        drugs_nr = self._format_str("drug", self.distinct_values.drugs)
        media_nr = self._format_str("media", self.distinct_values.media)
        trace_type_nr = self._format_str("trace_type", self.distinct_values.trace_types)
        repeat_nr = self._format_str("repeat", self.distinct_values.repeats)
        df = pd.Series(
            {
                "drugs": drugs_nr,
                "pacing": pacing_nr,
                "doses": doses_nr,
                "media": media_nr,
                "trace_type": trace_type_nr,
                "chips": chips_nr,
                "repeats": repeat_nr,
            },
        )

        return df

    @property
    def info(self):

        df = self.get_number_of_recordings()
        s = dedent(
            f"""\
        --- General info ----
        Drugs (recordings):
        {df.drugs}

        Doses (recordings): (total: {len(self.distinct_values.doses)} doses)
        {df.doses}

        Pacing Frequencies (recordings)
        {df.pacing}

        Chips (recordings): (total: {len(self.distinct_values.chips)} chips)
        {df.chips}

        Media (recordings):
        {df.media}

        Trace types (recordings):
        {df.trace_type}

        Repeats (recordings):
        {df.repeats}

        """,
        )

        return s

    @property
    def distinct_values(self) -> DistinctValues:
        if not hasattr(self, "_distinct_values"):
            self._distinct_values = DistinctValues(
                doses=sorted(
                    [
                        delist(x)
                        for x in self.session.query(model.Dose.value).distinct()
                    ],
                ),
                drugs=[
                    delist(x) for x in self.session.query(model.Drug.value).distinct()
                ],
                pacing=[
                    delist(x) for x in self.session.query(model.Pacing.value).distinct()
                ],
                chips=[
                    delist(x) for x in self.session.query(model.Chip.value).distinct()
                ],
                media=[
                    delist(x) for x in self.session.query(model.Media.value).distinct()
                ],
                trace_types=[
                    delist(x)
                    for x in self.session.query(model.TraceType.value).distinct()
                ],
                repeats=[
                    delist(x) for x in self.session.query(model.Repeat.value).distinct()
                ],
            )
        return self._distinct_values

    def get_all(
        self,
        chip=None,
        pacing=None,
        trace_type=None,
        dose=None,
        media=None,
        drug=None,
        repeat=None,
    ):

        args = []

        for x in ["chip", "pacing", "media", "dose", "drug", "trace_type", "repeat"]:
            if eval(x) is not None:
                args.append(getattr(model.Recording, x).has(value=eval(x)))

        return self.session.query(model.Recording).filter(and_(*args))

    def plot_trace(self, folder):
        logger.info("Plot traces...")
        for (drug, trace_type, pacing, dose, media, chip, repeat) in it.product(
            self.distinct_values.drugs,
            ["calcium", "voltage"],
            self.distinct_values.pacing,
            self.distinct_values.doses,
            self.distinct_values.media,
            self.distinct_values.chips,
            self.distinct_values.repeats,
        ):
            path = (
                Path(folder)
                .joinpath("plots")
                .joinpath(drug)
                .joinpath("-".join([trace_type, pacing]))
                .joinpath("-".join([chip, media]))
                .joinpath("-".join([dose, repeat]))
                .with_suffix(".png")
            )
            recs = self.get_all(
                drug=drug,
                media=media,
                chip=chip,
                dose=dose,
                trace_type=trace_type,
                pacing=pacing,
                repeat=repeat,
            )
            if recs.count() == 0:
                continue
            d = recs.first()
            f = d.analysis.get("unchopped_data", {})
            if not f:
                continue

            path.parent.mkdir(exist_ok=True, parents=True)

            fig, ax = plt.subplots(2, 1, sharex=True)
            ax[0].plot(f["original_times"], f["original_trace"])
            ax[1].plot(f["time"], f["trace"])
            ax[1].set_xlabel("Time [ms]")
            ax[0].set_ylabel("Pixel intensity")
            ax[1].set_ylabel("dF / F0")
            fig.savefig(path)
            plt.close()
        logger.info("Done plotting traces")

    def to_excel(self, filename, info=None):
        logger.info("Create excel file...")
        if info is None:
            info = {}

        filename = Path(filename)
        columns = [
            "drug",
            "trace_type",
            "pacing",
            "media",
            "chip",
            "dose",
            "repeat",
            "APD30",
            "cAPD30",
            "APD80",
            "cAPD80",
            "triangulation",
            "beat_rate",
            "EAD",
            "bad_trace",
        ]
        data = []
        for (drug, trace_type, pacing, dose, media, chip, repeat) in it.product(
            self.distinct_values.drugs,
            ["calcium", "voltage"],
            self.distinct_values.pacing,
            self.distinct_values.doses,
            self.distinct_values.media,
            self.distinct_values.chips,
            self.distinct_values.repeats,
        ):
            recs = self.get_all(
                drug=drug,
                media=media,
                chip=chip,
                dose=dose,
                trace_type=trace_type,
                pacing=pacing,
                repeat=repeat,
            )
            if recs.count() == 0:
                # Missing value
                continue
            else:
                if recs.count() > 1:
                    paths = list(map(lambda x: x.path, recs))
                    logger.warning(
                        f"Warning: The following paths have the same parameters {paths}",
                    )
                    logger.warning(f"Will only use {paths[0]}")

                d = recs.first()
                f = d.analysis.get("features", {})

            try:
                bad_trace = not (f["apd30"] < f["apd50"] < f["apd80"])
            except Exception:
                bad_trace = True
            data.append(
                [
                    drug,
                    trace_type,
                    pacing,
                    media,
                    chip,
                    dose,
                    repeat,
                    f.get("apd30", np.nan),
                    f.get("capd30", np.nan),
                    f.get("apd80", np.nan),
                    f.get("capd80", np.nan),
                    f.get("triangulation", np.nan),
                    f.get("beating_frequency", np.nan),
                    f.get("num_eads", 0) > 0,
                    bad_trace,
                ],
            )

        df_info = {"timestamp": datetime.datetime.now().isoformat()}
        df_info.update(info)
        df_info.update(self.get_number_of_recordings().to_dict())

        with pd.ExcelWriter(filename, mode="w") as writer:
            pd.Series(df_info).to_excel(writer, "info")

        df = pd.DataFrame(data, columns=columns)
        for trace_type, df_trace in df.groupby("trace_type"):
            for pacing, df_pacing in df_trace.groupby("pacing"):
                with pd.ExcelWriter(filename, engine="openpyxl", mode="a") as writer:
                    df_pacing.sort_values(by=["chip", "dose", "repeat"]).to_excel(
                        writer,
                        "-".join([trace_type, pacing]),
                    )

        logger.info(f"Done creating excel file at {filename}.")


def delist(x):
    if isinstance(x, (list, tuple, engine.Row)):
        return x[0]
    else:
        return x


def get_recordings_for_x(session, x, lst):
    return [
        session.query(model.Recording)
        .filter(getattr(model.Recording, x).has(value=xi))
        .count()
        for xi in lst
    ]

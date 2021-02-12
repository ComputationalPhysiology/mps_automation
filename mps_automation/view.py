import itertools as it
from collections import namedtuple
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
from sqlalchemy import and_

from . import model

DistinctValues = namedtuple(
    "DistinctValues", ["doses", "drugs", "pacing", "media", "chips", "trace_types"]
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
            ]
        )

    @property
    def info(self):

        chips_nr = self._format_str("chip", self.distinct_values.chips)
        pacing_nr = self._format_str("pacing", self.distinct_values.pacing)
        doses_nr = self._format_str("dose", self.distinct_values.doses)
        drugs_nr = self._format_str("drug", self.distinct_values.drugs)
        media_nr = self._format_str("media", self.distinct_values.media)
        trace_type_nr = self._format_str("trace_type", self.distinct_values.trace_types)

        s = dedent(
            f"""\
        --- General info ----
        Drugs (recordings):
        {drugs_nr}

        Doses (recordings): (total: {len(self.distinct_values.doses)} doses)
        {doses_nr}

        Pacing Frequencies (recordings)
        {pacing_nr}

        Chips (recordings): (total: {len(self.distinct_values.chips)} chips)
        {chips_nr}

        Media (recordings):
        {media_nr}

        Trace types (recordings):
        {trace_type_nr}

        """
        )
        return s

    @property
    def distinct_values(self) -> DistinctValues:
        if not hasattr(self, "_distinct_values"):
            self._distinct_values = DistinctValues(
                doses=sorted(
                    [delist(x) for x in self.session.query(model.Dose.value).distinct()]
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
            )
        return self._distinct_values

    def get_all(
        self, chip=None, pacing=None, trace_type=None, dose=None, media=None, drug=None
    ):

        args = []

        for x in ["chip", "pacing", "media", "dose", "drug", "trace_type"]:
            if eval(x) is not None:
                args.append(getattr(model.Recording, x).has(value=eval(x)))

        return self.session.query(model.Recording).filter(and_(*args))

    def to_excel(self, filename):

        filename = Path(filename)
        columns = [
            "trace_type",
            "pacing",
            "dose",
            "chip",
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
        for (trace_type, pacing, dose, chip) in it.product(
            ["calcium", "voltage"],
            self.distinct_values.pacing,
            self.distinct_values.doses,
            self.distinct_values.chips,
        ):
            recs = self.get_all(
                chip=chip, dose=dose, trace_type=trace_type, pacing=pacing
            )
            if recs.count() == 0:
                # Missing value
                d = {}
            if recs.count() > 1:
                paths = list(map(lambda x: x.value, recs))
                print(f"Warning: The following paths have the same parameters {paths}")
                print(f"Will only use {paths[0]}")

            d = recs.first()
            f = d.analysis["features"]
            try:
                bad_trace = not (f["apd30"] < f["apd50"] < f["apd80"])
            except Exception:
                bad_trace = True
            data.append(
                [
                    trace_type,
                    pacing,
                    dose,
                    chip,
                    f.get("apd30", np.nan),
                    f.get("capd30", np.nan),
                    f.get("apd80", np.nan),
                    f.get("capd80", np.nan),
                    f.get("triangulation", np.nan),
                    f.get("beating_frequency", np.nan),
                    f.get("num_eads", 0) > 0,
                    bad_trace,
                ]
            )

        df = pd.DataFrame(data, columns=columns)
        mode = "w"
        for trace_type, df_trace in df.groupby("trace_type"):
            for pacing, df_pacing in df_trace.groupby("pacing"):
                with pd.ExcelWriter(filename, mode=mode) as writer:
                    df_pacing.to_excel(writer, "-".join([trace_type, pacing]))
                mode = "a"


def delist(x):
    if isinstance(x, (list, tuple)):
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

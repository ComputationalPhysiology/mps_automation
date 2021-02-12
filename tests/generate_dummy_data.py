import shutil
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Union

import numpy as np
import yaml

PathStr = Union[Path, str]

HERE = Path(__file__).absolute().parent


def get_dummy_analysis_data(*args, **kwargs):
    trace_type = np.random.choice(["voltage", "calcium"])
    if trace_type == "voltage":
        return np.load(
            HERE.joinpath("example_traces/voltage_data.npy"),
            allow_pickle=True,
        ).item()
    return np.load(
        HERE.joinpath("example_traces/calcium_data.npy"),
        allow_pickle=True,
    ).item()


class SeqNr:
    """Dummy class that can be used an infinite counter"""

    def __init__(self):
        self.n = -1

    def __next__(self):
        self.n += 1
        # Yield 4 digit number with zeros filled in front
        return str(self.n).zfill(4)

    def __iter__(self):
        return self


CONTENT = {
    "200720_HCQ_doseEscalation": {
        "dose": ["dose0", "dose1", "dose2"],
        "pacing_frequency": ["1Hz", "15Hz", "spont"],
        "chip": ["1A", "3B"],
        "channel": ["Red", "Cyan"],
        "roi": ["VC"],
    },
    "190820_Ver_Alf_SCVI273_direct": {
        "date": [190820],
        "dose": ["no dose", "1uM"],
        "pacing_frequency": ["1Hz", "spont"],
        "chip": ["1A", "3B"],
        "media": ["SM", "MM"],
        "drug": ["Alf", "Ver"],
        "channel": ["Red", "Cyan"],
    },
    "181113_Isoproterenol_SCVi20": {
        "date": [181113],
        "dose": ["0nM", "1nM"],
        "pacing_frequency": ["1Hz", "0Hz"],
        "chip": ["2a", "3a"],
        "media": ["SM", "MM"],
        "channel": ["Red", "Cyan"],
        "roi": ["VC"],
        "control": ["Ctrl"],
    },
    "181116_Lidocaine": {
        "date": [181116],
        "dose": ["0uM", "1uM", "10uM"],
        "pacing_frequency": ["1Hz", "0Hz"],
        "chip": ["1A", "2A", "1B"],
        "media": ["SM", "MM"],
        "channel": ["Red", "Cyan"],
        "roi": ["VC"],
        "control": ["Ctrl"],
    },
}


def copy_data_traces(channel, dst):
    calcium_data = HERE.joinpath("example_traces/calcium_data.npy")
    voltage_data = HERE.joinpath("example_traces/voltage_data.npy")

    channel_to_data = {"Red": voltage_data, "Cyan": calcium_data}
    shutil.copy(channel_to_data[channel], dst)


def generate_data(
    config: Dict[str, Any],
    content: Dict[str, List[str]],
    data_dir: PathStr,
):

    data_dir = Path(data_dir)
    data_dir.mkdir(exist_ok=True, parents=True)

    folder = data_dir.joinpath(config["folder"])
    for path_str in config["regexs"]:
        for p, seq_nr in zip(product(*list(content.values())), SeqNr()):
            params = dict(zip(content.keys(), p))
            params["seq_nr"] = seq_nr

            path = folder.joinpath(path_str.format(**params))
            path.parent.mkdir(exist_ok=True, parents=True)
            path.touch()


def get_original_config(folder):
    with open(HERE.joinpath(f"config_files/{folder}.yaml"), "r") as f:
        d = yaml.load(f, Loader=yaml.SafeLoader)
    return d


def main():

    data_dir = Path("test_data")

    for folder, content in CONTENT.items():
        config = get_original_config(folder)
        generate_data(config, content, data_dir)

    return data_dir


if __name__ == "__main__":
    main()

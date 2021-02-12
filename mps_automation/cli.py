from pathlib import Path
from typing import Optional, Union

import typer

from .collect import run

PathStr = Union[str, Path]


def main(folder: PathStr, config_file: Optional[PathStr] = None):
    """Run automation script for MPS analysis

    \b
    Parameters
    ----------
    folder : str
        Path to the folder to be analyzed
    config_file : Optional[str], optional
        Path to the configuration file. If not provided it will
        look for a file called `config.yaml` in the root of the
        folder you are trying to analyze
    """

    folder = Path(folder)
    if not folder.is_dir():
        typer.echo(f"Folder {folder} is not a directory")
        raise typer.Exit(code=1)

    if config_file is None:
        config_file = folder.joinpath("config.yaml")
    config_file = Path(config_file)
    if not config_file.is_file():
        typer.echo(f"Cannot find config file at {config_file}")
        raise typer.Exit(code=2)

    valid_extensions = [".yml", ".yaml"]
    if config_file.suffix not in valid_extensions:
        typer.echo(
            f"Config file has an invalid extension. Expected of of "
            f"{valid_extensions} got {config_file.suffix}"
        )
        raise typer.Exit(code=3)

    typer.echo(f"Analyzing folder {folder}...")
    run(folder, config_file)

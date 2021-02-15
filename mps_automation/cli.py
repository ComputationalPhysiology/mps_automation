from pathlib import Path
from typing import Optional

import typer

from .collect import run


def main(
    folder: str,
    config_file: Optional[str] = None,
    recompute: bool = False,
    plot: bool = True,
):
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
    recompute : bool
        If True then redo analysis even though it allready
        exist in the database, by default False
    plot : bool
        Plot traces, by default True. Plotting takes quite a lot of
        time so you can speed up the process by setting this to false.
    loglevel : int
    """

    folder_: Path = Path(folder)
    if not folder_.is_dir():
        typer.echo(f"Folder {folder} is not a directory")
        raise typer.Exit(code=1)

    if config_file is None:
        config_file = folder_.joinpath("config.yaml").as_posix()
    config_file_: Path = Path(config_file)
    if not config_file_.is_file():
        typer.echo(f"Cannot find config file at {config_file}")
        raise typer.Exit(code=2)

    valid_extensions = [".yml", ".yaml"]
    if config_file_.suffix not in valid_extensions:
        typer.echo(
            f"Config file has an invalid extension. Expected of of "
            f"{valid_extensions} got {config_file_.suffix}"
        )
        raise typer.Exit(code=3)

    typer.echo(f"Analyzing folder {folder}...")
    run(folder_, config_file_, recompute=recompute, plot=plot)

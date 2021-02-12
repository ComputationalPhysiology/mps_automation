# MPS Automation Scripts



![CI](https://github.com/ComputationalPhysiology/mps_automation/workflows/CI/badge.svg)



Scripts for automating the mps analysis


* Source code: https://github.com/ComputationalPhysiology/mps_automation

## Install

Create a virtual environment
```
python -m virtualenv venv
```
Activate virtual environment
```
(Unix)
source venv/bin/activate
```
```
(Windows)
.\venv\Scripts\activate
```

Install private dependencies

- [mps](https://github.com/finsberg/mps)
- [mps_data_parser](https://github.com/ComputationalPhysiology/mps_data_parser)

Install package with its dependencies
```
python -m pip install .
```

## Usage

### Command line interface
Once installed you should be able to run the command
```
python -m mps_automation --help
```
and this should display some information about how to run the script.
In brief, if you have a folder. Put the config file (see info below) in the root folder of the folder you want to analyze. For example if you want to analyze `/Users/finsberg/data/experiment1` then you should also have a file at `/Users/finsberg/data/experiment1/config.yaml`. If is also possible to specify a path to this file

To analyze the the folder you execute the command

```
python -m mps_automation <folder>
```
for example
```
python -m mps_automation /Users/finsberg/data/experiment1
```
(note that you can also use relative paths).

Once this is done you should see the following files and folder appearing in your experiment folder

- `database.db`
  - This is file containing all the information about all the files in the experiment. This is basically a huge table (or SQLite database) where each row is one recording that contains information about chips, media, doses, drugs, pacing, trace type, as well as the full analysis. You can open and inspect this file with to tool like [DB Browser for SQLite](https://sqlitebrowser.org)
- `data.xlsx`
  - This is an excel file with a few sheets summarizing the analysis of the folder
- `plots`
  - TBW


## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[finsberg/cookiecutter-pypackage](https://github.com/finsberg/cookiecutter-pypackage)
project template.

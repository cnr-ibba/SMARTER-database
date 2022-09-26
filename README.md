SMARTER Database
==============================

[![Pytest Workflow](https://github.com/cnr-ibba/SMARTER-database/actions/workflows/pytest-workflow.yml/badge.svg)](https://github.com/cnr-ibba/SMARTER-database/actions/workflows/pytest-workflow.yml)
[![Lint Workflow](https://github.com/cnr-ibba/SMARTER-database/actions/workflows/lint-workflow.yml/badge.svg)](https://github.com/cnr-ibba/SMARTER-database/actions/workflows/lint-workflow.yml)
[![Coverage Status](https://coveralls.io/repos/github/cnr-ibba/SMARTER-database/badge.svg?branch=master)](https://coveralls.io/github/cnr-ibba/SMARTER-database?branch=master)
[![Documentation Status](https://readthedocs.org/projects/smarter-database/badge/?version=latest)](https://smarter-database.readthedocs.io/en/latest/?badge=latest)

SMARTER-database aims to collect data produced by the WP4 group in the context of
the [SMARTER project](https://www.smarterproject.eu/) and to merge them with
already available data.

Project Organization
--------------------

    ├── data
    │   ├── external        <- Data from third party sources.
    │   ├── interim         <- Intermediate data that has been transformed.
    │   ├── processed       <- The final, canonical data sets for modeling.
    │   └── raw             <- The original, immutable data dump.
    |
    ├── database            <- MongoDB smarter database docker-composed image
    │
    ├── docs                <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models              <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks           <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                          the creator's initials, and a short `-` delimited description, e.g.
    │                          `1.0-jqp-initial-data-exploration`.
    │
    ├── references          <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports             <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures         <- Generated graphics and figures to be used in reporting
    │
    ├── src                 <- Source code for use in this project.
    │   ├── __init__.py     <- Makes src a Python module
    │   │
    │   ├── data            <- Scripts to download or generate data
    │   │
    │   ├── features        <- Scripts to turn raw data into features for modeling
    │   │
    │   ├── models          <- Scripts to train models and then use trained models to make
    │   │   │                  predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization   <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    |
    ├── tests               <- Folder to test python modules / scripts
    │
    ├── HISTORY.rst         <- Project change log
    ├── LICENSE             <- Project LICENSE
    ├── Makefile            <- Makefile with commands like `make data` or `make train`
    ├── README.md           <- The top-level README for developers using this project.
    ├── TODO.md             <- Stuff that need to be done
    ├── environment.yml     <- Conda environment file
    ├── pytest.ini          <- Configuration file for `pytest` testing environment
    ├── requirements.txt    <- The requirements file for reproducing the analysis environment, e.g.
    │                          generated with `pip freeze > requirements.txt`
    ├── setup.py            <- makes project pip installable (pip install -e .) so src can be imported
    ├── test_environment.py <- Helper script to test if environment is properly set
    └── tox.ini             <- Tox file with settings for running tox; see tox.readthedocs.io

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>

Commands
========

The Makefile contains the central entry points for common tasks related to this project::

    $ make help
    $ make create_environment
    $ conda activate SMARTER-database
    $ make requirements

.. click:: src.data.add_breed:main
    :prog: src/data/add_breed.py
    :nested: full

.. click:: src.data.import_affymetrix:main
    :prog: src/data/import_affymetrix.py
    :nested: full

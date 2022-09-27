
The Data Import Process
=======================

.. contents:: Table of Contents

When calling the ``make data`` step of SMARTER-database data generation, a series
of steps are performed in order to process raw data and to generate the final dataset.
This document tries to describe how the data import process work and how to add
new data to the SMARTER-database dataset.

Defining a new dataset
----------------------

The data import process start by defining a dataset as a zip archive, which could
contain *genotype* or *phenotype* information (or other metadata). Dataset can also
be classified as *foreground* or *background* respectively if they are generated
in the context of the *SMARTER* project or before it. Accordingly to data source
type and provenience, you have to define a record in the proper ``.csv`` file
in ``data/raw`` folder, like the following::

    #;File;Uploader;Size;Partner;Country;Species;Breed;N of Individuals;Gene Array;Chip Name
    3;ADAPTmap_genotypeTOP_20161201.zip;smarterdatabase-admin;43.68MB;AUTH;36 Countries;Goat;144 breeds;4653;Genotyping data in plink binary format;IlluminaGoatSNP50

Next, dataset need to be imported by calling ``src/data/import_datasets.py``
with the proper dataset type and input file, like the following example:

.. code-block:: bash

    python src/data/import_datasets.py \
        --types genotypes background \
        data/raw/genotypes-bg.csv \
        data/processed/genotypes-bg.json

the last command argument will be the output file where to store a dump of the
:py:class:`Dataset <src.features.smarterdb.Dataset>` objects of the same type.
This command will add this dataset into the SMARTER-database and will unpack
its content in a folder with the sample *MongoDB* ``ObjectID`` inside the
``data/interim`` folder. This let you to analyze and process the dataset content
using the SMARTER-database ``src.features`` code. For more information, see the
:ref:`import_datasets.py <import_datasets>` help.

Exploring data with Jupyter-lab
-------------------------------

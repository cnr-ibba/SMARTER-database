
The Data Import Process
=======================

.. contents:: Table of Contents

When calling the ``make data`` step of SMARTER-database data generation, a series
of steps are performed in order to process raw data and to generate the final dataset.
This document tries to describe how the data import process work and how to add
new data to the SMARTER-database dataset. To add a new dataset into SMARTER-database,
you need to call some script with specific option in some section of the ``Makefile``
file. The order in which those import scripts are called matters, since importing
a sample into SMARTER-database means generating a unique ``smarter_id``, which need
to be stable, in order to track the same object when updating the database or
in different releases. Scripts are written in order to be idempotent: calling the
same script twice with the same parameters will produce the same final result.

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
        data/raw/genotypes-bg.csv

This command will add this dataset as a new
:py:class:`Dataset <src.features.smarterdb.Dataset>` object into the SMARTER-database
and will unpack its content in a folder with the *MongoDB* ``ObjectID`` inside the
``data/interim`` folder. This let you to analyze and process the dataset content
using the SMARTER-database ``src.features`` code. For more information, see the
:ref:`import_datasets.py <import_datasets>` help.

Exploring data with Jupyter Lab
-------------------------------

First step of data-import is *data exploration* using Jupyter Lab: this step require
manual intervention to understand if data could be imported or if some fixing steps
are required. Common issues in datasets could
be having different breeds with the same code, or using different codes to specify
the same breeds. Other issues that can arise when sample names within the genotype
file are different from the ones used in metadata: In those case, you have to define
a new metadata file where there will be the proper correct value in correspondence
of the wrong value. In this step you could check the coding format of genotypes,
by calling the proper :py:class:`SmarterMixin <src.features.plinkio.SmarterMixin>`
derived class. In this step you can also integrate metadata relying on external
data sources or you can fix some stuff related to metadata. Start Jupyter Lab
(in an activated conda environment) with:

.. code-block:: bash

    jupyter lab

Then create a new notebook according your needs. Please, see the
`notebook section <https://drivendata.github.io/cookiecutter-data-science/#notebooks-are-for-exploration-and-communication>`__
in the `Cookiecutter Data Science <https://drivendata.github.io/cookiecutter-data-science/>`__
project for more information.

Adding breeds to the database
-----------------------------

First step of data import is to add breeds in to the database: If the dataset have
one or few breeds, you could define a new breed object by calling
:ref:`add_breed.py <add_breed>` like this:

.. code-block:: bash

    python src/data/add_breed.py --species_class sheep \
        --name Texel --code TEX --alias TEXEL_UY \
        --dataset TEXEL_INIA_UY.zip

where the ``--species_class`` parameter specifies the source species ``Goat`` or
``Sheep``, ``--name`` and ``--code`` specify the breed name and code used in the
SMARTER-database respectively, the ``--alias`` specifies the FID (the *code*) used
in the genotype file and the ``--dataset`` parameter specifies the dataset
sources of the sample we want to add. If you have to manage very different breeds
in the same submissions, it's better to create breeds from a metadata file. In
such case, you can create your new breeds with a different script:

.. code-block:: bash

    python src/data/import_breeds.py --species_class Sheep \
        --src_dataset=ovine_SNP50HapMap_data.zip \
        --datafile ovine_SNP50HapMap_data/kijas2012_dataset_fix.xlsx \
        --code_column code --breed_column Breed \
        --fid_column Breed --country_column country

in such case, we will have a ``--src_dataset`` and ``--dst_dataset`` which let
to specify the dataset where the metadata information are retrieved (using the
``--datafile`` option) and the dataset where these information will be applied.
The other parameters let to specify which columns of the metadata file will be
used when defining a new breed. See :ref:`import_breeds.py <import_breeds>`
documentation for more information.

.. note::

    Breed ``name`` and ``code`` are unique in the same species (enforced by MongoDB):
    if you have the same breed in two different dataset, you need to call those
    command twice: first time you will create a new
    :py:class:`Breed <src.features.smarterdb.Breed>` object with the alias used
    in the first dataset. Every other call on the same breed, will update the same
    object to support also the new alias in the other dataset.

Adding samples to the database
------------------------------

Samples can be added in two ways: the first is when converting data from genotype
files, the second is by processing metadata information. The first approach should
be used when you have a single breed in the whole genotype file, and the breed
``code`` in the genotype file have already a
:py:class:`Breed <src.features.smarterdb.Breed>` instance in the SMARTER-database:
this is the simplest data file, when data belongs to the same country and breed.
With this situation, you could create samples while processing the genotype
file simply by adding the ``--create-samples`` flag to the appropriate importing
script (for more information, see :ref:`Process PLINK-like files`,
:ref:`Process ILLUMINA ROW files` and :ref:`Process AFFIMETRIX files` sections)

The second approach need to be used when you have different breeds in you genotype
file, or there are additional information that can't be derived from the genotype
file, like the country of origin, the sample name or the breed codes which
could have different values respect to the values stored in the genotype file.
Other scenario could be *illumina row* or *affymetrix report* files which don't
track the FID or other types of information outside sample names and genotypes.
Another case is when your genotype files contains more samples than in the metadata
file, for example, when you want to track in SMARTER-database only a few samples:
in all these cases, samples need to be created **before** processing genotypes,
using the :ref:`import_samples.py <import_samples>` script:

.. code-block:: bash

    python src/data/import_samples.py --src_dataset Affymetrix_data_Plate_652_660.zip \
        --datafile Affymetrix_data_Plate_652_660/Uruguay_Corriedale_ID_GenotypedAnimals_fix.xlsx \
        --code_all CRR --id_column "Sample Name" \
        --chip_name AffymetrixAxiomOviCan --country_all Uruguay \
        --alias_column "Sample Filename"

like :ref:`import_breeds.py <import_breeds>`, we have ``--src_dataset``
and ``--datafile`` to indicate where our metadata file is located; if our
genotype file is located in the same dataset of metadata, we can omit the
``--dst_dataset`` parameter. Breed codes and country can be set to the same values
with the ``--code_all`` or ``--country_all`` parameters, or can be read from metadata
file like the following example:

.. code-block:: bash

    python src/data/import_samples.py --src_dataset greece_foreground_sheep.zip \
        --dst_dataset AUTH_OVN50KV2_CHIOS_FRIZARTA.zip \
        --datafile greece_foreground_sheep/AUTH_OVN50KV2_CHIOS_FRIZARTA.xlsx \
        --code_column breed_code --id_column sample_name \
        --chip_name IlluminaOvineSNP50 --country_column Country

Please, look at :ref:`import_samples.py <import_samples>` help page to have more
info about the sample creation process.

Processing genotype files
-------------------------

Converting genotypes to ILLUMINA TOP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Process PLINK-like files
^^^^^^^^^^^^^^^^^^^^^^^^

Process ILLUMINA ROW files
^^^^^^^^^^^^^^^^^^^^^^^^^^

Process AFFIMETRIX files
^^^^^^^^^^^^^^^^^^^^^^^^

Adding metadata information
---------------------------

Merging datasets together
-------------------------

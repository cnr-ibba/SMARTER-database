
Loading variants into database
==============================

.. contents:: Table of Contents

When calling ``make initialize`` a series of steps are performed to
initialize the MongoDB database by loading variants information. This process
is independent from the :ref:`data generation <Processing genotype files>` step,
but those information are used to convert genotype files to the same format and
produce the final genotype dataset.
Information on variants need to be loaded for both SMARTER species (*Goat* and *Sheep*)
in order to do this data conversion. Some accessory information
are also required, for example ``rs_is``, since the same SNP can be called
with different names.

The variant collections
-----------------------

Mainly the variations are modelled around Illumina variants described in their
chips, since the majority of genotype files are produced using this technology.
However, those data need to support also the Affymetrix manufacturer and even
data produced from Whole Genome Sequencing (WGS). To accomplish this, variants
have additional fields as described by
:py:class:`VariantSpecies <src.features.smarterdb.VariantSpecies>` class, in order to support
different sources of information. Variants derived from Affymetrix technology or
by WGS are retrieved and replaced with the proper Illumina variants when possible,
in order to make possible the comparison between samples derived from different
technologies. When genotypes are processed during the
:ref:`data import process<Processing genotype files>`, variants are retrieved
relying their names or attributes like genomic positions or ``rs_id``, and genotypes
are checked against database and then converted with
:ref:`illumina TOP <Converting genotypes to Illumina TOP>` coding convention.

About supported assemblies
--------------------------

Received genotype data could come from different chips which relies on different
assemblies. Data generated long time ago could refer a very old or deprecated genome
assembly, and even data generated with the same chip could have different positions
since the probe mapping is a process continuously under revision. Considering this,
we can't trust genomic positions when processing genotype files, the only thing
stable in genotype files is the SNP *name*: this is the reason why we chose to
use SNP names to update genomic positions. We upload evidences for different assemblies
and chips in order to represent every SNP processed in genotype file, but we convert
genomic positions and genotypes relying only on one evidence: this could introduce
some errors maybe non present in latest assemblies, however this genome assembly
is consistent between genotype files, and this let to compare genotypes across
different dataset produced by different platforms.
When we first upload a SNP, we assign an initial
:py:class:`Location <src.features.smarterdb.Location>` object with a ``version``
and ``imported_from`` attribute in which track the genome assembly *version* and
the *source* of information. This let us to further update the same location, if
the assembly and the source is the same (for example, with a more recent manifest
file) or store another :py:class:`Location <src.features.smarterdb.Location>`
object to manage a new genomic position from a
different evidence. This let us also to convert from one assembly to another one,
since all the available genomic locations are stored within the SNP itself.

At this time, the genome assemblies we support are ``OAR3`` for *Sheep* and
``ARS1`` for *Goat* genome: they are not the latest assembly versions, however
they are supported by genome browser like `Ensembl <https://www.ensembl.org/index.html>`__
or `UCSC <https://genome.ucsc.edu/cgi-bin/hgGateway>`__. We plan to support more
recent assemblies to facilitate the data sharing in the future.

Upload the supported chips
--------------------------

First step in database initialization is loading the supported chip into
:py:class:`SupportedChip <src.features.smarterdb.SupportedChip>` documents. You need to
prepare a JSON file in which at least the chip name and the species is specified:
This chip name will be assigned to
:py:class:`VariantSpecies <src.features.smarterdb.VariantSpecies>`
defined within this chips and also to
:py:class:`SampleSpecies <src.features.smarterdb.SampleSpecies>` and
:py:class:`Dataset <src.features.smarterdb.Dataset>`. Here is an example of
such JSON file:

.. code-block:: json

    [
        {
            "name": "IlluminaOvineSNP50",
            "species": "Sheep",
            "manifacturer": "illumina",
            "n_of_snps": 0
        },
        {
            "name": "WholeGenomeSequencing",
            "species": "Sheep"
        }
    ]

Next, you can upload the chip name using :ref:`import_snpchips.py <import_snpchips>`:

.. code-block:: bash

    python src/data/import_snpchips.py --chip_file data/raw/chip_names.json

For more information, see :ref:`import_snpchips.py <import_snpchips>` manual page.

Import SNPs from manifest files
-------------------------------

In order to define a :py:class:`VariantSpecies <src.features.smarterdb.VariantSpecies>`
object, you need to load such SNP from a manifest file and specify the source of
such location. After a SNP object is created, you can add additional location
evidences, or update the same genomic location using a more
recent manifest file. Since this database is modelled starting from Illumina chips,
its better to define all the Illumina SNPs before: after that, if an Affymetrix
chip has a correspondence with a SNP already present, the new location source can be
integrated with the illumina genotype. To upload SNP from an illumina manifest
file, simply type:

.. code-block:: bash

    python src/data/import_manifest.py --species_class sheep \
        --manifest data/external/SHE/ILLUMINA/ovinesnp50-genome-assembly-oar-v3-1.csv.gz \
        --chip_name IlluminaOvineSNP50 --version Oar_v3.1 --sender AGR_BS

where the ``--species_class`` must be one of *Sheep* or *Goat* and ``--manifest``,
``--chip_name`` and ``--version`` need to specify the manifest file location, a
:py:class:`SupportedChip <src.features.smarterdb.SupportedChip>` ``name`` already
loaded into database and the assembly version. To upload data from an Affymetrix
manifest file, there's another script:

.. code-block:: bash

    python src/data/import_affymetrix.py --species_class sheep \
        --manifest data/external/SHE/AFFYMETRIX/Axiom_BGovis2_Annotation.r1.csv.gz \
        --chip_name AffymetrixAxiomBGovis2 --version Oar_v3.1

where the parameters required are similar to the Illumina import process. For
more information see :ref:`import_manifest.py <import_manifest>` and
:ref:`import_affymetrix.py <import_affymetrix>` manual pages.

Import locations from SNPchiMp
------------------------------

Another useful source of information come from the `SNPchiMp database <https://webserver.ibba.cnr.it/SNPchimp/>`__,
which was a project in which SNPs belonging to Affymetrix or Illumina manufacturers
where loaded with their genome alignment from `dbSNP <https://www.ncbi.nlm.nih.gov/snp/>`__
database: This lets to convert coordinates and genotypes between different genomic
assemblies. Unfortunately, after dbSNP release ``151`` SNPs from animals like *Sheep* and *Goat*
are not more managed by NCBI but were transferred to `EBI EVA <https://www.ebi.ac.uk/eva/>`__.
This implies update importing script data and update database like SNPchiMp. At
the moment SNPchiMp data are the main data used from assemblies ``OAR3``, ``OAR4``
and ``CHI1``, while ``ARS1`` assembly is currently managed from manifest file
(which is more recent than SNPchiMp). We plan to re-map the probes and to integrate
data with EVA, in order to solve genomic locations for all the SNPs and having the
latest evidences and *cross-reference* id like ``rs_id``. To upload data from SNPchiMp,
simply download the entire datafile for a certain assembly and chip. Then call the
following program:

.. code-block:: bash

    python src/data/import_snpchimp.py --species_class sheep \
        --snpchimp data/external/SHE/SNPCHIMP/SNPchimp_SHE_SNP50v1_oar3.1.csv.gz \
        --version Oar_v3.1

see :ref:`import_snpchimp.py <import_snpchimp>` manual page for additional information.

Import locations from genome projects
-------------------------------------

The last source of evidence that is modelled by SMARTER-database comes from
*Sheep* and *Goat* genome initiatives like `Sheep HapMap <https://www.sheephapmap.org/>`__
or `VarGoats <http://www.goatgenome.org/vargoats.html>`__, which can re-map chips
on latest genome assemblies. However, this mapping process can have some issues
(see `here <https://github.com/cnr-ibba/SMARTER-database/blob/master/notebooks/exploratory/0.15.0-bunop-check_sheep_coordinates.ipynb>`__,
`here <https://github.com/cnr-ibba/SMARTER-database/blob/master/notebooks/exploratory/0.15.1-bunop-about_sheep_coordinates.ipynb>`__ and
`here <https://github.com/cnr-ibba/SMARTER-database/blob/master/notebooks/exploratory/0.16.0-bunop-check_goat_coordinates.ipynb>`__
for example) so this source of evidence need to be revised with *Sheep* and *Goat*
genomic projects. To upload this type of information in database, you can do as
following:

.. code-block:: bash

    python src/data/import_consortium.py --species_class sheep \
        --datafile data/external/SHE/CONSORTIUM/OvineSNP50_B.csv_v3.1_pos_20190513.csv.gz \
        --version Oar_v3.1

please, refer to :ref:`import_consortium.py <import_consortium>` manual page for additional information.

=======
History
=======

TODO
^^^^

* ``alleles`` and ``illumina_top`` attributes should be referred to variants, while
  in ``locations`` should be stored the read value from data source. Alleles and
  illumina_top shouldn't change within the same SNP, indipendently from data source
* fix linter issues
* Check chromosomes in *Variants locations*: mind to **scaffold**, **null**, and
  **non-autosomal** chromosomes for *Goat* and *Sheep*
* Skip ``null`` fields when importing datasets
* Import foreground genotypes
  - import french sheep data
  - import greece goat data
  - import grece sheep data (20210407 and 20200731)
* Enable continuous integration
  - ReadTheDocs
* Rename objects (use names in a consistent way)

0.4.0.dev0
----------

* load data from affymetrix manifest
* calculate *illumina_top* from affymetrix sequence
* Test import data from *snpchimp*
* Import ``OARV4`` coordinates
* ``data/common`` module refactoring
* Fix bug when importing a datasource
* Model affymetrix fields
* Read from affymetrix manifest file
* Track illumina manifactured date

0.3.1 (2021-06-11)
------------------

* Upgrade dependencies
* Enable continuous integration
  - Github Workflow
  - Coverage

0.3.0 (2021-05-19)
------------------

Features
^^^^^^^^

* Deal with multi-sheets ``.xlsx`` documents
* Import phenotypes (from a *source* dataset to a *destination* dataset)
* Define phenotype attribute as a ``mongoengine.DynamicDocument`` field
* Import metadata or phenotype *by breeds* or *by samples*
* Import metadata (from a *source* dataset to a *destination* dataset)
* Forcing ``plink`` **chrom** options when converting in binary formats
* import data from *ADAPTmap* project
  - Import goat breeds (from a *source* dataset to a *destination* dataset)
  - Import goat data from plink files
  * Import goat metadata
* Import goat data from manifest and snpchimp
* configure ``mongodb-express`` credentials
* Add Goat Related tables
  - add ``variantGoat`` collection
  - add ``sampleGoat`` collection

0.2.3 (2021-05-03)
------------------

Features
^^^^^^^^

* Unset ped columns if relationship can't be derived from data (ex. *brazilian BSI*)
* Deal with geographical coordinates
* Add features to samples (relying on metadata file)

0.2.2 (2021-04-29)
------------------

Features
^^^^^^^^

* Breed name should be a unique key within species
* make rule to clean-up ``interim`` data
* skip already processed file from import
* Deal with ``mother_id`` and ``father_id`` (search for ``smarter_id`` in database)
* Deal with multi-countries dataset
  - track country in aliases while importing breeds from dataset

0.2.1 (2021-04-22)
------------------

Features
^^^^^^^^

* Track ``chip_name`` with samples
* Deal with binary plink files
* Search breed by *aliases* used in ``dataset``:
  - match *fid* with breed *aliases* in ``dataset``
  - store *aliases* by ``dataset``
* Add breeds from ``.xlsx`` files

0.2.0 (2021-04-15)
------------------

Features
^^^^^^^^

* Merge multiple files per dataset
* Import from an *illumina report* file
* Deal with *AB* allele coding
* Deal with plink text files using modules
* Fix *SNPchiMp* data import
* Determine ``illumina_top`` coding as a *property* relying on database data
* Support multi-manifest upload (extend database with *HD* chip)
* Deal with compressed manifest
* Add breeds with *CLI*
* Check coordinates format relying on *DRM*
* Test stuff with ``mongomock``

0.1.0 (2021-03-29)
------------------

Features
^^^^^^^^

* Start with project documentation
* Explore background datasets
* Merge plink binary files
* Convert from ``forward`` to ``illumina_top`` coordinates
* Convert to plink binary format
* Manage database credentials
* Import samples into ``smarter`` database while fixing coordinates and genotypes
* Configure tox and sphinx environments
* Model breeds in ``smarter`` database
* Import *datasets* into database
* Read from *dbSNP xml dump* file
* Import *SNPchiMp* data into ``smarter`` database
* Import *Illumina manifest* data into database
* Model objects with ``mongoengine``
* Model *smarter ids*
* Configure environments, requirements and dependencies

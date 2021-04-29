=======
History
=======

TODO
^^^^

* Add features to samples (relying on metadata file)

0.2.2.dev0
----------

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

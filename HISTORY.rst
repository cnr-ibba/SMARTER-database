=======
History
=======

0.2.0.dev0
----------

TODO
^^^^

* Import from an *illumina report* file
* Deal with *AB* allele coding
* Track ``chip_name`` with samples
* Deal with plink text files using modules
* make rule to clean-up ``interim`` data

Features
^^^^^^^^

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
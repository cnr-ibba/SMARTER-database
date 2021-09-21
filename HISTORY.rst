=======
History
=======

TODO
^^^^

* ``illumina_top`` attribute should be referred to variants, while
  in ``locations`` should be stored the read value from data source. 
  illumina_top shouldn't change within the same SNP, indipendently from data source
* Check chromosomes in *Variants locations*: mind to **scaffold**, **null**, and
  **non-autosomal** chromosomes for *Goat* and *Sheep*
* Import foreground genotypes
  - import greece goat data
  - import greece sheep data (1 datasets)
* Enable continuous integration
  - ReadTheDocs
* Rename objects (use names in a consistent way)
* Generate output files for *OARV4* and *CHIR1*
* Check coordinates with sheep and goat genome projects
* Release a *smarter* coordinate version with information on every variant defined 
  in database (which will be used as reference)
* Have an ``update_breed`` script to add an alias to an existent breed
* if ``src_dataset`` and ``dst_dataset`` are equals, provide only ``dst_dataset``
  both in *import_samples* and *import_metadata* scripts
* define a collection for all available *purpose* phenotypes

0.4.2.dev0
----------

* Import greek *frizarta-chios-pelagonia* sheep dataset
* Import greek *frizarta-chios* sheep dataset
* Import sweden foreground goat dataset
* Update *ADAPTmap* breed names and phenotypes import
* Check that breed exists while inserting phenotype data
* Import french foreground sheep dataset
* Use ``elemMatch`` in projection in ``plinkio.SmarterMixin.fetch_coordinates``
  (ex: ``VariantSheep.objects.fields(elemMatch__locations={"imported_from": "SNPchiMp v.3", "version": "Oar_v4.0"})``)
* Use ``elemMatch`` to search a SNP within the desidered coordinate systems in ``plinkio.SmarterMixin.fetch_coordinates``
* Skip SNPchimp indels when importing from SNPchimp
* Skip illumina indels when reading from manifest

0.4.1 (2021-09-08)
------------------

* Add ``chip_name`` in Dataset (database value, not user value)
* Skip ``null`` fields when importing datasets
* Import uruguay sheep affymetrix data
* Import from affymetrix dataset
* Rely on original affymetrix coordinate system to determine illumina top alleles
* Search samples *aliases* while importing genotypes
* Clearly state when creating samples (ignore samples if not defined in database)
* Track sample aliases for ``original_id``
* Import samples from file by providing *country* and *breeds* values as parameters
* Security updates
* Fix github Workflow

0.4.0 (2021-06-18)
------------------

* ``dbSNP`` feature library refactor
* fix linter issues
* Transform *affymetrix* unmapped chrom to ``0``
* Transform *SNPchiMp* unmapped chroms to ``0``
* ignore affymetrix insertions and deletions
* join affymetrix data with illumina relying on ``cust_id``
* define ``illumina_top`` from affymetrix flanking sequences
* load data from affymetrix manifest
* calculate *illumina_top* from affymetrix sequence
* Test import data from *snpchimp*
* Import ``OARV4`` coordinates
* ``data/common`` module refactoring
* Fix bug in importing dataset order
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

* Unset ped columns if relationship can't be derived from data (ex. *brazilian BSI*)
* Deal with geographical coordinates
* Add features to samples (relying on metadata file)

0.2.2 (2021-04-29)
------------------

* Breed name should be a unique key within species
* make rule to clean-up ``interim`` data
* skip already processed file from import
* Deal with ``mother_id`` and ``father_id`` (search for ``smarter_id`` in database)
* Deal with multi-countries dataset
  - track country in aliases while importing breeds from dataset

0.2.1 (2021-04-22)
------------------

* Track ``chip_name`` with samples
* Deal with binary plink files
* Search breed by *aliases* used in ``dataset``:
  - match *fid* with breed *aliases* in ``dataset``
  - store *aliases* by ``dataset``
* Add breeds from ``.xlsx`` files

0.2.0 (2021-04-15)
------------------

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

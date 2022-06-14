=======
History
=======

TODO
^^^^

* Check chromosomes in *Variants locations*: mind to **scaffold**, **null**, and
  **non-autosomal** chromosomes for *Goat* and *Sheep*
* Enable continuous integration
  - ReadTheDocs
* Rename objects (use names in a consistent way)
* Generate output files for *OARV4* and *CHIR1*
* Check coordinates with sheep and goat genome projects
* Release a *smarter* coordinate version with information on every variant defined
  in database (which will be used as reference)
* Map affymetrix snps in OARV3 coordinates
* define a collection for all available *purpose* phenotypes
* Check if ``rs_id`` is still valid or not (with EVA)

0.4.5 (2022-06-14)
------------------

* Update requirements
* Import data from Hungary `#53 <https://github.com/cnr-ibba/SMARTER-database/issues/53>`__
* Create a new sample when having the same ``original_id`` in dataset but for a different breed
* ``illumina_top`` is an attribute of variant, and is set when the first location
  is loaded.
* Check variants data before update `#56 <https://github.com/cnr-ibba/SMARTER-database/issues/56>`__
* Simplified ``import_affymetrix`` script
* Import custom affymetrix chips (*Oar_v3.1*)
* Support *source* and *destination* assemblies when importing from *plink* or
  *affymetrix* source files
* Deal with spaces in filenames while importing from plink
* Add ``affy_snp_id`` primary key
* Update ``import_affymetrix.py`` script
* Import data from Spain `#52 <https://github.com/cnr-ibba/SMARTER-database/issues/52>`__
* Fix 20220503 dataset breed and churra chip name
* Track manifest probe ``sequence``s by ``chip_name``
* Track ``probeset_id`` by ``chip_name``
* Search for affymetrix ``probeset_id`` in the proper ``chip_name`` while importing
  samples
* Track multiple ``rs_id``
* Fetch *churra* coordinates by ``rs_id`` and ``probeset_id`` and filter out unmanaged
  SNPs
* If ``src_dataset`` and ``dst_dataset`` are equals, provide only ``src_dataset``

0.4.4 (2022-02-28)
------------------

* Model location with MultiPointField
* Describe smarter metadata
* Import sweden goat metadata
* Import latest 290 samples greek dataset
* Fix issue with greek samples name (``B273`` converted into ``B273A``)
* Add latest 19 sheep greek samples
* Add a country collection
* Update dependencies

0.4.3 (2021-11-11)
------------------

* Add 270 Frizarta background samples
* Import from ab plink and support multiple missing letters
* Track database status and constants
* Add *foreground/background* type attribute in ``SampleSpecies``
* Update dependencies
* Add make rule to pack results and make checksum
* Move greek foreground metadata to a custom phenotypes dataset
* Update greek foreground metadata
* Import phenotypes from Uruguay
* Import phenotypes using alias
* Allow phenotypes for ambiguous sex animals
* Import french goat foreground dataset
* Pin ``plinkio`` to support *extra-chroms* in plink binary files
* Import 5 Sweden Sheep background genotypes
* Force *half-missing* SNPs to be MISSING
* Add the README.txt.ftp
* Bug fixed in importing multibreed reportfile (setting FID properly in output)

0.4.2 (2021-08-27)
------------------

* Set nullable ``ListField`` for sample *locations* and variant *consequences*
* Capitalize phenotype values (ie *milk* -> *Milk*)
* Import greek *chios-mytilini-boutsko* sheep dataset
* Track multiple location for sample (deal with transhumant breeds )
* Import greek *skopelios-eghoria* goat dataset
* Use sample data to deal with multi breeds illumina row files
* Determine fid from database with IlluminaReportIO
* Import greek *frizarta-chios-pelagonia* sheep dataset
* Import greek *frizarta-chios* sheep dataset
* Import sweden foreground goat dataset
* Update *ADAPTmap* breed names and phenotypes import
* Check that breed exists while inserting phenotype data
* Import french foreground sheep dataset
* Use ``elemMatch`` in projection in ``plinkio.SmarterMixin.fetch_coordinates``
  (ex: ``VariantSheep.objects.fields(elemMatch__locations={"imported_from": "SNPchiMp v.3", "version": "Oar_v4.0"})``)
* Use ``elemMatch`` to search a SNP within the desired coordinate systems in ``plinkio.SmarterMixin.fetch_coordinates``
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
* Import sheep coordinates from genome project
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
* Track illumina manufactured date

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

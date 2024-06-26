=======
History
=======

TODO
----

* Check chromosomes in *Variants locations*: mind to **scaffold**, **null**, and
  **non-autosomal** chromosomes for *Goat* and *Sheep*
* Rename objects (use names in a consistent way, ex *TOP*, *BOT*)
* Release a *smarter* coordinate version with information on every variant defined
  in database (which will be used as reference)
* Map affymetrix snps in *OARV3* coordinates
* Check if ``rs_id`` is still valid or not (with EVA)

0.4.10 (2024-05-28)
-------------------

* Fix issues with sample countries using reverse geocoding (`#112 <https://github.com/cnr-ibba/SMARTER-database/issues/112>`__)
  * fix country for *Merino* (Sheep)
  * fix country for *Sumavska* (Sheep)
  * fix GPS location for *Latxa* (Sheep)
  * fix country for *Karakul* (Sheep)
  * fix country for *Romanov* (Sheep)
  * fix country for *Suffolk* (Sheep)
  * fix country for *Texel* (Sheep)
* Manage python packages with `poetry <https://python-poetry.org/>`__ (`#128 <https://github.com/cnr-ibba/SMARTER-database/issues/128>`__)
* Add data for *Guisandesa* goats (`#117 <https://github.com/cnr-ibba/SMARTER-database/issues/117>`)
* Rename ``manifacturer`` into ``manufacturer``
* Convert genotypes from *top* to *forward* (`#111 <https://github.com/cnr-ibba/SMARTER-database/issues/111>`__)
* Update dependencies

0.4.9 (2023-09-27)
------------------

* Load phenotypes for *Fosses, Provencale* goat breeds
* Add sex for *Fosses, Provencale* goat breeds
* Add *sex* while importing metadata
* Load multiple phenotypes for *Boutsko foreground* sheeps
* Add multiple phenotypes as a list (`#103 <https://github.com/cnr-ibba/SMARTER-database/issues/103>`__)
* Update *datasets* metadata
* Update dependencies

0.4.8 (2023-06-28)
------------------

* Capitalize ``species_class`` parameter in ``src.data.import_breeds.py``
* Generate output files for *OARV4* and *CHIR1* (`#87 <https://github.com/cnr-ibba/SMARTER-database/issues/87>`__)
* Import data from *dbSNP152* (`#15 <https://github.com/cnr-ibba/SMARTER-database/issues/15>`__)
* Import data from *IGGC* (`#18 <https://github.com/cnr-ibba/SMARTER-database/issues/18>`__)
* Split ``import_consortium.py`` in ``import_isgc.py`` and ``import_iggc.py``
  to import data from Sheep and Goat genome *consortia* respectively
* Force data update when importing from consortium
* Track date when importing from consortium
* Determine ``illumina_top`` data directly from variant for Sheep when importing
  from *consortium* data
* Uniform *note* metadata field (add a *note* parameters in import metadata)
* Import data from *Cortellari et al 2021* (https://doi.org/10.1038/s41598-021-89900-2)
* Import data from *Burren et al 2016* (https://doi.org/10.1111/age.12476)
* Revise illumina A/B genotype tracking
* Import from Illumina report with only 3 columns in SNP list file
* Update dependencies

0.4.7 (2022-12-23)
------------------

* Import background data from *Gaouar et al 2017* (https://doi.org/10.1038/hdy.2016.86)
* Import from plink with illumina coding (as specified in manifest: not *top* nor *forward*)
* Import background data from *Belabdi et al 2019* (https://doi.org/10.1038/s41598-019-44137-y)
* Import background data from *Ciani et al 2020* (https://doi.org/10.1186/s12711-020-00545-7)
* Import background data from *Barbato et al 2017* (https://doi.org/10.1038/s41598-017-07382-7)
* Update species for *european mouflon*
* Support species update with ``import_metadata.py``
* Import 18 *welsh* breed as background genotypes
* Rename two *welsh* breeds
* Model *doi* in datasets
* Upgrade CI workflows to ``actions/cache@v3``
* Add ``SNPconvert.py`` script
* Import genotypes of other WPs coming from Uruguay
* Deal with affymetrix report with less SNPs than declared
* Add an option to skip coordinate check when importing affymetrix report
* Import from affymetrix a limited number of samples
* Skip sample creation when there's no alias
* Support for missing columns in affymetrix report files
* Support *invalid python names* in ``src.features.affymetrix.read_affymetrixRow``
* Update requirements
* Deal with missing files in ``import_datasets.py``
* Update Uruguay metadata locations
* Move *Galway* sheep to *Ireland* country (Ovine HapMap)

0.4.6 (2022-09-26)
------------------

* Update requirements
* Read from affymetrix A/B reportfile
* Import latest Uruguayan data (`#65 <https://github.com/cnr-ibba/SMARTER-database/issues/65>`__)
* Configure database connection (`#66 <https://github.com/cnr-ibba/SMARTER-database/issues/66>`__)
* Update sex in ped file if there are information in database
* Enable continuous integration for documentation (ReadTheDocs)
* Update documentation
* Track full species information in Sample (support for multi-species sheep and goats)
* Updated *isheep* exploration notebooks
* Deal with *unknown* countries and species
* Fix issues related on *alias* when creating samples or adding metadata
* Fetch variants using positions
* Import from plink using *genomic coordinates*
* Import *50K*, *600K* and *WGS isheep* datasets (`#47 <https://github.com/cnr-ibba/SMARTER-database/issues/47>`__)
* Fix issue in ``src.features.plinkio.plink_binary_exists``
* Code refactoring in ``src.features.plinkio``
* Import data from Sheep HapMap V2

0.4.5 (2022-06-14)
------------------

* Update requirements
* Import data from Hungary (`#53 <https://github.com/cnr-ibba/SMARTER-database/issues/53>`__)
* Create a new sample when having the same ``original_id`` in dataset but for a different breed
* ``illumina_top`` is an attribute of variant, and is set when the first location
  is loaded.
* Check variants data before update (`#56 <https://github.com/cnr-ibba/SMARTER-database/issues/56>`__)
* Simplified ``import_affymetrix`` script
* Import custom affymetrix chips (*Oar_v3.1*)
* Support *source* and *destination* assemblies when importing from *plink* or
  *affymetrix* source files
* Deal with spaces in filenames while importing from plink
* Add ``affy_snp_id`` primary key
* Update ``import_affymetrix.py`` script
* Import data from Spain (`#52 <https://github.com/cnr-ibba/SMARTER-database/issues/52>`__)
* Fix *20220503* dataset breed and *churra* chip name
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

* Model location with ``MultiPointField``
* Describe smarter metadata
* Import sweden goat metadata
* Import latest 290 samples greek dataset
* Fix issue with greek samples name (``B273`` converted into ``B273A``)
* Add latest 19 sheep greek samples
* Add a country collection
* Update dependencies

0.4.3 (2021-11-11)
------------------

* Add 270 *Frizarta* background samples
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
  - Import goat metadata

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

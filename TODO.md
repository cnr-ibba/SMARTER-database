
TODO
====

Database
--------

* load breeds into database
* Should I check genotype coding **before** importing dataset?
* create samples collection (one for goat, one for sheep)
* create a variation collection (one for goat, one for sheep)
  - determine unique values for *bottom*, *top*, *forward*
* a function to convert plink/text to plink/binary with plink
  - how to deal with extra-chroms?
* extract dataset file from an archive
* create a variation collection (for goat and sheep)
  - import ILLUMINA data with coordinates (make an entry for each snp)
  - import SNPchimp data into database (the proper variation collection)
  - parse dbSNP data and update position
  - parse EVA data and EnsEMBL data and update positions
* configure mongodb replica set and transactions:
  - https://docs.mongodb.com/manual/tutorial/enforce-keyfile-access-control-in-existing-replica-set/
  - https://stackoverflow.com/questions/61846280/how-to-add-configuration-for-mongodb-4-2-transaction-in-spring-boot
  - https://docs.mongodb.com/manual/tutorial/deploy-replica-set-for-testing/
* create a read only user `smarterro` (for web stuff?)
* manage python packages with [poetry](https://python-poetry.org/)
* upgrade `mongoengine` to solve warnings while generating documentation with `sphinx`
  (the `one-to-many-with-listfields` reference was fixed after version `0.23.0`)


TODO
====

Database
--------

* Add a counter collection for samples
* Get country code list
* define IDS like VarGoats format FRCH-PVC-0001 = CO(untry)SP(ecies)-BREED-ID
* load breeds into database
* create samples collection (one for goat, one for sheep)
* create a variation collection (one for goat, one for sheep)
* a function to convert plink/text to plink/binary with plink
  - how to deal with extra-chroms?
* extract dataset file from an archive
* create a variation collection (for goat and sheep)
  - import ILLUMINA data with coordinates (make an entry for each snp)
  - import SNPchimp data into database (the proper variation collection)
  - parse dbSNP data and update position
  - parse EVA data and EnsEMBL data and update positions
* configure replica set and transactions:
  - https://docs.mongodb.com/manual/tutorial/enforce-keyfile-access-control-in-existing-replica-set/
  - https://stackoverflow.com/questions/61846280/how-to-add-configuration-for-mongodb-4-2-transaction-in-spring-boot
  - https://docs.mongodb.com/manual/tutorial/deploy-replica-set-for-testing/

TODO
====

Code
----

* a function to convert plink/text to plink/binary with plink
  - how to deal with extra-chroms?
* extract dataset file from an archive (on-the-fly)
* manage python packages with [poetry](https://python-poetry.org/)
* mind permission while writing files/creating dirs


Database
--------

* Model 10K affymetrix dataset 
  * collect and upload 10k manifest file
  * move `AffymetrixAxiomOviCan` to `AffymetrixOvineSNP50`
  * add `AffymetrixOvineSNP10`
* Should I check genotype coding **before** importing dataset?
* create a variation collection (for goat and sheep)
  - parse dbSNP data and update position
  - parse EVA data and EnsEMBL data and update positions

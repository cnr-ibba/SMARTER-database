.. SMARTER Database documentation master file, created by
   sphinx-quickstart.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the SMARTER Database documentation!
==============================================

This documentation describe how the SMARTER database is made. This project is started
from `cookiecutter data science project template <https://www.redhat.com/sysadmin/suid-sgid-sticky-bit>`__
and was then adapted to model additional requirements. In order to work correctly
with this project, you will need both `Docker <https://www.docker.com/>`__ and
`Docker Compose <https://docs.docker.com/compose/>`__ installed and configured for your user.
You will need also `Anaconda <https://docs.anaconda.com/anaconda/>`__ to manage
project dependencies and installing required software.
After that you need to configure some stuff in order to properly use this project.

This project is currently managed with git: you should track only scripts or dependencies,
don't try to track ``data`` folder (which can be very large and could change in any
times) the ``.env`` configuration files (for security reasons) or any other files
declared in ``.gitignore`` file. By following the instruction in :ref:`Getting started`
section, you will be able to run your local instance of the *SMARTER-database* project!

Background
----------

Small ruminant populations play a fundamental role for the livelihood and
socio-economic well-being of human settlements, especially in marginal areas of
Europe. Under-utilized sheep and goat breeds may be highly valuable in
increasing the profitability of small ruminant farming in such marginal areas.
These breeds are valuable because they have peculiar and often atypical genetic
make-up which make them a potentially extraordinary resource to be exploited
for adaptation to (harsh) environments, resilience to farming conditions,
resistance to biotic and abiotic stressors, and the production of quality of
products of animal origin
(see `Biscarini et al. 2015 <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4340267/>`__).

The `SMARTER-database <https://github.com/cnr-ibba/SMARTER-database>`__ GitHub
project is a collection of tools and script to collect, standardize and provide
to the partners of the SMARTER Work Package 4 (WP4), and later to the whole community,
a collection of genotype data and metadata information in hardy goat and sheep
populations by combining new with already existing datasets.
Those data can be exploited to characterize the genetic diversity and demography
of sheep and goat breeds with a particular focus on underutilized breeds and to
contribute to understanding the genetic basis of resilience and adaptation to the
environment of hardy breeds.

This project is part of the `SMARTER project <https://www.smarterproject.eu/>`__
which aims to develop and deploy innovative strategies to improve Resilience and Efficiency
(R&E) related traits in sheep and goats.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2

   getting-started
   data-import
   commands
   modules
   history


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

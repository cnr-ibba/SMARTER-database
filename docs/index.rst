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

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2

   getting-started
   commands
   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

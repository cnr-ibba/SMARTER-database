
Getting started
===============

..
  This is where you describe how to get set up on a clean install, including the
  commands necessary to get the raw data (using the `sync_data_from_s3` command,
  for example), and then how to make the cleaned, final data sets.

The SMARTER-database project
----------------------------

Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute
irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Installation and configuration
------------------------------

Clone this project with GIT
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to install *SMARTER-database* project, you need to clone it
`from GitHub <https://github.com/cnr-ibba/SMARTER-database.git>`__ using git::

  $ git clone https://github.com/cnr-ibba/SMARTER-database.git

.. note::

  If you plan to install this project in a shared folder, take a look before at
  `Shared folders and permissions <https://bioinfo-guidelines.readthedocs.io/en/latest/general/sharing.html#shared-folders-and-permissions>`__
  and in particoular at the `Setting permissions <https://bioinfo-guidelines.readthedocs.io/en/latest/general/sharing.html#setting-permissions>`__
  section in the `BIOINFO Guidelines <https://bioinfo-guidelines.readthedocs.io/en/latest/>`__
  documentation

.. tip::

  In order to better share this project with other users on the same machine, its
  better to clone this project inside a directory with the **SGID** special permission
  (see `Using SGID <https://bioinfo-guidelines.readthedocs.io/en/latest/general/sharing.html#using-sgid>`__
  for more informations)

.. warning::

  Every file you create in a **SGID** directory will have the correct permissions
  and ownership, however if you **copy** a file throug ``scp``, ``rsync`` or you
  move a file from a non **SGID** directory, the permission will be the stardard
  ones defined for your user. You should check that permissions are correct after
  *moving* or *copying* files, in particoular for ``data`` directory. To add the
  **SGID** permission on the current directory and subfolder, you could do like
  this::

    $ find . -user $USER -type d -exec chmod g+s {} \;

  This command should be called inside a *interactive bash login session*, since
  bash will ignore commands which try to set the **SGID** permission.

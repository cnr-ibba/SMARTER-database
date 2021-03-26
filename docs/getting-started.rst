
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

Now enter into the smarter cloned directory with ``cd SMARTER-database``: from now
and in the rest of this documentation this ``SMARTER-database`` directory will be
referred as **the project home directory**::

  $ cd SMARTER-database
  $ export PROJECT_DIR=$PWD

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

Configure environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to work properly *SMARTER-database* need some environment variables defined
in two environment files. Those files **must not be tracked with GIT** for security
reasons, and should be defined **before** starting with this project.

The first ``.env`` file is located inside the ``database`` folder and is required
in order to start the *MongoDB* image and to set up the required collections and
validation constraints. So edit the ``database/.env`` file by setting these two variables::

  MONGODB_ROOT_USER=<smarter root database username>
  MONGODB_ROOT_PASS=<smarter root database password>

The second ``.env`` file need to be located in the **project HOME directory** and
need to define the smarter credentials required to access the MongoDB instance. Start
by this template and set your smarter credentials properly in ``$PROJECT_DIR/.env``
file::

  # Environment variables go here, can be read by `python-dotenv` package:
  #
  #   `src/script.py`
  #   ----------------------------------------------------------------
  #    import dotenv
  #
  #    project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
  #    dotenv_path = os.path.join(project_dir, '.env')
  #    dotenv.load_dotenv(dotenv_path)
  #   ----------------------------------------------------------------
  #
  # DO NOT ADD THIS FILE TO VERSION CONTROL!
  MONGODB_SMARTER_USER=<smarter username>
  MONGODB_SMARTER_PASS=<smarter password>

Start the MongoDB instance
^^^^^^^^^^^^^^^^^^^^^^^^^^

The smarter *MongoDB* instance is managed using ``docker-compose``: database will
instantiated and configured when you start the docker container for the first time.
Local files are written in the ``$PROJECT_DIR/database/mongodb-data`` that will
persist even when turning down and destroying docker containers . First check
that the ``database/.env`` file is configured correctly as described by the section
before. Next, in order to avoid annoying messages, set ``mongodb-home`` *sticky dir*
permission::

  $ chmod o+wt mongodb-home/

Next download, build and initialize the smarter database with::

  $ docker-compose pull
  $ docker-compose build
  $ docker-compose up -d

Now is time to define create a *smarter* user with the same credentials used in
your ``$PROJECT_DIR/.env`` environment file. You could do this using *docker-compose*
commands::

  $ docker-compose run --rm --user mongodb mongo sh -c 'mongo --host mongo --username="${MONGO_INITDB_ROOT_USERNAME}" --password="${MONGO_INITDB_ROOT_PASSWORD}"'

Then in the mongodb terminal crate the *smarter* user using the value of ``$MONGODB_SMARTER_PASS``
variable as the ``pwd`` argument::

  use admin
  db.createUser({user: "smarter", pwd: "<password>", roles: [{role: "readWrite", db: "smarter"}]})

For more information on the smarter *MongoDB* database usage, please refer to the
`README.md` documentation in the ``$PROJECT_DIR/database`` folder.

Setting up python environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Initialize and populate SMARTER database
----------------------------------------

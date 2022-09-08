
SMARTER MongoDB database
========================

This is the base folder of the *MongoDB* instance of the *SMARTER-database* project.
Such database runs and its managed using `docker-compose`, which store all database
related files in a local folder and will expose the standard `27017` *MongoDB* port
to the system. Moreover, database could be accessed through *mongodb-express* at
<http://localhost:8081>.

This directory is structured like this:

```text
database
├── docker-compose.yml
├── docker-entrypoint-initdb.d
├── mongodb-data
├── mongodb-home
└── README.md
```

`docker-compose.yml`: is the configuration file used by docker-compose.
`docker-entrypoint-initdb.d`: keeps the scripts used when database is initialized
for the first time.
`mongodb-data`: keeps the MongoDB data directory
`mongodb-home`: home directory of the mongodb user. Can be used to load or dump data
in or from database
`README.md`: this file

When you start the *docker-compose* image for the first time, the MongoDB database
is initialized and all the scripts defined in the `docker-entrypoint-initdb.d` are
executed using the mongodb root credentials stored in the `.env` configuration file.
After that, you could stop, destroy, re-create the *MongoDB* container without worrying
about smarter data: all database information are stored inside the `mongodb-data`
folder. If you want to wipe out the whole database and starting again from scratch,
you could remove the `mongodb-data` folder.

Create the .env configuration file
----------------------------------

In order to work properly, you need to define some environment variables in a
`.env` file inside this directory. This file is read by `docker-compose` when
invoked and it's required by docker containers in order to work properly. Please
set those environment variables in `.env` file:

```text
MONGODB_ROOT_USER=<smarter root database username>
MONGODB_ROOT_PASS=<smarter root database password>
MONGOEXPRESS_USER=<smarter mongoexpress username>
MONGOEXPRESS_PASS=<smarter mongoexpress password>
```

Fix permissions for mongodb-home folder
---------------------------------------

In order to avoid annoying messages, set `mongodb-home` *sticky dir* permission

```bash
chmod o+wt mongodb-home/
```

Build images and start them up
------------------------------

Initialize the smarter database with:

```bash
docker-compose pull
docker-compose build
docker-compose up -d
```

This will start and initialize the database (if not yet initialized)

Turn database down
------------------

In order to terminate *MongoDB* instance:

```bash
docker-compose down
```

This will terminate docker containers and remove them. Your data will persists in
the `mongodb-data` folder

Using smarter database
----------------------

Login with root credentials (inside this directory)

```bash
docker-compose run --rm --user mongodb mongo sh -c 'mongo --host mongo --username="${MONGO_INITDB_ROOT_USERNAME}" --password="${MONGO_INITDB_ROOT_PASSWORD}"'
```

Create a user for *smarter* database with `readWrite` permissions

```javascript
use admin
db.createUser({user: "smarter", pwd: "<password>", roles: [{role: "readWrite", db: "smarter"}]})
```

Login with smarter credentials

```bash
docker-compose run --rm --user mongodb mongo mongo --host mongo -u smarter -p <password> --authenticationDatabase admin
```

Or by starting a docker container and then login using console

```javascript
use admin
db.auth("smarter", "<password>")
```

Such smarter credentials need to be defined in the `SMARTER-database` root folder
in order to be used by the `SMARTER-database` scripts

Some useful queries in `smarter` database:

```javascript
// get only SNPchiMp location using projection (need to declare the projected column names)
db.variantSheep.findOne({}, {name: 1, rs_id: 1, locations: {$elemMatch: { imported_from: "SNPchiMp v.3"}}})
// count sample by breeds using aggregation framework
db.sampleSheep.aggregate([{ $group: { _id: { breed: "$breed" }, total: { $sum: 1 } } }])
// same query as before but relying on breed collection (which count samples
// when a new sample is added by application)
db.breeds.find({}, {name: 1, n_individuals: 1})
```

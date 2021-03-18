
SMARTER MongoDB database
========================

Login with root credentials (inside this directory)

```
$ docker-compose run --rm --user mongodb mongo sh -c 'mongo --host mongo --username="${MONGO_INITDB_ROOT_USERNAME}" --password="${MONGO_INITDB_ROOT_PASSWORD}"'
```

Create a user for smarter database

```javascript
use admin
db.createUser({user: "smarter", pwd: "<password>", roles: [{role: "readWrite", db: "smarter"}]})
```

Login with smarter credentials

```
$ docker-compose run --rm --user mongodb mongo mongo --host mongo -u smarter -p <password> --authenticationDatabase admin
```

Or by starting a docker container and then login using console

```javascript
use admin
db.auth("smarter", "<password>")
```

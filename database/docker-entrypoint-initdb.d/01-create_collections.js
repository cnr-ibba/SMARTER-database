
db.createCollection("breeds", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["species", "breed"],
      properties: {
        species: {
          bsonType: "string",
          description: "Species is a mandatory string"
        },
        breed: {
          bsonType: "object",
          required: ["name", "code"],
          properties: {
            name: {
              bsonType: "string",
              description: "Breed name is a mandatory string"
            },
            code: {
              bsonType: "string",
              description: "Breed code is a mandatory string"
            },
          }
        },
        nIndividuals: {
          bsonType: "int",
          minimum: 0,
          description: "Number of individuals of a certain breed"
        }
      }
    }
  }
})

// create a unique index case insensitive
db.breeds.createIndex( { "species": 1, "breed.code": 1 }, { unique: true, collation: { locale: 'en', strength: 1 } } )

// create a collection for sheep samples
db.createCollection("sampleSheep", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["smarterId", "originalId"],
      properties: {
        smarterId: {
          bsonType: "string",
          description: "this is the smarter internal id"
        },
        originalId: {
          bsonType: "string",
          description: "this is the original sample id submitted by partners"
        }
      }
    }
  }
})

// create a unique index case insensitive
db.sampleSheep.createIndex( { "smarterId": 1 }, { unique: true } )

// create a collection for counters
db.createCollection("counters", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["sequence_value"],
      properties: {
        sequence_value: {
          bsonType: "int",
          description: "last sequence value"
        }
      }
    }
  }
})

// initialize counter values
db.counters.insertMany([
  {
    _id: "sampleSheep",
    sequence_value: NumberInt("0")
  },
  {
    _id: "sampleGoat",
    sequence_value: NumberInt("0")
  },
])

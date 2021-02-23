
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

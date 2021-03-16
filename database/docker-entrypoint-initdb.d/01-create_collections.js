
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

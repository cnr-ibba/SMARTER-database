
// https://medium.com/idomongodb/mongodb-shell-cool-things-you-can-do-in-db65b6570468
print("")
print("As always sir, a great pleasure watching you work")
print("")

prompt = function() {
  if (typeof db == 'undefined') {
    return '(nodb)> ';
  }
  // Check the last db operation
  try {
    db.runCommand({getLastError:1});
  }
  catch (e) {
    print(e);
  }
  return db+"> ";
};

var no = function() {
  print("Not on my watch.");
};

// Prevent dropping databases
db.dropDatabase = DB.prototype.dropDatabase = no;

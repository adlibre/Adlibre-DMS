function(doc) {
     if (doc.doc_type == "CouchDocument")
          emit(doc._id, {rev: doc._rev});
}

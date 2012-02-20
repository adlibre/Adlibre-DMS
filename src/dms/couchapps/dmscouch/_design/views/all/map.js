function(doc) {
     if (doc.doc_type == "CouchDocument")
          emit(doc._id, doc);
}

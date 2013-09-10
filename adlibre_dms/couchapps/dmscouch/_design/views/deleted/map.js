function(doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted == "deleted") {
            emit(doc._id, {rev: doc._rev});
        }  // if deleted
    }  // if doc_type
}  // function
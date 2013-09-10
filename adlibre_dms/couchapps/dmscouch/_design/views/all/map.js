function(doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted != "deleted") {
            emit(doc._id, {rev: doc._rev});
        }
    }
}
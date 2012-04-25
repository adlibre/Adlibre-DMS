function(doc) {
    if (doc.doc_type == "CouchDocument") {
        for(var key in doc.mdt_indexes) {
            emit(
                [key, doc.mdt_indexes[key]] ,  {rev: doc._rev}
            );// emit
        };// for
    }; //if doc_type
} //function
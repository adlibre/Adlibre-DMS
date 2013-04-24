function(doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted == "deleted") {
            pass
        } else {
            for(var key in doc.mdt_indexes) {
                emit(
                    [doc.metadata_doc_type_rule_id, key, doc.mdt_indexes[key]],  {rev:doc._rev}
                );// emit
            };// for
        }; //deleted
    } //if doc_type
} //function
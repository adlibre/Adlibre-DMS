function(doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted != "deleted") {
            for(var key in doc.mdt_indexes) {
                emit([doc.metadata_doc_type_rule_id, key, doc.mdt_indexes[key]],  {rev:doc._rev});
            }  // for
        }  //deleted
    } //if doc_type
} //function
function(doc) {
    if (doc.doc_type == "CouchDocument") {
        for(var key in doc.mdt_indexes) {
            emit(
                    [doc.metadata_doc_type_rule_id, key, doc.mdt_indexes[key]],  {rev: doc._rev, metadata_doc_type_rule_id: doc.metadata_doc_type_rule_id, single_suggestion: doc.mdt_indexes[key]}
            );// emit
        };// for
    }; //if doc_type
} //function
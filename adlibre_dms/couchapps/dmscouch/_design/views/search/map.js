function(doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted != "deleted") {
            for(var key in doc.mdt_indexes) {
                emit(
                    [ key, doc.mdt_indexes[key] , doc.metadata_doc_type_rule_id ],
                    {rev: doc._rev, metadata_doc_type_rule_id: doc.metadata_doc_type_rule_id} // metadata_doc_type_rule_id is required for search results sorting
                );// emit
                emit(
                    [ key, doc.mdt_indexes[key] , doc.metadata_doc_type_rule_id, doc.metadata_created_date ],
                    {rev: doc._rev, metadata_doc_type_rule_id: doc.metadata_doc_type_rule_id} // metadata_doc_type_rule_id is required for search results sorting
                );// emit
            };// for
        }; // if deleted
    }; //if doctype
} //function
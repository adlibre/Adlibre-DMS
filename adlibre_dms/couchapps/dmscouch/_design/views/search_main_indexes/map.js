function (doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted != "deleted") {
            emit(
                doc._id,
                    {
                        metadata_doc_type_rule_id: doc.metadata_doc_type_rule_id,
                        metadata_created_date: doc.metadata_created_date,
                        mdt_indexes: doc.mdt_indexes,
                        metadata_description: doc.metadata_description,
                    }
            );// emit
        } // deleted
    } // if doctype
} // function
function(doc) {
     if (doc.doc_type == "CouchDocument") {
          emit([doc.metadata_doc_type_rule_id, doc.metadata_created_date], {rev: doc._rev, metadata_doc_type_rule_id: doc.metadata_doc_type_rule_id});
     } // if
}// function
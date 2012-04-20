function(doc) {
     if (doc.doc_type == "CouchDocument") {
          emit([doc.metadata_created_date, doc.metadata_doc_type_rule_id], {rev: doc._rev, metadata_doc_type_rule_id: doc.metadata_doc_type_rule_id});
     } // if
}// function
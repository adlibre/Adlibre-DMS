function(doc) {
     if (doc.doc_type == "CouchDocument") {
          emit([doc.metadata_created_date, doc.metadata_doc_type_rule_id], {rev: doc._rev});
     } // if
}// function
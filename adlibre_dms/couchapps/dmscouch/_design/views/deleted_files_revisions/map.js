function(doc) {
    if (doc.doc_type == "CouchDocument") {
        if (doc.deleted == "deleted") {
        } else {
            for(var revision in doc.revisions) {
                //emit([revision, doc.revisions[revision] ], {rev: doc._rev});
                if (doc.revisions[revision].deleted == true) {
                    emit(revision, {rev: doc._rev, deleted_revision: revision});
                }
            };// for
        }; // if deleted
    }; //if doctype
} //function
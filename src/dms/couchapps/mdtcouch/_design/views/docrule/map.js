function(doc) {
     if (doc.doc_type == "MetaDataTemplate") {
         for (var key in doc.docrule_id){
            emit(doc.docrule_id[key], {rev: doc._rev});
         }
     }
}

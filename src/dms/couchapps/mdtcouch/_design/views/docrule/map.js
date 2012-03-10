function(doc) {
     if (doc.doc_type == "MetaDataTemplate") {
          emit(doc.docrule_id, doc);
     }
}

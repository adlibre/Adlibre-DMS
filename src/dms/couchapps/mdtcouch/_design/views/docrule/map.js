function(doc) {
     if (doc.doc_type == "MetaDataTemplate")
          emit(doc.docrule_id, {rev:doc._rev});
}

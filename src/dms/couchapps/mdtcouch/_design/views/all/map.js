function(doc) {
     if (doc.doc_type == "MetaDataTemplate")
          emit(doc._id, doc);
}
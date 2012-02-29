function(doc) {
    for(var key in doc.mdt_indexes) {
        emit(
            [ key, doc.mdt_indexes[key] ],
            {rev: doc._rev}
        );
    }
}
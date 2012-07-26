function (key, values, rereduce) {
    var o = {}, i, l = values.length, r = [];

    for (i = 0; i < l; i += 1) {
        o[values[i]] = values[i];
    }

    for (i in o) {
        r.push(o[i]);
    }

    return r;
}
function UIRenderer(){
    var self = this;
    this.rule_list_id = "ui_rule_list";
    this.document_list_id = "ui_document_list";

    this.render_object_list = function(list_id, objects, construct_item_callback){
        var container = $("#" + list_id);
        var item = container.children().first().detach();
        for (var i = 0; i < objects.length; i++){
            var object_node = construct_item_callback(objects[i], item.clone());
            container.append(object_node);
        }
    }

    this.render_rules = function(rules){
        self.render_object_list(self.rule_list_id, rules, function(rule, rule_item){
            var lnk = $('<a>');
            lnk.text(rule.doccode);
            lnk.attr('href', rule.ui_url);
            rule_item.append(lnk);
            return rule_item;
        });
    }
    
    this.render_documents = function(documents){
        self.render_object_list(self.document_list_id, documents, function(document, document_item){
            var lnk = $('<a>');
            lnk.text(document.name);
            lnk.attr('href', "#");
            document_item.append(lnk);
            return document_item;
        });
    }
}
function UIRenderer(){
    var self = this;
    this.rule_list_id = "ui_rule_list";
    this.document_list_id = "ui_document_list";
    this.document_container_id = 'ui_document';
    this.breadcrumb_list_id = "ui_breadcrumbs";

    this.update_breadcrumbs = function(crumb_item){
        var container = $("#" + self.breadcrumb_list_id);
        var li = $("<li>");
        if (crumb_item.url){
            var a = $('<a>');
            a.attr('href', crumb_item.url);
            a.text(crumb_item.text);
            li.append(a);
        }else{
            li.text(crumb_item.text);
        }
        container.append(li);
    }


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
        var rule_name = documents[0].rule;
        self.render_object_list(self.document_list_id, documents, function(document, document_item){
            var lnk = $('<a>');
            lnk.text(document.name);
            lnk.attr('href', document.ui_url);
            document_item.append(lnk);
            return document_item;
        });
        self.render_documents_info({'rule_name': rule_name});
    }
    this.render_documents_info = function(documents_info){
        self.update_breadcrumbs({'url': '.', 'text': documents_info['rule_name']});
    }
    
    this.render_document = function(document_url){
       var iframe = $('<iframe>');
       iframe.attr('src', document_url);
       iframe.css('border', '2px solid #333');
       $('#' + self.document_container_id).empty().append(iframe);
    }
    
    this.render_document_info = function(document_info){
        self.update_breadcrumbs({'url': document_info['document_list_url'], 'text': document_info.doccode.title});
        self.update_breadcrumbs({'text': document_info['document_name']});
    }
}
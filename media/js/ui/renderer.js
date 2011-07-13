function UIRenderer(manager){
    var self = this;
    this.manager = manager;
    this.options = manager.options;

    this.info_rendered = false;

    this.init = function(){
        $('#' + self.options.document_list_id).bind('ui_documents_loaded', self.after_documents_load)
    }
    
    this.update_breadcrumbs = function(crumb_item){
        var container = $("#" + self.options.breadcrumb_list_id);
        var li = $("<li>");
        if (crumb_item.url){
            var a = $('<a>');
            a.attr('href', crumb_item.url);
            a.text(crumb_item.text);
            li.text(" > ");
            li.append(a);
        }else{
            li.text(" > " + crumb_item.text);
        }
        container.append(li);
    }


    this.render_object_list = function(list_id, objects, construct_item_callback){
        var container = $("#" + list_id);
        var item = $("<li>");
        for (var i = 0; i < objects.length; i++){
            var object_node = construct_item_callback(objects[i], item.clone());
            container.append(object_node);
        }
    }

    this.render_rules = function(rules){
        self.render_object_list(self.options.rule_list_id, rules, function(rule, rule_item){
            var lnk = $('<a>');
            lnk.text(rule.doccode);
            lnk.attr('href', rule.ui_url);
            rule_item.append(lnk);
            return rule_item;
        });
    }
    
    this.render_documents = function(documents){
        if(! documents.length){ return false; }
        var rule_name = documents[0].rule;
        self.render_object_list(self.options.document_list_id, documents, function(document, document_item){
            var lnk = $('<a>');
            lnk.text(document.name);
            lnk.attr('href', document.ui_url);
            document_item.append(lnk);
            return document_item;
        });
        self.render_documents_info({'rule_name': rule_name});
        $('#' + self.options.document_list_id).trigger('ui_documents_loaded');
    }

    this.render_documents_info = function(documents_info){
        if (! self.info_rendered){
            self.update_breadcrumbs({'url': '.', 'text': documents_info['rule_name']});
            self.info_rendered = true;
        }
    }

    this.after_documents_load = function(event){
        $(self.options.document_list_id).endlessScroll({
                bottomPixels: 450,
                fireDelay: 100,
                callback: function(p){
                    $("#" + self.options.document_list_id).trigger('ui_more_documents_needed');
                }
        });
    }

    this.render_document = function(document_url){
       var iframe = $('<iframe>');
       iframe.attr('src', document_url);
       iframe.css('border', '2px solid #333');
       $('#' + self.options.document_container_id).empty().append(iframe);
    }

    this.render_document_info = function(document_info){
        self.update_breadcrumbs({'url': document_info['document_list_url'], 'text': document_info.doccode.title});
        self.update_breadcrumbs({'text': document_info['document_name']});
    }
    
    this.add_page = function(page){
        var container = $("#" + self.options.pager_list_id);
        var li = $("<li>");
        var a = $('<a>');
        var url = 'javascript:void(0);';
        a.attr('href', url);
        a.bind('click', function(event){self.manager.move_to_page(page);})
        a.text(page);
        li.append(a);
        container.append(li);
    }

    this.init();
}
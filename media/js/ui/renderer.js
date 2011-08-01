function UIRenderer(manager){
    var self = this;
    this.manager = manager;
    this.options = manager.options;

    this.info_rendered = false;

    this.update_breadcrumbs = function(crumb_item, do_replace){
        var container = $("#" + self.options.breadcrumb_list_id);
        if (do_replace){
            container.children().last().remove();
        }
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

    this.render_control_panel = function(){
        for (var key in self.manager.DOCUMENT_ORDERS){
            var li = $('<li>');
            var a = $('<a>').attr('href', "javascript:void(0);");
            a.bind('click', function(val){
                    return function() { 
                        self.manager.reset_document_list();
                        self.manager.set_state_variable('Order', val);
                        $("#" + self.options.document_list_id).trigger("ui_more_documents_needed");
                    };
            }(key)
            );
            a.text(self.manager.DOCUMENT_ORDERS[key].title);
            li.append(a);
            $("#ui_order_tab").append(li);
        }
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

    this.get_document_list_details = function(){
        var details = ["Ordered by (" + 
                        self.manager.DOCUMENT_ORDERS[self.manager.get_state_variable('Order', 'Date')].title + ")"]
        var filter = self.manager.get_state_variable('Tag', null);
        if (filter){
            details.push('Filtered by (' + '"' + filter + '"' + ')');
        }
        return details.join(" + ");
    }

    this.render_doccode_tags = function(tags){
        $('#ui_tag_list').empty();
        for (var i = 0; i < tags.length; i++){
            var tag = tags[i];
            var li = $('<li>');
            var a = $('<a>');
            a.attr('href', 'javascript:void(0)');
            a.text(tag);
            li.append(a);
            $('#ui_tag_list').append(li);
        }
    }

    this.render_documents_info = function(documents_info){
        if (! self.info_rendered){
            self.update_breadcrumbs({'url': '.', 'text': documents_info['rule_name']});
            self.info_rendered = true;
            self.update_breadcrumbs({'text': self.get_document_list_details()}, false);
        } else{
            self.update_breadcrumbs({'text': self.get_document_list_details()}, true);
        }
    }

    this.render_document = function(document_url){
       var iframe = $('<iframe>');
       iframe.attr('src', document_url);
       iframe.css('border', '2px solid #333'); //FIXME: implement proper css design
       $('#' + self.options.document_container_id).empty().append(iframe);
    }

    this.construct_tag_list_item = function(tag){
        var li = $('<li>');
        li.append($('<span>').text(tag));
        var a = $('<a>');
        a.addClass('ui_delete_tag_link');
        a.attr('href', 'javascript:void(0)');
        a.text('X');
        li.append(a);
        return li;
    }

    this.render_document_info = function(document_info){
        if (! self.info_rendered){
            self.update_breadcrumbs({'url': document_info['document_list_url'], 'text': document_info.doccode.title});
            self.update_breadcrumbs({'text': document_info['document_name']});
            self.info_rendered = true;
        }
        self.render_document_tags(document_info.tags);
        self.render_document_metadata(document_info.current_metadata);
        self.render_document_revisions(document_info.metadata);
        $('#' + self.options.document_container_id).trigger('ui_document_info_loaded');
    }

    this.render_document_tags = function(tags){
        $('#ui_tag_list').empty();
        for (var i = 0; i < tags.length; i++){
            var tag = tags[i];
            $('#ui_tag_list').append(self.construct_tag_list_item(tag));
        }
    }
    this.render_document_metadata = function(metadata){
        $('#ui_metadata_list').empty();
        var keys = {'name': 'Name', 
                    'mimetype': 'Mimetype',
                    'created_date': 'Creation Date',
                    'compression_type': 'Compression Type',
                    'revision': 'Revision'
                    }
        for (var key in keys){
            var li = $('<li>');
            li.text(keys[key] + ": " + metadata[key]);
            $('#ui_metadata_list').append(li);
        }
    }
    this.render_document_revisions = function(metadatas){
        $('#ui_revision_list').empty();
        for (var revision in metadatas){
//        self.render_object_list('ui_revision_list', metadatas, function(metadata, revision_item){
            var revision_item = $('<li>');
            var metadata = metadatas[revision];
            var filename = metadata['name']
            self.manager.store_revision_info(revision, filename);
            var lnk = $('<a>');
            lnk.addClass('ui_revision_link');
            lnk.text(revision);
            lnk.attr('href', "javascript:void(0)");
            revision_item.append(lnk);
            var delete_lnk = $('<a>');
            delete_lnk.addClass('ui_delete_revision_link');
            delete_lnk.attr('href', "javascript:void(0)");
            delete_lnk.text("X");
            revision_item.append(delete_lnk);
            $('#ui_revision_list').append(revision_item);
        }
    }
    this.add_page = function(page){
        var container = $("#" + self.options.pager_list_id);
        var last_page = container.children().last().children().first().text();
        if (!last_page | parseInt(last_page) < page){
            var li = $("<li>");
            var a = $('<a>');
            var url = 'javascript:void(0);';
            a.attr('href', url);
            a.bind('click', function(event){self.manager.move_to_page(page);})
            a.text(page);
            li.append(a);
            container.append(li);
        }
    }
}
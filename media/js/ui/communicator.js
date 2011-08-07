function UICommunicator(manager, renderer){
    var self = this;
    this.renderer = renderer;
    this.manager = manager;
    this.options = manager.options;

    this.loading_documents = false;

    this.document_list_init = function(){
        self.manager.reset_document_list();

        $('#' + self.options.document_list_id).bind('ui_documents_loaded', self.after_documents_load)

        var height = $(window).height() - 200;//FIXME: some more intelligent way to tell container height
        height = (height < 150) ? 150 : height;
        $('#' + self.options.document_list_id).height(height);
        $('#' + self.options.document_list_id).bind('ui_more_documents_needed', self.get_more_documents);
        $('#' + self.options.document_list_id).scroll(function(){
            var page = self.manager.calculate_current_page();
            if (page != parseInt(self.manager.get_state_variable('Page', 1))){
                //alert('new_page '+ page + ', current_page '+ parseInt(self.manager.get_state_variable('Page', 1)));
                self.manager.set_state_variable('Page', page);
            }
        });
        
        self.renderer.render_control_panel();
        
        $('#ui_search_field').val(self.manager.get_state_variable('Search', ''));
        $('#ui_search_form').submit(function(){
            var q = $('#ui_search_field').attr('value') || null;
            if (q){
                self.manager.set_state_variable('Search', q);
            }else{
                self.manager.remove_state_variable('Search');
            }
            self.manager.reset_document_list();
            $("#" + self.options.document_list_id).trigger('ui_more_documents_needed');
            return false;
        });
        
        $('#id_date').val(self.manager.get_state_variable('Date', ''));
        $('#ui_calendar_form').submit(function(event){
            var date = $('#id_date').datepick('getDate')[0];
            var fdate = $.datepick.formatDate('yyyy-mm-dd', date);
            self.filter_by_date(fdate);
            return false;
        });
        $('#ui_clear_filter').click(function(){
            self.manager.remove_state_variable('Tag');
            self.manager.remove_state_variable('Date');
            self.manager.reset_document_list();
            $("#" + self.options.document_list_id).trigger("ui_more_documents_needed");
        });
    }
    this.doccode_tags_init = function(){
        $('#ui_tag_list li a').click(function(event){
            self.filter_by_tag($(event.target).text());
        });
    }
    this.document_init = function(){
        $("#ui_add_tags_form").submit(function(){
            var tag_string = $('#ui_add_tags_field').val();
            if (!tag_string){return false;}
            $.ajax({
                'type': 'PUT',
                'url': self.get_url('document_url'),
                'contentType': 'application/x-www-form-urlencoded',
                'data': {"tag_string": tag_string},
                'success': function(jqXHR, textStatus){
                    self.renderer.render_document_tags($.parseJSON(jqXHR).tags);
                    $('#' + self.options.document_container_id).trigger('ui_document_info_loaded');
                    $('#ui_add_tags_field').val('');
                }
            });
            return false;
        });
        $('#' + self.options.document_container_id).bind('ui_document_info_loaded', self.document_info_init);
        $("#ui_delete_document_form").submit(function(){
            if(confirm("All revisions of this document will be deleted. Are you sure you want to continue?")){
                $.ajax({
                'type': 'DELETE',
                'url': self.get_url('document_url'),
                'contentType': 'application/x-www-form-urlencoded',
                'success': function(jqXHR, textStatus){
                        window.location.href = self.manager.back_url;
                    }
                });
            }
        });
        $("#ui_rename_document_form").submit(function(){
            var new_name = $('#ui_new_name_field').val();
            if (!new_name){return false;}
            var params = $.param.querystring(document.location.href, {"new_name": new_name});
            $.ajax({
                'type': 'PUT',
                'url': self.get_url('document_url', params),
                'contentType': 'application/x-www-form-urlencoded',
                'success': function(jqXHR, textStatus){
                    window.location.href = self.manager.back_url;
                }
            });
        });
    }

    this.document_info_init = function(){
        $('a.ui_delete_tag_link').click(function(event){
                var tag_string = $(event.target).prev().text();
                $.ajax({
                'type': 'PUT',
                'url': self.get_url('document_url'),
                'contentType': 'application/x-www-form-urlencoded',
                'data': {"remove_tag_string": tag_string},
                'success': function(jqXHR, textStatus){
                    self.renderer.render_document_tags($.parseJSON(jqXHR).tags);
                    $('#' + self.options.document_container_id).trigger('ui_document_info_loaded');
                }
                });
        });
        $('a.ui_revision_link').click(function(event){
            var revision = $(event.target).text();
            var params = {'r': revision};
            self.get_document_info(params);
            self.get_document(params);
        });
        $("a.ui_delete_revision_link").click(function(event){
            var revision = $(event.target).prev().text();
            if(confirm("Revision " + revision + " of this document will be deleted. Are you sure you want to continue?")){
                var params = {"r": revision, 'full_filename': self.manager.metadata[revision]};
                $.ajax({
                'type': 'DELETE',
                'url': self.get_url('document_url', params),
                'contentType': 'application/x-www-form-urlencoded',
                'success': function(jqXHR, textStatus){
                    if ($('#ui_revision_list').children().length <= 1){
                        window.location.href = self.manager.back_url;
                    }else{
                        self.get_document_info();
                        self.get_document(); // In case we've deleted current revision
                    }
                }
                });
            }
        });
    }
    
    this.get_url = function(name, params){
        var url = UI_URLS[name];
        if (params){
            url = $.param.querystring(url, params);
        }
        return url
    }

    this.get_rules = function(){
        $.getJSON(self.get_url('rules_url'), self.renderer.render_rules);
    }
    
    this.get_documents = function(){
        //$.getJSON(self.get_url('documents_url'), self.renderer.render_documents);
        $("#" + self.options.document_list_id).trigger('ui_more_documents_needed');
        self.get_doccode_tags();
    }
    
    this.get_document_list_params = function(){
        var per_page = self.manager.get_objects_per_page();
        var current_page = parseInt(self.manager.get_state_variable('Page', 1));
        if (!current_page){
            current_page = 1;
            self.manager.set_state_variable(current_page);
        }
        var tag = self.manager.get_state_variable('Tag', null);
        var date = self.manager.get_state_variable('Date', null);
        var more_documents_start = $("#" + self.options.document_list_id).children().length;
        var more_documents_finish = more_documents_start + per_page * current_page;
        var q = self.manager.get_state_variable('Search', null);//self.manager.get_searchword();
        var params = {'start': more_documents_start,
                'finish': more_documents_finish,
                'order': self.manager.DOCUMENT_ORDERS[self.manager.get_state_variable('Order', 'Date')].param_value,
                };
        if (tag){ params['tag'] = tag;}
        if (q){ params['q'] = q;}
        if (date){ params['created_date'] = date; }
        return params;
    }

    this.get_more_documents = function(event){
        event.stopPropagation();
        if (self.loading_documents){ return false; }
        if (self.manager.no_more_documents){ return false; }
        var per_page = self.manager.get_objects_per_page()
        var params = self.get_document_list_params();
        if (params.finish > self.manager.already_loaded_documents){
            //self.manager.already_loaded_documents = params.finish;
            self.loading_documents = true;
            $.getJSON(self.get_url('documents_url'),
                params,
                function(documents){
                    self.renderer.render_documents(documents);
                    self.manager.already_loaded_documents = $("#" + self.options.document_list_id).children().length;
                    if (documents.length < (params.finish - params.start)){
                        self.manager.no_more_documents = true;
                    }
                    current_page = Math.ceil(self.manager.already_loaded_documents / per_page);
                    for(var i = 1; i <= current_page; i++){
                        self.renderer.add_page(i);
                    }
                    self.manager.move_to_page(current_page);
                    self.loading_documents = false;
                });
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

    this.get_document_info = function(params){
        if (!params){ params = {}; }
        params = $.param.querystring(document.location.href);
        $.getJSON(self.get_url('document_info_url', params), function(document_info){
            self.renderer.render_document_info(document_info);
            self.manager.document_metadata = document_info['metadata']
            });
    }
    this.get_document = function(params){
        if (!params){ params = {}; }
        params = $.param.querystring(document.location.href);
        if (params.indexOf('parent_directory') != -1){
            //this is a no-doccode file
            self.renderer.render_document_link(self.get_url('document_url', params));
        }else{
            self.renderer.render_document(self.get_url('document_url', params)); //No ajax, using iframe
        }
    }
    this.get_doccode_tags = function(){
        $.getJSON(self.get_url('tags_url'), function(tags){
            self.renderer.render_doccode_tags(tags);
            self.doccode_tags_init();
            });
    }
    this.filter_by_tag = function(tag){
        self.manager.set_state_variable('Tag', tag);
        self.manager.reset_document_list();
        $("#" + self.options.document_list_id).trigger("ui_more_documents_needed");
    }
    this.filter_by_date = function(date){
        self.manager.set_state_variable('Date', date);
        self.manager.reset_document_list();
        $("#" + self.options.document_list_id).trigger("ui_more_documents_needed");
    }
}

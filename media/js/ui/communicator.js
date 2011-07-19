function UICommunicator(manager, renderer){
    var self = this;
    this.renderer = renderer;
    this.manager = manager;
    this.options = manager.options;

    this.document_list_init = function(){
        self.manager.reset_document_list();
        var height = $(window).height() - 200;//TODO: some more intelligent way to tell container height
        height = (height < 150) ? 150 : height;
        $('#' + self.options.document_list_id).height(height);
        $('#' + self.options.document_list_id).bind('ui_more_documents_needed', self.get_more_documents);
        self.renderer.render_control_panel();
        $('#' + self.options.document_list_id).scroll(function(){
            var page = self.manager.calculate_current_page();
            if (page != parseInt(self.manager.get_state_variable('Page', 1))){
                //alert('new_page '+ page + ', current_page '+ parseInt(self.manager.get_state_variable('Page', 1)));
                self.manager.set_state_variable('Page', page);
            }
        });
        $('#ui_trigger_search').click(function(){
            var q = $('#ui_search_field').attr('value') || null;
            if (q){
                window.location.href = $.param.querystring(window.location.href, {'q':q});
            }
        });
    }

    this.get_url = function(name, params){
        var url = UI_URLS[name];
        if (params){
            for(var i = 0; i < params.length; i++){
                url = (url.split("{{" + i + "}}")).join(params[i])
            }
        }
        return url
    }

    this.get_rules = function(){
        $.getJSON(self.get_url('rules_url'), self.renderer.render_rules);
    }
    
    this.get_documents = function(){
        //$.getJSON(self.get_url('documents_url'), self.renderer.render_documents);
        $("#" + self.options.document_list_id).trigger('ui_more_documents_needed');
    }
    
    this.get_document_list_params = function(){
        var per_page = self.manager.get_objects_per_page();
        var current_page = self.manager.get_state_variable('Page', 1);
        var more_documents_start = $("#" + self.options.document_list_id).children().length;
        var more_documents_finish = more_documents_start + per_page * current_page;
        var q = self.manager.get_searchword();
        var params = {'start': more_documents_start,
                'finish': more_documents_finish,
                'order': self.manager.DOCUMENT_ORDERS[self.manager.get_state_variable('Order', 'Date')].param_value,
                'q': q
                };
        return params;
    }

    this.get_more_documents = function(event){
        if (self.manager.no_more_documents){ return false; }
        var per_page = self.manager.get_objects_per_page()
        var params = self.get_document_list_params();
        if (params.finish > self.manager.already_loaded_documents){
            //self.manager.already_loaded_documents = params.finish;
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
                });
        }
    }

    this.get_document_info = function(){
        $.getJSON(self.get_url('document_info_url'), self.renderer.render_document_info);
    }
    
    this.get_document = function(){
        self.renderer.render_document(self.get_url('document_url')); //No ajax, using iframe
    }
}

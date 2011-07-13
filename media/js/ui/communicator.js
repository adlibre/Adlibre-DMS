function UICommunicator(manager, renderer){
    var self = this;
    this.renderer = renderer;
    this.manager = manager;
    this.options = manager.options;
    this.already_loaded_documents = 0;
    this.no_more_documents = false;

    this.document_list_init = function(){
        var height = $(window).height() - 200;//TODO: some more intelligent way to tell container height
        height = (height < 150) ? 150 : height;
        $('#' + self.options.document_list_id).height(height);
        $('#' + self.options.document_list_id).bind('ui_more_documents_needed', self.get_more_documents);
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
    
    this.get_more_documents = function(event){
        if (self.no_more_documents){ return false; }
        var more_documents_start = $("#" + self.options.document_list_id).children().length;
        var per_page = self.manager.get_objects_per_page()
        var more_documents_finish = more_documents_start + per_page;
        if (more_documents_finish > self.already_loaded_documents){
            self.already_loaded_documents = more_documents_finish;
            $.getJSON(self.get_url('documents_url'), 
                {'start': more_documents_start,
                'finish': more_documents_finish
                }, function(documents){
                    self.renderer.render_documents(documents);
                    if (documents.length < (more_documents_finish - more_documents_start)){
                        self.no_more_documents = true;
                    }
                    current_page = self.already_loaded_documents / per_page;
                    self.renderer.add_page(current_page);
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

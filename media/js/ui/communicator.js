function UICommunicator(options, renderer){
    var self = this;
    this.renderer = renderer;
    this.options = options;
    this.already_loaded_documents = 0;
    this.objects_per_page = null;
    this.no_more_documents = false;

    this.document_list_init = function(){
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
    
    this.get_objects_per_page = function(){
        if (!self.objects_per_page){
            //TODO: think of a way to calculate document dimensions dynamically
            if (!self.document_width){
                self.document_width = 150;//$("#" + self.options.document_list_id).children().first().outerWidth(true);
            }
            if (!self.document_height){
                self.document_height = 130;//$("#" + self.options.document_list_id).children().first().outerHeight(true);
            }
            var docs_in_row = parseInt($("#" + self.options.document_list_id).innerWidth() / self.document_width);
            var rows = parseInt(($(window).height() - $("#" + self.options.document_list_id).offset().top) / self.document_height);
            var rows = rows ? rows : 1;
            self.objects_per_page = rows * docs_in_row;
            alert(self.objects_per_page);
        }
        return self.objects_per_page;
    }

    this.get_more_documents = function(event){
        if (self.no_more_documents){ return false; }
        var more_documents_start = $("#" + self.options.document_list_id).children().length;
        var more_documents_finish = more_documents_start + self.get_objects_per_page();
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
                });
        }
    }

    this.get_document_info = function(){
        $.getJSON(self.get_url('document_info_url'), self.renderer.render_documents_info);
    }
    
    this.get_document = function(){
        self.renderer.render_document(self.get_url('document_url')); //No ajax, using iframe
    }
}

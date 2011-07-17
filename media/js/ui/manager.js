function UIManager(){
    var self = this;
    this.options = {};
    this.options.rule_list_id = "ui_rule_list";
    this.options.document_list_id = "ui_document_list";
    this.options.document_container_id = 'ui_document';
    this.options.breadcrumb_list_id = "ui_breadcrumbs";
    this.options.pager_list_id = "ui_pager";

    this.reset_document_list = function(){
        this.already_loaded_documents = 0;
        this.no_more_documents = false;
        $("#" + self.options.document_list_id).empty();
        $("#" + self.options.pager_list_id).empty();
    }

    this.DOCUMENT_ORDERS = {
                                "Date": {'title':"Date", 'param_value': 'created_date'},
                                "Name": {'title':"Name", 'param_value': 'name'}
                            };
    this.get_state_variable = function(var_name, default_value){
        var val = $.bbq.getState(var_name);
        if (!val | typeof(val) == 'undefined'){ val = default_value; }
        return val;
    }
    this.set_state_variable = function(var_name, value){
        var options = new Object();
        options[var_name] = value;
        jQuery.bbq.pushState(options);
    }

    this.calculate_current_page = function(){
        var current_scroll = $("#" + self.options.document_list_id).scrollTop();
        var page_height = self.get_document_height() * self.get_rows_per_page() + 15;
        return parseInt(current_scroll / page_height) + 1;
    }

    this.move_to_page = function(page){
        var page_height = self.get_document_height() * self.get_rows_per_page();
        var margin = 15;
        var scroll_top = (page-1) * page_height + margin;
        $("#" + self.options.document_list_id).scrollTop(scroll_top);
        self.set_state_variable('Page', page);
    }

    this.get_document_width = function(){
        //TODO: think of a way to calculate document dimensions dynamically
        if (!self.document_width){
            self.document_width = 150;//$("#" + self.options.document_list_id).children().first().outerWidth(true);
        }
        return self.document_width;
    }

    this.get_document_height = function(){
        //TODO: think of a way to calculate document dimensions dynamically
        if (!self.document_height){
                self.document_height = 130;//$("#" + self.options.document_list_id).children().first().outerHeight(true);
        }
        return self.document_height;
    }
    
    this.get_docs_in_row = function(){
        return parseInt($("#" + self.options.document_list_id).innerWidth() / self.get_document_width());
    }
    
    this.get_rows_per_page = function(){
        var rows = parseInt(($(window).height() - $("#" + self.options.document_list_id).offset().top) / self.get_document_height());
        var rows = rows ? rows : 1;
        return rows;
    }
    
    this.get_objects_per_page = function(){
        if (!self.objects_per_page){
            self.objects_per_page = self.get_rows_per_page() * self.get_docs_in_row();
        }
        return self.objects_per_page;
    }

};
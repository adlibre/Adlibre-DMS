function UIManager(){
    var self = this;
    this.options = {};
    this.options.rule_list_id = "ui_rule_list";
    this.options.document_list_id = "ui_document_list";
    this.options.document_container_id = 'ui_document';
    this.options.breadcrumb_list_id = "ui_breadcrumbs";
    this.options.pager_list_id = "ui_pager";

    this.move_to_page = function(page){
        var page_height = self.get_document_height() * self.get_rows_per_page();
        var margin = 15;
        var scroll_top = (page-1) * page_height + margin;
        $("#" + self.options.document_list_id).scrollTop(scroll_top);
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
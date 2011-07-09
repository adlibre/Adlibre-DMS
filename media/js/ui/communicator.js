function UICommunicator(){
    var self = this;

    this.get_url = function(name, params){
        var url = UI_URLS[name];
        if (params){
            for(var i = 0; i < params.length; i++){
                url = (url.split("{{" + i + "}}")).join(params[i])
            }
        }
        return url
    }

    this.get_rules = function(success_callback){
        $.getJSON(self.get_url('rules_url'), success_callback);
    }
    
    this.get_documents = function(success_callback){
        $.getJSON(self.get_url('documents_url'), success_callback);
    }
    
    this.get_document_info = function(success_callback){
        $.getJSON(self.get_url('document_info_url'), success_callback);
    }
    
    this.get_document = function(success_callback, success_callback_info){
        success_callback(self.get_url('document_url')); //No ajax, using iframe
    }
}

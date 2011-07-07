function UICommunicator(options){
    var self = this;
    this.options = options;

    this.get_url = function(name, params){
        var url = this.options[name];
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
}

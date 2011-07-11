$(document).ready(function(){
    var options = {};
    options.rule_list_id = "ui_rule_list";
    options.document_list_id = "ui_document_list";
    options.document_container_id = 'ui_document';
    options.breadcrumb_list_id = "ui_breadcrumbs";

    renderer = new UIRenderer(options);
    window.ui_communicator = new UICommunicator(options, renderer);

});
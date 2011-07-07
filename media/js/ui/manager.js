function UIManager(communicator, renderer){
    this.communicator = communicator;
    this.renderer = renderer;
    this.init = function(){
        1;
    }
}

$(document).ready(function(){
    var communicator = new UICommunicator(COMMUNICATOR_OPTIONS);
    var renderer = new UIRenderer();
    window.ui_manager = new UIManager(communicator, renderer);
    }
);
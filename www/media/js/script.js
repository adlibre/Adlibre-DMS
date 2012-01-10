$(document).ready(function() {
	// setup ul.tabs to work as tabs for each div directly under div.panes
	$("ul.tabs").tabs("div.panes > div");
	$("#new-rule").click(function() {
	    $("#new-rule-form").toggle();
	    return false;
	});
});


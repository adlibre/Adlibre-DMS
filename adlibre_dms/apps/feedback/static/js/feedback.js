/*
Module: Feedback form for DMS MUI scripts

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
*/
$(document).ready(function(){
    var feedback_csrf_val = $('input[name=csrfmiddlewaretoken]').attr('value');
    // Caching the feedback object:
    var feedback = $('#feedback');
    var submitURL = feedback.attr("url");

    $('#feedback h1').click(function(){
        var anim	= {
            mb : 0,			// Margin Bottom
            pt : 12			// Padding Top
        };

        var el = $(this).find('.fpointer');

        if(el.hasClass('fb-down')){
            anim = {
                mb : -240,
                pt : 10
            };
        }

        // The first animation moves the form up or down, and the second one
        // moves the "Feedback heading" so it fits in the minimized version

        feedback.stop().animate({marginBottom: anim.mb});

        feedback.find('.section').stop().animate({paddingTop:anim.pt},function(){
            el.toggleClass('fb-down fb-up');
        });
    });

    function create_response(text){
        var span = $('<span>')
                .hide()
                .addClass('response')
                .html(text)
                .appendTo(feedback.find('.section'))
                .show();
    }

    $('#feedback a.fb-submit').live('click',function(){
        var button = $(this);
        var textarea = feedback.find('textarea');

        // We use the working class not only for styling the submit button,
        // but also as kind of a "lock" to prevent multiple submissions.

        if(button.hasClass('btn-disabled') || textarea.val().length < 5){
            return false;
        }

        // Locking the form and changing the button style:
        button.removeClass('btn-primary');
        button.addClass('btn-disabled');
        button.text('Working...');


        $.ajax({
            url		: submitURL,
            type	: 'post',
            data	: {
                feedback_body :         textarea.val(),
                csrfmiddlewaretoken :   feedback_csrf_val
            },
            complete	: function(xhr){

                var text = xhr.responseText;

                // This will help users troubleshoot their form:
                if(xhr.status == 404){
                    text = 'Your path to feedback form is incorrect.';
                }

                button.fadeOut();

                textarea.fadeOut(create_response(text)).val('');
            }
        });

        return false;
    });
});
/*
 * Script to handle file Upload form.
 * Requires jQuery 1.5.3 or higher to function.
 */

// emulating browse call for hidden file input
$('#upload_file_fake_browse').click(function(){
     $('#upload_file_fileinput').click();
});
//emulating Mac behavior
$('#upload_file_fake_filename').click(function(){
     $('#upload_file_fileinput').click();
});

// changing function for fileinput value
$('#upload_file_fileinput').change(function(){
    $('#upload_file_fake_filename').val($(this).val().replace(/^C:\\fakepath\\/i, ''));
});//DjangoCon 2008_ 


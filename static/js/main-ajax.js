$(document).ready(function() {


    $('#likes').click(function(){

        var catid = $(this).attr("data-catid");
        $.get('/main/like_category/', {cat_id: catid}, function(data){
            $('#like_count').html(data);
            $('#likes').hide();
        });
    });



    $('#suggestion').keyup(function(){
        var query;
        query = $(this).val();
        $.get('/main/suggest_category/', {suggestion: query}, function(data){
            $('#cats').html(data);
        });
    });



    $('#page_suggestion').keyup(function(){
        var query;
        query = $(this).val();
        $.get('/main/suggest_page/', {suggestion: query}, function(data){
            $('#pages').html(data);
        });
    });




    $('.autoadd').click(function(){



        var catid = $(this).attr("data-catid");
        var title = $(this).attr("data-title");
        var url = $(this).attr("data-url");


        $(this).hide();


        $.get('/main/auto_add_page/', {cat_id: catid, title: title, url: url}, function(data){

            $('#pages').html(data);

        });




    });



    $('#id_username').keyup(function(){
        var id_username;
        id_username = $(this).val();
        $.get('/main/username_taken/', {id_username: id_username}, function(data){
            $('#username_taken').html(data);

        });
    });



    $('#id_email').keyup(function(){
        var id_email;
        id_email = $(this).val();
        $.get('/main/email_taken/', {id_email: id_email}, function(data){
            $('#username_taken').html(data);

        });
    });



});





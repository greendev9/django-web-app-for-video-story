
$(function(){

    $( "#result_list").find("tbody #update_button " ).on( "click", function() {
        var inappid = $(this).attr("inappid");
        var selected_option = $( this ).closest( "tr" ).find("td.field-skigit_status #id_status_ldis");
        var status_id = $(selected_option).val();
        $.get(
            "/inappropriateskigit_status_save/",
            {inappid:inappid, status_id:status_id},
            function(data, status){}
        );
    });
});


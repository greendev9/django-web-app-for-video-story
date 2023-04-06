var myMessages = ['info', 'warning', 'error', 'success']; // define the messages types
var csrftoken;
var load = '/static/skigit/detube/images/ring.svg';
var PROFILE_PLACEHOLDER = '/static/skigit/detube/images/noimage_user.jpg';
var LOGO_PLACEHOLDER = '/static/skigit/detube/images/logo_placeholder1.png';
var OFFLINE_BUTTON_IMG = '/static/skigit/detube/images/offline.png';
var ONLINE_BUTTON_IMG = '/static/skigit/detube/images/online.png';
var MSG_DELETE_IMG = '/static/skigit/detube/images/delete.png';
var MSG_READ_SRC = '/static/skigit/detube/images/read.png';
var MSG_UNREAD_SRC = '/static/skigit/detube/images/unread.png';
var MSG_SENDER_IMG = '/static/skigit/detube/images/Undo-icon.png';
var DELETE_ICON = '/static/skigit/detube/images/deleteIcon.png';
var RIGHT_ICON = '/static/skigit/detube/images/success_icon.png';

var MSG_READ_IMG = '<img width="15" height="15" src="' + MSG_READ_SRC + '" title="Mark Conversion Read">';
var MSG_UNREAD_IMG = '<img width="15" height="15" src="' + MSG_UNREAD_SRC + '" title="Mark Conversion Unread">';
var lodder = '<div class="outer_wrap"><img src="/static/skigit/detube/images/ring.svg"></div>';
var current_url, temp_url;
var count=0

$(document).ready(function () {

    /*get csrf token for pass in post method whiule ajax call */

    current_url = window.location.href;
    temp_url = /messages/;
    if (temp_url.test(current_url))
    {
        perform_chat_action();
    }

    /* Code added by mitesh for default select option in skigit upload form*/

    $("#id_file_on_server").attr("accept", ".wmv,.avi,.flv,.MPEG4,.MPG,.MPE,.WEBM,.MOV,.WMV,.WVX,.WM,.WMX,.3GP,.3GPP,.3GPP2,.3G2,.mp4");
    $('#id_made_by').prepend($('<option>', {
        value: 0,
        text: 'Select maker',
        selected: true,
        disabled: true
    }));
    $('.sk_cat > select').prepend($('<option>', {
        value: 0,
        text: 'Select category',
        selected: true,
        disabled: true
    }));
    $('.sk_subject_cat >select').prepend($('<option>', {
        value: 0,
        text: 'Select subject category',
        selected: true,
        disabled: true
    }));
    /* End of code added by mitesh for default select option in skigit upload form*/

    /* Code added by mitesh for Placeholder*/

    $("#id_bought_at").attr('placeholder', 'Enter item URL');
    $("#id_bought_at").attr('required', 'required');
    $("#id_why_rocks").attr('placeholder', 'Enter text');
    /* End of code added by mitesh for Placeholder*/

    if ($("#id_logo_img").length == 1)
    {
        $("#id_logo_img").attr("onchange", "logo_imgURL(this);");
    }
    if ($("#id_profile_img").length == 1)
    {
        $("#id_profile_img").attr("onchange", "profile_imgURL(this);");
    }

    $('.img-zoom').hover(function () {
        $(this).addClass('transition');
    }, function () {
        $(this).removeClass('transition');
    });
    // Code added by mitesh for skigit like/unlike

    $(".like_unlike").click(function ()
    {
//     var user_id = $(this).attr('data-userid');
//     if (user_id == 1)
//     {
        var skigit_id = $(this).attr('data-pid');
        var csrftoken = getCookie('csrftoken');
	console.log('count:', count)  
	var post_id = $(this).attr('id');
        $.ajax({
            type: "POST",
            url: "/skigit_like/",
            data: {'skigit_id': skigit_id, 'csrfmiddlewaretoken': csrftoken},
            //dataType: "text",
            success: function (response)
            {
                //alert(response.message);
                //alert('You liked this')
		console.log(response.message)
		console.log('count:', count)
                if (response.is_success)
                {
                    if (response.is_liked == 1)
                    {
                        $("#" + post_id).removeClass("like");
                        $("#" + post_id).addClass("liked");
                        $("#likecount" + skigit_id).html(response.like_count);
			$("#" + post_id + "> img").attr("src", "/static/skigit/images/heart_liked(22x22).png");
                    }
                    else
                    {
                        $("#" + post_id).removeClass("liked");
                        $("#" + post_id).addClass("like");
                        $("#likecount" + skigit_id).html(response.like_count);
                    }
                }
                else
                {
                    $("#popup_msg").text(response.message);
                    $("#popScreen").show();
                }
            },
            error: function (rs, e)
            {
                //alert("Please try again to like this skigit");
                $("#popup_msg").text("Error into like the Skigit...! Please try again");
                $("#popScreen").show();
            }
        });
//        }
//        else
//        {
//            //alert("Please login first to like Skigit");
//            $("#popup_msg").text("Please login first to like the Skigit");
//            $("#popScreen").show();
//        }
    });
    $("#popclose").click(function () {

        $("#popScreen").hide();
    });
    // End of code added by mitesh for skigit like/unlike

    $(".showdropdown").click(function () {

        if ($('.head_share_popupbox'))
            $('.head_share_popupbox').css("display", "none"); //sharebox
        if ($(".joinTooltip_content"))
            $(".joinTooltip_content").css("display", "none"); //joinbox
        if ($('.head_share_favpopup'))
            $('.head_share_favpopup').css("display", "none"); //fav sharebox
        if ($('.invitebox'))
            $('.invitebox').css("display", "none"); //friend invite
        if ($('.head_share_origin'))
            $('.head_share_origin').css("display", "none"); //origin sharebox
        if ($('#head_notification_popup'))
            $('#head_notification_popup').css("display", "none"); //notifications
        if ($('#head_frireq_popup'))
            $('#head_frireq_popup').css("display", "none"); //friend request
        if ($('#head_email_popup'))
            $('#head_email_popup').css("display", "none"); //emails
        if ($('.my_skigitt_popupbox'))
            $('.my_skigitt_popupbox').css("display", "none"); //popup statistics

        if ($(this).next().css('display') == 'none')
            $(this).next().slideDown("fast").css("display", "block");
        else
            $(this).next().slideUp("fast");
    });
    $(".dropdown-content").mouseover(function () {

//alert('mrphpguru');
    });
    $(".dropdown-content").mouseleave(function () {
        if ($(".dropdown-content").css('display') == 'none')
        {
//alert('none');
        }
        else
        {
            if ($("#head_share_popuploop11").css('display') == 'none')
            {
                $(".dropdown-content").slideUp("fast");
            }
        }

//$().slideUp("fast");
//alert('mrphpguru latestvideos');
    });
    // code for retrive logo image of business user
    $("#id_made_by").change(function ()
    {
        var bus_user_id = $(this).find(":selected").val();
        if (bus_user_id)
        {
//alert(bus_user_id);
            $.ajax({
                type: "POST",
                url: "/display_business_logo/",
                data: {'bus_user_id': bus_user_id, 'csrfmiddlewaretoken': csrftoken},
                //dataType: "text",
                success: function (response)
                {
                    $("#display_logo").attr("src", response.logo_main);
                    $("#getnewlogodiv").show();
                    //alert(response.message);
                },
                error: function (rs, e)
                {
                    alert("Erro into getiing business logo");
                }
            });
        }
        else
        {
            alert('Invalid user');
        }
    });
    //End of code for retrive logo image of business user


    /*To display flag as inappropriate popup start */

    $(".flag_popup").click(function () {
        $("#singlehead_flag_popuploop").toggle('fast');
    });
    /* code for submit inapp reason form*/

    $('#innapp_reason_form').on('submit', function (event) {
        event.preventDefault();
        //console.log("form submitted!")  // sanity check
        //create_post();

        var formdata = $(this).serialize();
        $.ajax({
            type: "POST",
            url: "/skigit_inapp_reason/",
            data: formdata,
            success: function (response)
            {
                if (response.user_id) // chech whether user login or not
                {
                    if (response.reason_id) // check whether user select at least one reason for inappropriate skigit or not
                    {

                        if (response.is_success)
                        {
                            $("#singlehead_flag_popuploop").hide();
                            $("#popup_msg").text("Thanks for submitting the complaint. Admin will take approriate steps to investigate. We will inform you when complete.");
                            $("#popScreen").show();
                        }
                        else
                        {
                            $("#singlehead_flag_popuploop").hide();
                            $("#popup_msg").text(response.message);
                            $("#popScreen").show();
                        }
                    }
                    else
                    {
                        $("#error_message").show();
                        $("#error_message").html(response.message);
                    }
                }
                else
                {
                    $("#singlehead_flag_popuploop").hide();
                    $("#popup_msg").text(response.message);
                    $("#popScreen").show();
                }
            },
            // handle a non-successful response
            error: function (xhr, errmsg, err)
            {
                alert(errmsg);
//                $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
//                        " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
//                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });
    });
    /* End of code for submit inapp reason form*/

    /*For ajax get data*/

    $(document).on("click", function ()
    {
        $(".emailresponseclass").fadeOut('slow');
    });
    $(".keyword_toemail").on("keyup", function (event)
    {
        document.getElementById("compose_errors").style.display = "none";
        $(this).parent().nextAll().filter('.emailconfirm').hide();
        $(this).focus();
        var offset = $(this).offset();
        var width = $(this).width() - 2;
        $(this).parent().nextAll().filter(".emailresponseclass").css("left", offset.left);
        $(this).parent().nextAll().filter(".emailresponseclass").css("width", width);
        var keyword = $(this).val();
        var keyobj = $(this);
        if (keyword.length)
        {
            if (event.keyCode != 40 && event.keyCode != 38 && event.keyCode != 13)
            {
                $('#msg_user_loading').show();
                $.ajax(
                        {
                            type: "POST",
                            url: "/get_username/",
                            data: {'keyword': keyword, 'csrfmiddlewaretoken': csrftoken},
                            success: function (msg) {
                                if (msg.is_success)
                                {
                                    $("#namefetchlist").html("");
                                    $("#emailresponseclass").fadeIn("slow");
                                    for (var i = 0; i < msg.users.length; i++)
                                    {
                                        $("#namefetchlist").fadeIn("slow").append("<li><a href='javascript:void(0);' ><span class='bold'>" + keyword + "</span>" + msg.users[i]['username'].substring(keyword.length) + "</a></li>");
                                    }
                                    //alert(keyobj.attr('id'));
                                    //keyobj.parent().nextAll().filter(".emailresponseclass").fadeIn("slow").html(msg);
                                }
                                else
                                {
                                    keyobj.parent().nextAll().filter(".emailresponseclass").fadeIn("slow");
                                    keyobj.parent().nextAll().filter(".emailresponseclass").html('<div style="text-align:center;color:#000;">No Matches Found</div>');
                                }
                                $('#msg_user_loading').hide();
                            }
                        });
            }
            else
            {
                switch (event.keyCode)
                {
                    case 40:
                        {
                            found = 0;
                            $("li").each(function () {
                                if ($(this).attr("class") == "selected")
                                    found = 1;
                            });
                            if (found == 1)
                            {
                                var sel = $("li[class='selected']");
                                sel.next().addClass("selected");
                                sel.removeClass("selected");
                            }
                            else
                            {
                                $("li:first").addClass("selected");
                            }
                        }
                        break;
                    case 38:
                        {
                            found = 0;
                            $("li").each(function ()
                            {
                                if ($(this).attr("class") == "selected")
                                    found = 1;
                            });
                            if (found == 1)
                            {
                                var sel = $("li[class='selected']");
                                sel.prev().addClass("selected");
                                sel.removeClass("selected");
                            }
                            else
                            {
                                $("li:last").addClass("selected");
                            }
                        }
                        break;
                    case 13:
                        keyobj.parent().nextAll().filter(".emailresponseclass").fadeOut("slow");
                        keyobj.parent().nextAll().filter(".emailresponseclass").val($("li[class='selected'] a").text());
                        break;
                }
            }
        }
        else
            keyobj.parent().nextAll().filter(".emailresponseclass").fadeOut("slow");
    });

    $(".emailresponseclass").on("mouseover", function ()
    {
        var res = $(this);
        res.find("li a:first-child").on("mouseover", function ()
        {
            $(this).addClass("selected");
        });
        res.find("li a:first-child").on("mouseover", function ()
        {
            $(this).removeClass("selected");
        });
        res.find("li a:first-child").on("click", function ()
        {
            $(".keyword_toemail").val($(this).parent().text());
            res.fadeOut("slow");
        });
    });
    /*End Ajax get data*/

    /* Ajax to get Plugin Details */

    $('.joinpopup').on("click", function ()
    {
        if ($('.head_share_popupbox'))
            $('.head_share_popupbox').css("display", "none"); //sharebox
        if ($(".joinTooltip_content"))
            $(".joinTooltip_content").css("display", "none"); //joinbox
        if ($(".dropdown-content"))
            $(".dropdown-content").css("display", "none"); //useraccout
        if ($('.head_share_favpopup'))
            $('.head_share_favpopup').css("display", "none"); //fav sharebox
        if ($('.invitebox'))
            $('.invitebox').css("display", "none"); //friend invite
        if ($('.head_share_origin'))
            $('.head_share_origin').css("display", "none"); //origin sharebox
        if ($('#head_notification_popup'))
            $('#head_notification_popup').css("display", "none"); //notifications
        if ($('#head_frireq_popup'))
            $('#head_frireq_popup').css("display", "none"); //friend request
        if ($('#head_email_popup'))
            $('#head_email_popup').css("display", "none"); //emails
        if ($('#singlehead_flag_popuploop'))
            $('#singlehead_flag_popuploop').css("display", "none"); //emails

        /* get plugin data ajax*/

        var skigit_id = $(this).attr('data-pid');
        $.ajax({
            type: "POST",
            url: "/skigit_plugin_ajax/",
            data: {'skigit_id': skigit_id, 'csrfmiddlewaretoken': csrftoken},
            success: function (response)
            {
                //alert('You liked this')
                if (response.is_success)
                {
                    if (response.data != "")
                    {
                        $(".plugged_data").html("");
                        $('.plugged_data').append(response.data);
                    }
                    else
                    {
                        $(".plugged_data").html("");
                        var str = '';
                        str += '<div class="join_inner thumb_content">';
                        str += '<div class="join_content">';
                        str += '<center style="color: rgb(3, 129, 195); font-weight: 600; margin:14px 0 0 100px;">No Plugs found.</center>';
                        str += '</div>';
                        str += '</div>';
                        $('.plugged_data').append(str);
                    }
                }
                else
                {
                    $(".plugged_data").html("");
                    var str = '';
                    str += '<div class="join_inner thumb_content">';
                    str += '<div class="join_content">';
                    str += '<span style="color: rgb(3, 129, 195); font-weight: 600; margin:6px 0 0 82px;">No Plugs found.</center>';
                    str += '</div>';
                    str += '</div>';
                    $('.plugged_data').append(str);
                }
            },
            error: function (rs, e)
            {
                $(".plugged_data").html("");
                var str = '';
                str += '<div class="join_inner thumb_content">';
                str += '<div class="join_content">';
                str += '<span style="color: rgb(3, 129, 195); font-weight: 600; margin:6px 0 0 82px;">Error into getting plugs data.</center>';
                str += '</div>';
                str += '</div>';
                $('.plugged_data').append(str);
            }
        });
        /* end of code get plugin data ajax*/

        if ($(this).next().css('display') == 'none')
            $(this).next().slideDown("slow").css("display", "block");
        else
            $(this).next().slideUp("slow");
    });
    $('.Joinclose').on("click", function ()
    {
        var pid = $(this).attr("id");
        var popup_id = pid.replace('skigitt_drop_close', '');
        if ($('#pop_upsingle' + popup_id))
            $('#pop_upsingle' + popup_id).slideUp("slow");
        if ($('#pop_uploop' + popup_id))
            $('#pop_uploop' + popup_id).slideUp("slow");
        if ($('#pop_upfav' + popup_id))
            $('#pop_upfav' + popup_id).slideUp("slow");
        if ($('#pop_uporigin' + popup_id))
            $('#pop_uporigin' + popup_id).slideUp("slow");
    });
    /*End of code to get Plugin Details*/

    //code by kartik for user nevigations open and close menu
    var url = window.location.href;
    $(".wpcf7-form-control-wrap input").val(url);
    $("#bug_popup_cancel").click(function () {
        $('#bug_feature_popup').hide();
    });
    $('#head_email').click(function ()
    {
        $('#bug_feature_popup').css("display", "none"); //bug_feature_popup
        $('#invite_feature_popup').hide();
    });
    $('#head_bug').click(function ()
    {
        $('#head_email_popup').hide(); //bug_feature_popup
        $('#head_notification_popup').css("display", "none"); //bug_feature_popup
        $('#invite_feature_popup').hide(); //bug_feature_popup
    });
    $('#invite_feature').click(function ()
    {

    });
    $('.invitefrnd_button, .close_invitefriend').click(function ()
    {
        $('#bug_feature_popup').css("display", "none");
        $('#head_email_popup').hide(); //bug_feature_popup
        $('#head_notification_popup').css("display", "none"); //bug_feature_popup
        $k('#invite_feature_popup').toggle('fast');
    });
    $('#head_notification').click(function ()
    {
        $('#bug_feature_popup').css("display", "none"); //bug_feature_popup
        $('#invite_feature_popup').hide();
    });
    $('#head_frireq').click(function ()
    {
        $('#bug_feature_popup').css("display", "none"); //bug_feature_popup
        $('#invite_feature_popup').hide();
    });
    var url = window.location.href;
    $(".wpcf7-form-control-wrap input").val(url);
    $("#bug_popup_cancel").click(function ()
    {
        $('#bug_feature_popup').hide();
    });

    $("form#create_message_form").submit(function (e) {
//'csrfmiddlewaretoken': csrftoken
//To Field id =keyword_toemail,name=to_field
//Field subject id=keyword_subject,name=keyword_subject
//Field msg id=mail_cmpmsg,name=mail_cmpmsg
        e.preventDefault()
        $("#msg_sending_loading").show();
        $("#mail_btn").attr('disabled', 'disabled');
        var form_data = $(this).serialize();
        to = $("#keyword_toemail").val();
        sub = $("#keyword_subject").val();
        text = $("#mail_cmpmsg").val();
        is_error = false
        msg = "";
        if (to && !is_empty(to.trim())) {
            if (sub && !is_empty(sub.trim())) {
                if (text && !is_empty(text.trim())) {
                    form_data += '&' + $.param({'csrfmiddlewaretoken': csrftoken});
                    //console.log(form_data);

                    $.ajax({
                        url: "/send_message/", // the endpoint
                        type: "POST", // http method
                        data: form_data, // data sent with the delete request
                        success: function (response) {
                            // hide the post
                            if (response)
                            {
                                if (response.is_success)
                                {
                                    rem_msg();
                                    set_msg('success', response.message);
                                    $("#head_email_popup").hide();
                                    $("#composenewemailbox").hide();
                                    show_msg();
                                }//message send
                                else
                                {
                                    is_error = true;
                                    msg = response.message
                                }
                            }
                            else
                            {
                                is_error = true;
                                msg = "Oops! Server encountered an error.";
                            }

                            //console.log("Message Send Successfully");
                        },
                        error: function (xhr, errmsg, err) {
                            // Show an error
                            is_error = true;
                            msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                        }
                    });
                }
                else
                {
                    is_error = true;
                    msg = 'Please Enter Proper Message Text';
                }
            }
            else
            {
                is_error = true;
                msg = 'Please Enter Subject';
            }
        }
        else
        {
            is_error = true;
            msg = 'Please Enter Uasr Name';
        }


        if (is_error)
        {
            $("#compose_errors").html('');
            $("#compose_errors").html('<p>' + msg + '</p>');
            $("#compose_errors").show();
        }
        else
        {
            $("#compose_errors").html('');
            $("#compose_errors").html('<p>' + msg + '</p>');
            $("#compose_errors").hide();
        }


        $("#msg_sending_loading").hide();
        $("#mail_btn").removeAttr('disabled');
    });

    $("form#chat_msg_form").submit(function (e) {
        e.preventDefault()
        $("#chat_msg_submit").attr('disabled', 'disabled');
        var form_data = $(this).serialize();
        to = $('.chat_screen').attr('data-id');
        sub = $("#chat_msg_subject").val();
        text = $("#chat_msg_text").val();
        is_error = false
        msg = "";
        if (to && !is_empty(to.trim())) {
            if (sub && !is_empty(sub.trim())) {
                if (text && !is_empty(text.trim())) {
                    console.log(form_data);
                    form_data += '&' + $.param({'to': to});
                    $.ajax({
                        url: "/send_chat_message/", // the endpoint
                        type: "POST", // http method
                        data: form_data, // data sent with the delete request
                        success: function (response) {
                            // hide the post
                            if (response)
                            {
                                if (response.is_success)
                                {
                                    rem_msg();
                                    set_msg('success', response.message);

                                    if ($(".conversation_thread").children(".message_thread").length > 0)
                                    {
                                        $(".conversation_thread").append(response.html);
                                        $("#chat_msg_subject").val('');
                                        $("#chat_msg_text").val('');
                                        perform_chat_action();

                                    }
                                    else
                                    {
                                        $(".conversation_thread").html(response.html);
                                    }
                                    show_msg();
                                    $("#chat_msg_submit").removeAttr('disabled');
                                }//message send
                                else
                                {
                                    is_error = true;
                                    msg = response.message
                                }
                            }
                            else
                            {
                                is_error = true;
                                msg = "Oops! Server encountered an error.";
                            }
                            $("#chat_msg_submit").removeAttr('disabled');
                        },
                        error: function (xhr, errmsg, err) {
                            // Show an error
                            is_error = true;
                            msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                            $("#chat_msg_submit").removeAttr('disabled');
                        }
                    });
                }
                else
                {
                    is_error = true;
                    msg = 'Please Enter Proper Message Text';
                }
            }
            else
            {
                is_error = true;
                msg = 'Please Enter Subject';
            }
        }
        else
        {
            is_error = true;
            msg = 'Please Select The Any Conversation To Send Message';
        }


        if (is_error)
        {
            rem_msg();
            set_msg('error', msg);
            show_msg();
        }
        else
        {
            rem_msg();
            set_msg('success', msg);
            show_msg();
        }


        $("#chat_msg_submit").removeAttr('disabled');
    });

    show_msg();
    //end code by kartik for user nevigations open and close menu

    /*Code added by mitesh for skigit statistics*/

    $('.dropdown-handlemystat').on("click", function ()
    {
//getUserStatistics("0");
        if ($(this).next().css('display') == 'none')
        {
            $.ajax({
                url: "/get_statistics/", // the endpoint
                type: "POST", // http method
                data: {'csrfmiddlewaretoken': csrftoken},
                success: function (response)
                {
                    if (response)
                    {
                        if (response.is_success)
                        {
                            $("#skigits").html(response.count_skigits);
                            $("#likes").html(response.count_likes);
                            $("#i_plugged_into").html(response.count_i_plugged_into);
                            //$("#plugged_into_me").html(response.count_i_plugged_into);
                            $("#favourites").html(response.count_favourites);
                            $("#following_me").html(response.count_following_me);
                            $("#i_am_following").html(response.count_i_am_following);
                            $("#friends").html(response.count_friends);
                            $('.dropdown-handlemystat').next().slideDown("slow").css("display", "block");
                        }//message send
                        else
                        {
                            is_error = true;
                            msg = response.message
                        }
                    }
                    else
                    {
                        is_error = true;
                        msg = "Oops! Server encountered an error.";
                    }

                },
                error: function (xhr, errmsg, err) {
                    // Show an error
                    is_error = true;
                    msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                }
            });
        }
        else
        {

            $(this).next().slideUp("slow");
        }
        /*ramalakshmi*/
        $('.divsingshskierr').html("");
    });
    /*End of Code added by mitesh for skigit statistics*/

    /* Code added for add to favourutes*/

    $('.favorites').on("click", function ()
    {
        var skigit_id = $(this).attr("id");
        var favaclass = $(this).children().closest("a").attr("class");
        if (favaclass == "addfavorite")
        {
            $.ajax({
                type: "POST",
                url: "/add_to_favourites/",
                data: {'skigit_id': skigit_id, 'csrfmiddlewaretoken': csrftoken},
                //cache: false,
                success: function (response)
                {
                    $('#fav_count' + skigit_id).html(response.fav_count);
                    if (response.is_fav == 1)
                    {
                        $('.favorites').html("<a class='addfavorite' id='addfavorite_" + skigit_id + "' href='javascript:void(0)' title='Remove Favourite' rel='nofollow'><img src='/static/skigit/detube/images/addstar_icon.png'></a>");

                    }
                    else if (response.is_fav == 0)
                    {
                        $('.favorites').html("<a class='addfavorite' id='addfavorite_" + skigit_id + "' href='javascript:void(0)' title='Add to Favourite' rel='nofollow'><img src='/static/skigit/detube/images/star_icon.png'></a>");
                    }

                }
            });
        }
    });
    /* End of code added for add to favourites */

    /* Code for follow/Unfollow user */

    $('.hrefunfollow').on("click", function ()
    {

        var follow_id = $(this).attr("id");
        var follow_id_replace = follow_id;
        follow_id = follow_id.replace('hrefunfid_', '');

        var skigit_id = $(this).attr("data-cuid");
        $.ajax({
            type: "POST",
            url: "/skigit_follow/",
            data: {'skigit_id': skigit_id},
            success: function (response)
            {
                //alert('You liked this')
                if (response.is_success)
                {
                    if (response.is_follow == 1)
                    {
                        $("#" + follow_id_replace).attr("title", "Unfollow");
                        $("#" + follow_id_replace + "> img").attr("src", "/static/skigit/detube/images/unfollow.png");
                    }
                    else
                    {
                        $("#" + follow_id_replace).attr("title", "Follow");
                        $("#" + follow_id_replace + "> img").attr("src", "/static/skigit/detube/images/flow_icon.png");
                    }
                }
                else
                {
                    $("#popup_msg").text(response.message);
                    $("#popScreen").show();
                }
            },
            error: function (rs, e)
            {
                //alert("Please try again to follow");
                $("#popup_msg").text("Oops...! Error into Following ...! Please try again");
                $("#popScreen").show();
            }
        });

    });

    /* End of code for follow/unfollow */


    /* Friend request code */
    $("#invite_user_friend").submit(function (e) {
        e.preventDefault();
        $("#divshskierrfriends").fadeIn('slow').html('<p>Please Wait</p>');
        $("#invite_btn5030").attr('disabled', 'disabled');
        is_error = false
        msg = "";
        var form_data = $(this).serialize();
        $.ajax({
            type: "POST",
            url: "/invite_friend/send_friend_request/",
            data: form_data,
            success: function (response) {
                if (response)
                {
                    if (response.is_success)
                    {
                        is_error = false;
                        msg = response.message
                    }
                    else {
                        is_error = true;
                        msg = response.message
                    }
                }
                else {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";
                }
                $("#invite_btn5030").removeAttr('disabled');

                if (is_error)
                {
                    var msg1 = '<p style="color:red;"><span><img src="' + DELETE_ICON + '">' + msg + '</span></p>';
                    $("#divshskierrfriends").fadeIn('slow').html(msg1);
                }
                else
                {
                    var msg1 = '<p style="color:green;"><span><img src="' + RIGHT_ICON + '">' + msg + '</span></p>';
                    $("#divshskierrfriends").fadeIn('slow').html(msg1);
                }
            },
            error: function (xhr, errmsg, err) {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#invite_feature_popup").hide();
                show_msg();
                $("#invite_btn5030").removeAttr('disabled');
            },
        });
        $("#invite_btn5030").removeAttr('disabled');
    });
    $(document).on("click", function ()
    {
        $(".responseclass").fadeOut('slow');
    });
    //$(".keywordclass").keyup(function(event)
    $(".keywordclass").on("keyup", function (event) {
        $(this).parent().nextAll().filter('.shareconfirm').hide();
        if ($(this).parent().nextAll().filter('.favshareconfirm'))
            $(this).parent().nextAll().filter('.favshareconfirm').hide();
        if ($(this).parent().nextAll().filter('.originshareconfirm'))
            $(this).parent().nextAll().filter('.originshareconfirm').hide();
        $(this).focus();
        var offset = $(this).offset();
        var width = $(this).width() - 2;
        //$(this).parent().nextAll().filter('.rclass').hide();
        //$(this).nextAll().filter('.lclass').css("visibility",'visible');
        $(this).parent().nextAll().filter(".responseclass").css("left", offset.left);
        $(this).parent().nextAll().filter(".responseclass").css("width", width);
        //alert(event.keyCode);
        var keyword = $(this).val();
        var keyobj = $(this);
        //alert($(this).attr('id'));
        if (keyword.length)
        {
            if (event.keyCode != 40 && event.keyCode != 38 && event.keyCode != 13)
            {
                keyobj.nextAll().filter('.loading').css("visibility", 'visible');
                //$("#loading").css("visibility","visible");
                $.ajax({
                    type: "POST",
                    url: "/get_username/",
                    data: "keyword=" + keyword,
                    success: function (msg) {
                        if (msg.is_success)
                        {
                            var text_str = '<ul id="namefetchlist" class="list">';
                            keyobj.parent().nextAll().filter(".responseclass").html('');
                            for (var i = 0; i < msg.users.length; i++)
                            {
                                text_str += "<li><a href='javascript:void(0);' ><span class='bold'>" + keyword + "</span>" + msg.users[i]['username'].substring(keyword.length) + "</a></li>";
                                //keyobj.parent().nextAll().filter(".responseclass").fadeIn("slow").append("<li><a href='javascript:void(0);' ><span class='bold'>" + keyword + "</span>" + msg.users[i]['username'].substring(keyword.length) + "</a></li>");
                            }
                            text_str += '</ul>';
                            keyobj.parent().nextAll().filter(".responseclass").fadeIn("slow").html(text_str);
                            //alert(keyobj.attr('id'));
                            //keyobj.parent().nextAll().filter(".emailresponseclass").fadeIn("slow").html(msg);
                        }
                        else
                        {
                            keyobj.parent().nextAll().filter(".responseclass").fadeIn("slow");
                            keyobj.parent().nextAll().filter(".responseclass").html('<div style="text-align:center;color:#000;">No Matches Found</div>');
                        }
                        keyobj.nextAll().filter('.loading').css("visibility", "hidden");
                    },
                    error: function (xhr, errmsg, err) {
                        // Show an error
                        is_error = true;
                        msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                        rem_msg();
                        set_msg('error', msg);
                        $("#invite_feature_popup").hide();
                        show_msg();
                    }
                });
            }
            else
            {
                switch (event.keyCode)
                {
                    case 40:
                        {
                            found = 0;
                            $("li").each(function () {
                                if ($(this).attr("class") == "selected")
                                    found = 1;
                            });
                            if (found == 1)
                            {
                                var sel = $("li[class='selected']");
                                sel.next().addClass("selected");
                                sel.removeClass("selected");
                            }
                            else
                                $("li:first").addClass("selected");
                        }
                        break;
                    case 38:
                        {
                            found = 0;
                            $("li").each(function () {
                                if ($(this).attr("class") == "selected")
                                    found = 1;
                            });
                            if (found == 1)
                            {
                                var sel = $("li[class='selected']");
                                sel.prev().addClass("selected");
                                sel.removeClass("selected");
                            }
                            else
                                $("li:last").addClass("selected");
                        }
                        break;
                    case 13:
                        keyobj.parent().nextAll().filter(".responseclass").fadeOut("slow");
                        keyobj.parent().nextAll().filter(".responseclass").val($("li[class='selected'] a").text());
                        break;
                }
            }
        }
        else
            keyobj.parent().nextAll().filter(".responseclass").fadeOut("slow");
    });
    //$(".responseclass").mouseover(function(){
    $(".responseclass").on("mouseover", function () {
        var res = $(this);
        res.find("li a:first-child").on("mouseover", function () {
            $(this).addClass("selected");
        });
        res.find("li a:first-child").on("mouseover", function () {
            $(this).removeClass("selected");
        });
        res.find("li a:first-child").on("click", function () {
            $(".keywordclass").val($(this).parent().text());
            res.fadeOut("slow");
        });
    });



    /*end of friend request code*/

    /* Friend request Code*/
    $('#head_frireq_popup').hide();
    $('#head_frireq').click(function () {
        if ($('.head_share_popupbox'))
            $('.head_share_popupbox').css("display", "none"); //sharebox
        if ($(".joinTooltip_content"))
            $(".joinTooltip_content").css("display", "none"); //joinbox
        if ($(".dropdown-content"))
            $(".dropdown-content").css("display", "none"); //useraccout
        if ($('.head_share_favpopup'))
            $('.head_share_favpopup').css("display", "none"); //fav sharebox
        if ($m('.invitebox'))
            $('.invitebox').css("display", "none"); //friend invite
        if ($('.head_share_origin'))
            $('.head_share_origin').css("display", "none"); //origin sharebox
        $('#head_notification_popup').slideUp("slow").css("display", "none");
        $('#head_email_popup').slideUp("slow").css("display", "none");
        if ($("#head_frireq_popup").css("display") == "none")
        {
            $('#head_frireq_popup').show();
            getfriend_request();
            console.log('true' + $("#head_frireq_popup").css("display"));
        }
        else {
            $('#head_frireq_popup').hide();
            console.log('false' + $("#head_frireq_popup").css("display"));
        }
        //$('#head_frireq_popup').slideDown("slow");
    });
    /*end */

    /* Notification Popup */
    $('#head_notification_popup').hide();
    $('#head_notification').click(
            function () {
                if ($('.head_share_popupbox'))
                    $('.head_share_popupbox').css("display", "none"); //sharebox
                if ($(".joinTooltip_content"))
                    $(".joinTooltip_content").css("display", "none"); //joinbox
                if ($(".dropdown-content"))
                    $(".dropdown-content").css("display", "none"); //useraccout
                if ($('.head_share_favpopup'))
                    $('.head_share_favpopup').css("display", "none"); //fav sharebox
                if ($('.invitebox'))
                    $('.invitebox').css("display", "none"); //friend invite
                if ($('.head_share_origin'))
                    $('.head_share_origin').css("display", "none"); //origin sharebox
                $('#head_frireq_popup').slideUp("slow").css("display", "none");
                $('#head_email_popup').slideUp("slow").css("display", "none");
                if ($("#head_notification_popup").css("display") == "none")
                {
                    $('#head_notification_popup').show();
                    get_notification();
                    console.log('true' + $("#head_notification_popup").css("display"));
                }
                else {
                    $('#head_notification_popup').hide();
                    console.log('false' + $("#head_notification_popup").css("display"));
                }

            }
    );
    $("#skigitt_email_close3").click(function ()
    {
        $("#head_notification_popup").hide();
        $("#head_frireq_popup").hide();
        $("#head_email_popup").hide();

    });
    /*End Notification pop up*/

}); //main document ready function


/* javascript functions  */

function close_popup_box()
{
    $("#error_message").hide();
    $("#singlehead_flag_popuploop").hide();
}

function hidemsg() {
    var messagesHeights = new Array(); // this array will store height for each
    to = 0;
    // Show message

    for (var i = 0; i < myMessages.length; i++)
    {
        //alert(i);
        //$('.' + myMessages[i]).animate({top: "0"}, 500);
        if ($('.' + myMessages[i]).length > 0)
        {
            //$('.' + myMessages[i]).show();
            to += $('.' + myMessages[i]).outerHeight();
            $('.' + myMessages[i]).animate({top: -to}, 1200);
            //$(this).animate({top: -$(this).outerHeight()}, 500);
            //messagesHeights[i] = $('.' + myMessages[i]).outerHeight();

            //$('.' + myMessages[i]).css(top, +messagesHeights[i]); //move element outside viewport
        }

        showMessage(myMessages[i]);
    }
}
function hideAllMessages()
{
    var messagesHeights = new Array(); // this array will store height for each

    for (i = 0; i < myMessages.length; i++)
    {
        messagesHeights[i] = $('.' + myMessages[i]).outerHeight();
        $('.' + myMessages[i]).css('top', -messagesHeights[i]); //move element outside viewport
    }
}

function showMessage(type)
{
    $('.' + type + '-trigger').click(function () {
        hideAllMessages();
        alert(type);
        $('.' + type).animate({top: "0"}, 500);
    });
}
function getInboxMessages()
{
    var is_error = false;
    var error_type = '';
    var msg;
    var send_data = {};

    if ($("#head_email_popup").css('display') == 'block') {

        msg = '<div class="inner_wrap"><img src="/static/skigit/detube/images/ring.svg"></div>';
        /*    str1 = "<div style='text-align:center'>Please wait..</div>"; */
        $('#ajaxinboxresponse').html(msg);



        $.ajax({
            type: "GET",
            url: "/get_messages/",
            data: send_data,
            //cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        msg = response.conv_html;
                        $('#ajaxinboxresponse').html(msg);
                        perform_msg_action();
                    }
                    else
                    {
                        msg = response.message;
                        $('#ajaxinboxresponse').html(msg);
                    }
                }
                else
                {
                    msg = "Oops! Server Encountered an error.";
                    $('#ajaxinboxresponse').html(msg);
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_email_popup").hide();
                    show_msg();
                }

            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;

                rem_msg();
                set_msg('error', msg);
                $("#head_email_popup").hide();
                show_msg();
            }

        });
    }
}

function getfriend_request() {
    var is_error = false;
    var error_type = '';
    var msg;
    var send_data = {};

    if ($("#head_frireq_popup").css('display') == 'block') {

        msg = '<div class="inner_wrap"><img src="/static/skigit/detube/images/ring.svg"></div>';
        /*    str1 = "<div style='text-align:center'>Please wait..</div>"; */
        $('#ajaxinboxresponse1').html(msg);

        $.ajax({
            type: "POST",
            url: "/friend/request/get/",
            data: send_data,
            //cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        msg = response.message;
                        $('#ajaxinboxresponse1').fadeIn('slow').html(msg);
                        $("#head_frireq").children('.countspan').fadeOut('slow');
                        perform_friend_request_action();
                    }
                    else
                    {
                        msg = response.message;
                        $('#ajaxinboxresponse1').html(msg);
                    }
                }
                else
                {
                    msg = "Oops! Server Encountered an error.";
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_frireq_popup").css('display', 'none');
                    show_msg();
                }

            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;

                rem_msg();
                set_msg('error', msg);
                $("#head_frireq_popup").css('display', 'none');
                show_msg();
            }

        });
    }
}

function perform_msg_action() {

    $("span.read").off();
    $("span.unread").off();
    $("span.delete").off();

    $("span.read").click(function () {

        console.log('read');
        var is_error = false;
        var $my_this = $(this);
        var error_type = '';
        var msg;
        var thread_id;
        var send_data = {};
        thread_id = $my_this.parents(".message_thread").attr('data-id').trim();
        send_data = {'thread_id': thread_id};
        $.ajax({
            type: "POST",
            url: "/messages/read/",
            data: send_data,
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        $my_this.parents(".message_thread").removeClass('msg_read');
                        $my_this.parents(".message_thread").children().find('span.msg_unread_count').fadeOut('slow');
                        $my_this.parents(".message_thread").children().find("span.read img").remove(); //MSG_READ_IMG
                        $my_this.parents(".message_thread").children().find("span.read").html(MSG_UNREAD_IMG); //MSG_READ_IMG
                        $my_this.removeClass('read');
                        $my_this.addClass('unread');
                        var MSG_NOTIFY_COUNT = parseInt($("#head_email").children('.countspan').find('a').html());

                        if (MSG_NOTIFY_COUNT && MSG_NOTIFY_COUNT > 0)
                        {
                            if (MSG_NOTIFY_COUNT > 1)
                            {
                                MSG_NOTIFY_COUNT = parseInt(MSG_NOTIFY_COUNT - 1);
                                $("#head_email").children('.countspan').find('a').html(MSG_NOTIFY_COUNT);
                            }
                            if (MSG_NOTIFY_COUNT == 1)
                            {
                                MSG_NOTIFY_COUNT = parseInt(0);
                                $("#head_email").children('.countspan').fadeOut('slow');
                                $("#head_email").children('.countspan').find('a').html(MSG_NOTIFY_COUNT);

                            }
                        }

                        perform_msg_action();
                    }
                    else
                    {
                        is_error = true;
                        msg = response.message;
                    }
                }
                else
                {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";

                }

                if (is_error) {
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_email_popup").hide();
                    show_msg();
                }
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#head_email_popup").hide();
                show_msg();
            }

        });
    });
    $("span.unread").click(function () {

        console.log('unread');
        var is_error = false;
        var $my_this = $(this);
        var error_type = '';
        var msg;
        var thread_id;
        var send_data = {};
        thread_id = $my_this.parents(".message_thread").attr('data-id').trim();
        send_data = {'thread_id': thread_id};
        $.ajax({
            type: "POST",
            url: "/messages/unread/",
            data: send_data,
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        $my_this.parents(".message_thread").addClass('msg_read');
                        $my_this.parents(".message_thread").children().find('span.msg_unread_count').html('(1)').fadeIn('slow');
                        $my_this.parents(".message_thread").children().find("span.unread img").remove(); //MSG_READ_IMG
                        $my_this.parents(".message_thread").children().find("span.unread").html(MSG_READ_IMG); //MSG_READ_IMG
                        $my_this.removeClass('unread');
                        $my_this.addClass('read');
                        perform_msg_action();
                    }
                    else
                    {
                        is_error = true;
                        msg = response.message;
                    }
                }
                else
                {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";

                }

                if (is_error) {
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_email_popup").hide();
                    show_msg();
                }
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#head_email_popup").hide();
                show_msg();
            }

        });


    });
    $("span.delete").click(function () {

        console.log('delete');
        var is_error = false;
        var $my_this = $(this);
        var error_type = '';
        var msg;
        var thread_id;
        var send_data = {};
        thread_id = $my_this.parents(".message_thread").attr('data-id').trim();
        send_data = {'thread_id': thread_id};
        $.ajax({
            type: "POST",
            url: "/messages/delete/",
            data: send_data,
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        $my_this.parents(".message_thread").replaceWith(response.message);
                        perform_msg_action();
                    }
                    else
                    {
                        is_error = true;
                        msg = response.message;
                    }
                }
                else
                {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";

                }

                if (is_error) {
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_email_popup").hide();
                    show_msg();
                }
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#head_email_popup").hide();
                show_msg();
            }

        });


    });

}



function perform_chat_action() {
    $("span.chat_delete_msg").off();
    $("span.conv_unread").off();
    $("span.conv_read").off();

    $("span.conv_read").click(function () {

        console.log('read');
        var is_error = false;
        var $my_this = $(this);
        var error_type = '';
        var msg;
        var thread_id;
        var send_data = {};
        thread_id = $my_this.parents(".conversation").attr('data-id').trim();
        send_data = {'thread_id': thread_id};
        $.ajax({
            type: "POST",
            url: "/messages/read/",
            data: send_data,
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        $my_this.parents(".conversation").removeClass('msg_read');
                        $my_this.parents(".conversation").children().find('span.msg_unread_count').fadeOut('slow');
                        $my_this.parents(".conversation").children().find("span.conv_read img").remove(); //MSG_READ_IMG
                        $my_this.parents(".conversation").children().find("span.conv_read").html(MSG_UNREAD_IMG); //MSG_READ_IMG
                        $my_this.removeClass('conv_read');
                        $my_this.addClass('conv_unread');
                        var MSG_NOTIFY_COUNT = parseInt($("#head_email").children('.countspan').find('a').html());

                        if (MSG_NOTIFY_COUNT && MSG_NOTIFY_COUNT > 0)
                        {
                            if (MSG_NOTIFY_COUNT > 1)
                            {
                                MSG_NOTIFY_COUNT = parseInt(MSG_NOTIFY_COUNT - 1);
                                $("#head_email").children('.countspan').find('a').html(MSG_NOTIFY_COUNT);
                            }
                            if (MSG_NOTIFY_COUNT == 1)
                            {
                                MSG_NOTIFY_COUNT = parseInt(0);
                                $("#head_email").children('.countspan').fadeOut('slow');
                                $("#head_email").children('.countspan').find('a').html(MSG_NOTIFY_COUNT);

                            }
                        }

                        perform_chat_action();
                    }
                    else
                    {
                        is_error = true;
                        msg = response.message;
                    }
                }
                else
                {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";

                }

                if (is_error) {
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_email_popup").hide();
                    show_msg();
                }
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#head_email_popup").hide();
                show_msg();
            }

        });
    });

    $("span.conv_unread").click(function () {

        console.log('unread');
        var is_error = false;
        var $my_this = $(this);
        var error_type = '';
        var msg;
        var thread_id;
        var send_data = {};
        thread_id = $my_this.parents(".conversation").attr('data-id').trim();
        send_data = {'thread_id': thread_id};
        $.ajax({
            type: "POST",
            url: "/messages/unread/",
            data: send_data,
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        $my_this.parents(".conversation").addClass('msg_read');
                        $my_this.parents(".conversation").children().find('span.msg_unread_count').html('(1)').fadeIn('slow');
                        $my_this.parents(".conversation").children().find("span.conv_unread img").remove(); //MSG_READ_IMG
                        $my_this.parents(".conversation").children().find("span.conv_unread").html(MSG_READ_IMG); //MSG_READ_IMG
                        $my_this.removeClass('conv_unread');
                        $my_this.addClass('conv_read');
                        perform_chat_action();
                    }
                    else
                    {
                        is_error = true;
                        msg = response.message;
                    }
                }
                else
                {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";

                }

                if (is_error) {
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_email_popup").hide();
                    show_msg();
                }
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#head_email_popup").hide();
                show_msg();
            }

        });


    });

    $("span.chat_delete_msg").click(function () {

        console.log('delete');
        var is_error = false;
        var $my_this = $(this);
        var error_type = '';
        var msg;
        var thread_id;
        var msg_id;
        var send_data = {};
        thread_id = $my_this.parents(".chat_screen").attr('data-id').trim();
        msg_id = $my_this.parents(".message_thread").attr('data-id').trim();
        send_data = {'thread_id': thread_id, 'message_id': msg_id};
        console.log(send_data);
        $.ajax({
            type: "POST",
            url: "/messages/chat_message_delete/",
            data: send_data,
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        $my_this.parents(".message_thread").remove();
                        if ($(".conversation_thread").children(".message_thread").length <= 0)
                        {
                            $(".conversation_thread").html('<h3>No Message Left In Conversation</h3>');
                        }
                    }
                    else
                    {
                        is_error = true;
                        msg = response.message;
                    }
                }
                else
                {
                    is_error = true;
                    msg = "Oops! Server Encountered an error.";

                }

                if (is_error) {
                    rem_msg();
                    set_msg('error', msg);
                    show_msg();
                }
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                show_msg();
            }

        });


    });
}


function perform_friend_request_action() {
    var is_error = false;
    var error_type = '';
    var msg;
    var thread_id;
    var send_data = {};
    var form_data;
    var lodder = '<div class="outer_wrap"><img src="/static/skigit/detube/images/ring.svg"></div>';
    $("form.friend_request_form").off();
    $("form.friend_request_form").children().find("input[type=submit]").off();
    $("form.friend_request_form").children().find("input[type=submit]").click(function () {
        $(this).attr("clicked", "true");
    });

    $("form.friend_request_form").submit(function (e) {
        e.preventDefault();
        var $mythis = $(this);
        form_data = $(this).serialize();
        form_data += '&' + $.param({'submit': $(this).children().find("input[type=submit][clicked=true]").val()});
        $(this).children().find("input[type=submit][clicked=true]").removeAttr('clicked');
        $(this).parents('.message_thread').append(lodder);
        $.ajax({
            type: "POST",
            url: "/friend/request/action/",
            data: form_data,
            //cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {

                        msg = response.message;
                        $mythis.parents('.message_thread').children('div.msg_action').html(msg);
                        $mythis.parents('.message_thread').children('div.outer_wrap').remove();
                        $mythis.parents('.message_thread').children().find('div.outer_wrap').remove();

                    }
                    else
                    {
                        msg = response.message;
                        rem_msg();
                        set_msg('error', msg);
                        $("#head_frireq_popup").css('display', 'none');
                        show_msg();
                        $mythis.parents('.message_thread').find('.outer_wrap').remove();
                    }
                }
                else
                {
                    msg = "Oops! Server Encountered an error.";
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_frireq_popup").css('display', 'none');
                    show_msg();
                }
                $(this).parents('.message_thread').find('.outer_wrap').remove();
            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
                rem_msg();
                set_msg('error', msg);
                $("#head_frireq_popup").css('display', 'none');
                show_msg();
                $(this).parents('.message_thread').find('outer_wrap').remove();
            }

        });

        console.log(form_data);
    });
}


function get_notification(){
    var is_error = false;
    var error_type = '';
    var msg;
    var send_data = {};

    if ($("#head_notification_popup").css('display') == 'block') {

        msg = '<div class="inner_wrap"><img src="/static/skigit/detube/images/ring.svg"></div>';
        /*    str1 = "<div style='text-align:center'>Please wait..</div>"; */
        $('#ajaxinboxresponse3').html(msg);

        $.ajax({
            type: "POST",
            url: "/notification/get/",
            cache: false,
            success: function (response)
            {
                if (response)
                {
                    if (response.is_success)
                    {
                        msg = response.message;
                        $('#ajaxinboxresponse3').fadeIn('slow').html(msg);
                        $("#head_notification").children('.countspan').fadeOut('slow');

                    }
                    else
                    {
                        msg = response.message;
                        $('#ajaxinboxresponse3').html(msg);
                    }
                }
                else
                {
                    msg = "Oops! Server Encountered an error.";
                    rem_msg();
                    set_msg('error', msg);
                    $("#head_notification_popup").css('display', 'none');
                    show_msg();
                }

            },
            error: function (xhr, errmsg, err)
            {
                // Show an error
                is_error = true;
                msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;

                rem_msg();
                set_msg('error', msg);
                $("#head_notification_popup").css('display', 'none');
                show_msg();
            }

        });
    }
}
function logo_imgURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
            $('#logo_img')
                    .attr('src', e.target.result);
            //.width(150)
            //.height(200);
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function profile_imgURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
            $('#profile_img')
                    .attr('src', e.target.result);
            //.width(150)
            //.height(200);
        };
        reader.readAsDataURL(input.files[0]);
    }
}


// Code added by mitesh for skigit like  unlike

function getCookie(name)
{
    var cookieValue = null;
    if (document.cookie && document.cookie != '')
    {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++)
        {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '='))
            {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// End of code added for skigit like unlike

//count views
function countviews(skigit_id)
{
    //var $ = jQuery.noConflict();
    var csrftoken = getCookie('csrftoken');
    $.ajax({
        type: "POST",
        url: "/skigit_view_count/",
        data: {'skigit_id': skigit_id, 'csrfmiddlewaretoken': csrftoken},
        //dataType: "text",
        success: function (response)
        {
            if (response.is_success)
            {
                $("#viewscount" + skigit_id).html(response.view_count);
            }
            else
            {
                $("#popup_msg").text("Invalid details found for count views of skigit");
                $("#popScreen").show();
            }
        },
        error: function (rs, e)
        {
            //alert("Error into updating view counter");
        }
    });
} // End of function countviews


function is_empty(str) {
    return !str || !/[^\s]+/.test(str);
}

function close_popup_box()
{
    $("#error_message").hide();
    $("#singlehead_flag_popuploop").hide();
}

function rem_msg() {
    $(".notify_msg_div").html('');
}

// function set_msg(tag, msg) {
//     msg_string = '<div style="display:none;"  class="' + tag + ' message"><h3>' + msg + '</h3></div>';
//     $(".notify_msg_div").append(msg_string);
// }

function show_msg() {
    hideAllMessages();
    var messagesHeights = new Array(); // this array will store height for each
    to = 0;
    // Show message

    for (var i = 0; i < myMessages.length; i++)
    {
        //alert(i);
        //$('.' + myMessages[i]).animate({top: "0"}, 500);
        if ($('.' + myMessages[i]).length > 0)
        {
            $('.' + myMessages[i]).show();
            $('.' + myMessages[i]).animate({top: to}, 1200);
            //messagesHeights[i] = $('.' + myMessages[i]).outerHeight();
            to += $('.' + myMessages[i]).outerHeight();
            //$('.' + myMessages[i]).css(top, +messagesHeights[i]); //move element outside viewport
        }

        showMessage(myMessages[i]);
    }

    // When message is clicked, hide it
    $('.message').click(function () {
        $(this).animate({top: -$(this).outerHeight()}, 500);
    });
    setTimeout(function () {
        hidemsg();
    }, 12000)
}

function getUserStatistics(uid)
{
    var uid = uid;
    var friends = "0";
    var curuser = "";
    $.ajax({
        type: "GET",
        url: "http://demo.mrphpguru.com/skigitdev/detube/ajax_get_statistics.php",
        data:
                {
                    uid: uid,
                    friends: friends,
                    curuser: curuser
                },
        cache: false,
        success: function (response)
        {
            $('#head_share_popuploop11').html(response);
        }
    });
}

function ajaxfollow(who, whom, fol)
{
    if (fol == "follow")
    {
        $.ajax({
            url: "http://demo.mrphpguru.com/skigitdev/detube/ajaxfollow.php",
            type: 'POST',
            data: "who=" + who + "&whom=" + whom + "&fol=" + fol,
            cache: false,
            success: function (res)
            {
                resplus = "<a data-cuid='" + who + "' class='hrefunfollow' title='Unfollow' id='hrefunfid_" + whom + "' href='javascript:void(0);'>" + res + "</a>";
                $('.followspan').html(resplus);
            }
        });
    }
    else if (fol == "unfollow")
    {
        $.ajax({
            url: "http://demo.mrphpguru.com/skigitdev/detube/ajaxfollow.php",
            type: 'POST',
            data: "who=" + who + "&whom=" + whom + "&fol=" + fol,
            cache: false,
            success: function (res)
            {
                resplus = "<a data-cuid='" + who + "' class='hreffollow' title='Follow' id='hrefid_" + whom + "' href='javascript:void(0);'>" + res + "</a>";
                $('.followspan').html(resplus);
            }
        });
    }
    return false;
}

//end

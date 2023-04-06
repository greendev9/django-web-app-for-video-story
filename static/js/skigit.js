$j = jQuery.noConflict();

$j(document).ready(function() {

  // When click browser back and forward button close the skigit modal popup and stay with the current location!
  if (window.history && window.history.pushState) {
    window.history.pushState('', null, './');
    $j(window).on('popstate', function() {
      if (($j("#skigit-modal").data('bs.modal') || {}).isShown) {
        $j("#skigit-modal").modal("hide");
      }
    });
  }

  var img1 = new Image();
  var img2 = new Image();
  var myMessages = ['info', 'warning', 'error', 'success']; // define the messages types
  //var DELETE_ICON = 'static/skigit/wp-content/themes/detube/images/deleteIcon.png';
  //var RIGHT_ICON = 'ttp://static.skigit.com/skigit/wp-content/themes/detube/images/success_icon.png';
  
   var DELETE_ICON = '/static/skigit/wp-content/themes/detube/images/deleteIcon.png';
  var RIGHT_ICON = '/static/skigit/wp-content/themes/detube/images/success_icon.png';
  
  
  var DELETE_ICON_IMG = '<img width="17" height="17" src="' + DELETE_ICON + '">';
  var RIGHT_ICON_IMG = '<img width="17" height="17" src="' + RIGHT_ICON + '">';
  var BASE_URL = '/';

  function get_skigit_statistics(skigit_id){
    $j.ajax({
    type: "POST",
    url: "/skigit_statistics/",
    data: {'skigit_id': skigit_id, 'csrfmiddlewaretoken': getCookie('csrftoken')},
    success: function (response) {
      if (response.is_success) {
        $j('li').find('#id_plug_count').html(response.plug_count);
        $j('li').find('#id_view_count').html(response.view_count);
        $j('li').find('#id_favorites').html(response.fav_count);
        $j('li').find('#id_likes').html(response.like_count);
        $j('li').find('#id_share').html(response.share_count)
      }
    },
    error: function (rs, e) {
      $j("#popup_msg").text("Error into Skigit Statistic Please try again");
      $j("#popScreen").show();
    }
  });
  };

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = $j.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function is_empty(str) {
    return !str || !/[^\s]+/.test(str);
  }

  function rem_msg() {
    $j(".notify_msg_div").html('');
  }

  function set_msg(tag, msg) {
    msg_string = '<div style="display:none;"  class="' + tag + ' message"><h3>' + msg + '</h3></div>';
    $j(".notify_msg_div").append(msg_string);
  }

  function show_msg() {
    hideAllMessages();
    to = 0;
    for (var i = 0; i < myMessages.length; i++) {
      if ($j('.' + myMessages[i]).length > 0) {
        $j('.' + myMessages[i]).show();
        $j('.' + myMessages[i]).animate({ top: to }, 1200);
        to += $j('.' + myMessages[i]).outerHeight();
      }
      showMessage(myMessages[i]);
    }

    // When message is clicked, hide it
    $j('.message').click(function() {
      $j(this).animate({ top: -$j(this).outerHeight() }, 500);
    });
    setTimeout(function() {
      hidemsg();
    }, 12000)
  }

  function hidemsg() {
    to = 0;
    for (var i = 0; i < myMessages.length; i++) {
      if ($j('.' + myMessages[i]).length > 0) {
        to += $j('.' + myMessages[i]).outerHeight();
        $j('.' + myMessages[i]).animate({ top: -to }, 1200);
      }
      showMessage(myMessages[i]);
    }
  }

  function hideAllMessages() {
    var messagesHeights = []; // this array will store height for each
    for (var i = 0; i < myMessages.length; i++) {
      messagesHeights[i] = $j('.' + myMessages[i]).outerHeight();
      $j('.' + myMessages[i]).css('top', '-' + messagesHeights[i]); //move element outside viewport
    }
  }

  function showMessage(type) {
    $j('.' + type + '-trigger').click(function() {
      hideAllMessages();
      $j('.' + type).animate({ top: "0" }, 500);
    });
  }

  function logo_imgURL(input) {
    if (input.files && input.files[0]) {
      var reader = new FileReader();
      reader.onload = function(e) {
        $j('#logo_img')
          .attr('src', e.target.result);
      };
      reader.readAsDataURL(input.files[0]);
    }
  }

  function profile_imgURL(input) {
    if (input.files && input.files[0]) {
      var reader = new FileReader();
      reader.onload = function(e) {
        $j('#user_profile_image')
          .attr('src', e.target.result);
      };
      reader.readAsDataURL(input.files[0]);
    }
  }

  function password_reset_email_check() {

    var id_email = $j('#id_email').val().trim();
    var is_error = false;
    //var is_success = false
    var msg = "...";

    if (id_email && !is_empty(id_email)) {
      $j.ajax({
        url: "/email_exits_check/", // the endpoint
        type: "POST", // http method
        data: { 'email': id_email }, // data sent with the delete request
        success: function(response) {
          if (response) {
            if (response.is_success) {
              is_error = false;
              msg = response.message;
            } else {
              is_error = true;
              msg = response.message;
            }
          } else {
            is_error = true;
            msg = "Oops! Server encountered an error.";
          }
        },
        error: function(xhr, errmsg, err) {
          is_error = true;
          msg = "Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
        }
      });
    } else {
      is_error = true;
      msg = "<img width='25' src='/static/images/error_icon.png'>Please enter a valid email address."
    }

    setTimeout(function() {
      if (is_error) {
        $j("#password_reset_error").html("<p class='error_msg'>" + msg + "</p>");
        return is_error
      } else {
        $j("#password_reset_error").html("<p class='success_msg'>" + msg + "</p>");
        return is_error
      }
    }, 80000);
  }

  var forceSubmitForm = false;

  $j("img.img2").hide();
  show_msg();
  $j("#header .navbar-nav li a").hover(function() {
    var $jimg1 = $j(this).children('.img1');
    var $jimg2 = $j(this).children('.img2');
    if ($jimg1 && $jimg1.length === 1 && $jimg2 && $jimg2.length === 1) {
      img1.src = $jimg1.attr('src');
      img2.src = $jimg2.attr('src');
      $jimg2.attr('src', img1.src);
      $jimg1.attr('src', img2.src);
    }
  }, function() {
    var $jimg1 = $j(this).children('.img2');
    var $jimg2 = $j(this).children('.img1');
    if ($jimg1 && $jimg1.length === 1 && $jimg2 && $jimg2.length === 1) {
      img1.src = $jimg1.attr('src');
      img2.src = $jimg2.attr('src');
      $jimg2.attr('src', img1.src);
      $jimg1.attr('src', img2.src);
    }
  });
  $j('.dropdown-menu').click(function(event) {
    event.stopPropagation();
  });
  $j.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        if(!getCookie('csrftoken')) window.location.reload() // incase csrf token is removed from cookies e.g clear cache
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    }
  });

  // $j("form#form_login").submit(function (e) {
  //   e.preventDefault()
  //   $j("#chat_msg_submit").attr('disabled', 'disabled');
  //   var form_data = $j(this).serialize();
  //   var user_login = $j('#user_login').val().trim();
  //   var user_pass = $j("#user_pass").val().trim();
  //   var is_error = false
  //   var is_success = false
  //   var $jsubmit = $j("form#form_login").children().find("input[type='submit']");
  //   $jsubmit.attr('disabled', 'disabled');
  //   var msg = "";
  //   if (user_login && !is_empty(user_login.trim())) {
  //     if (user_pass && !is_empty(user_pass.trim())) {
  //       $j.ajax({
  //         url: "/login_ajax/", // the endpoint
  //         type: "POST", // http method
  //         data: form_data, // data sent with the delete request
  //         success: function (response) {
  //           // hide the post
  //           if (response) {
  //             if (response.is_success) {
  //               is_success = true
  //               msg = response.message
  //               setTimeout(function () {
  //                 window.location = response.base_location;
  //               }, 500);
  //             }//message send
  //             else {
  //               is_success = false
  //               msg = response.message
  //             }
  //           }
  //           else {
  //             is_success = false
  //             msg = "<span style='font-size:20px;'><i class='glyphicon glyphicon-remove-circle' style='top: 5px !important;' /></span> Oops! Server encountered an error.";
  //           }
  //           if (is_success) {
  //             $j("#login_ingo_msg").html('<p class="success_msg" >' + msg + '</p>');
  //           }
  //           else {
  //             $j("#login_ingo_msg").html('<p class="error_msg" >' + msg + '</p>');
  //           }
  //           setTimeout(function () {
  //             $j("#login_ingo_msg > * ").fadeOut('slow');
  //             $j("#login_ingo_msg").empty();
  //           }, 6000);
  //           $jsubmit.removeAttr('disabled');
  //         },
  //         error: function (xhr, errmsg, err) {
  //           // Show an error
  //           is_error = true;
  //           msg = "<span style='font-size:20px;'><i class='glyphicon glyphicon-remove-circle' style='top: 5px !important;' /></span> Oops! We have encountered an error." + xhr.status + ": " + xhr.responseText;
  //           $j("#smallModal").hide();
  //           $jsubmit.removeAttr('disabled');
  //           if (is_error) {
  //             rem_msg();
  //             set_msg('error', msg);
  //             show_msg();
  //           }
  //         }
  //       });
  //     }
  //     else {
  //       is_error = true;
  //       msg = "<span class='sign-error'><i class='glyphicon glyphicon-remove-circle' /></span><span class='text-error'>Your username and/or password are incorrect. Please try again.</span>";
  //     }
  //   }
  //   else {
  //     is_error = true;
  //     msg = "<span class='sign-error'><i class='glyphicon glyphicon-remove-circle' /></span><span class='text-error'>Your username and/or password are incorrect. Please try again.</span>";
  //   }
  //
  //   if (is_error) {
  //     $j("#login_ingo_msg").html('<p class="error_msg" >' + msg + '</p>');
  //   }
  //
  //   setTimeout(function () {
  //     $j("#login_ingo_msg > * ").fadeOut('slow');
  //     $j("#login_ingo_msg").empty();
  //   }, 5000);
  //   $jsubmit.removeAttr('disabled');
  // });
  $j('.img-zoom').hover(function() {
    $j(this).addClass('transition');
  }, function() {
    $j(this).removeClass('transition');
  });

  if ($j("#id_logo_img").length === 1) {
    $j("#id_logo_img").attr("onchange", "logo_imgURL(this);");
  }
  if ($j("#id_profile_img").length === 1) {
    $j("#id_profile_img").attr("onchange", "profile_imgURL(this);");
  }

  // ############# Validator methods #############
  // Custom email checker!
  $j.validator.addMethod("customemail",
    function (value, element) {
      return /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(value);
    }, "<img width='25' src='/static/images/error_icon.png'> Please enter a valid email address."
  );

  // Custom uppercase letter checker
  $j.validator.addMethod("oneuppercaseletter",
      function (value, element) {
          return /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,16}$/.test(value);
      }, "Your New Password does not meet the minimum requirements. Please try again."
  );

    // username space checker
  $j.validator.addMethod("nospace",
    function (value, element) {
        return /^[A-Za-z0-9_]*$/.test(value);
    }, "Your username must contain only letters, numbers and underscores. Spaces are NOT allowed."
  );

  // ############# Validator methods End #############

  viewCount = function(video_id) {
    var skigit_id = video_id;
    $j.ajax({
      url: "/view_count_update/",
      type: "POST",
      data: {
        'skigit_id': skigit_id,
        csrfmiddlewaretoken: getCookie('csrftoken')
      },
      success: function(response) {
        if (response.is_success) {
          $j('#view_count' + skigit_id).text(parseInt(response.view_count))
        }
      }
    });
  };

  $j('#user_action #general_notify').click(function() {
    $j.post("/notification/get/", {},
      function(data, status) {
        if (data.is_success) {
          msg = data.message;
          $j('#gen_notification').fadeToggle('slow').html(msg);
        }
      });
  });

  /*$j('.dropdown').hover(function () {
      $j(this).addClass('show');
      $j(this).children('.dropdown-menu').addClass('show');
    },
    function () {
      $j(this).removeClass('show');
      $j(this).children('.dropdown-menu').removeClass('show');
    });*/

  // Drop down shown mouseover in large devices and click in small devices
  function toggleNavbarMethod() {
    if ($j(window).width() > 768) {
      $j('.dropdown').on('mouseover', function() {
        $j('.dropdown-toggle', this).trigger('click');
      }).on('mouseout', function() {
        $j('.dropdown-toggle', this).trigger('click').blur();
      });
    } else {
      $j('.dropdown').off('mouseover').off('mouseout');
    }
  }
  toggleNavbarMethod();
  $j(window).resize(toggleNavbarMethod);

  $j('.image-business').hover(function() {
    var vid = $j(this).data('vid');
    var id = '#business_enlarge' + vid;
    $j(id).fadeIn();
  }, function() {
    var vid = $j(this).data('vid');
    var id = '#business_enlarge' + vid;
    $j(id).fadeOut();
  });

  $j("#friendPopover").popover({
    html: true,
    title: "Friends and Invites",
    placement: "bottom",
    content: $j("#friendContent").html()
  });

  $j('body').mouseup(function(e) {
    $j('[data-original-title]').each(function() {
      //the 'is' for buttons that trigger popups
      //the 'has' for icons within a button that triggers a popup

      if (!$j(this).is(e.target) && $j(this).has(e.target).length === 0 &&
        $j('.popover').has(e.target).length === 0) {
        var popoverElement = $j(this).data('bs.popover').tip();
        var popoverWasVisible = popoverElement.is(':visible');

        if (popoverWasVisible) {
          $j(this).popover('hide');
          $j(this).click();
        }
      }
    });
  });

  shareClose = function(video_id) {

    $j('[data-original-title]').each(function(e) {
      //the 'is' for buttons that trigger popups
      //the 'has' for icons within a button that triggers a popup
      if (!$j(this).is(e.target) && $j(this).has(e.target).length === 0 && $j('.popover').has(e.target).length === 0) {
        var popoverElement = $j(this).data('bs.popover').tip();
        var popoverWasVisible = popoverElement.is(':visible');

        if (popoverWasVisible) {
          $j("#share_overlay" + video_id).removeClass("popupdisplay");
          $j(".overlayview").css("display", "none");
          $j(".skigit_play img").css("display", "block");
          $j(this).popover('hide');
          $j(this).click();
        }
      }
    });
  };

  logoclick = function(logo_id, url) {
    var message;
    $j.ajax({
      url: "/invoice/business-logo/",
      type: "POST",
      data: { 'logo_id': logo_id },
      success: function(data) {
        if (data.is_success) {
          window.location.href = url
        } else {
          message = data.message;
        }
      }
    });
  };

  learnMoreClick = function(login_id, skigit_id, url) {
    var message;
    $j.ajax({
      url: "/invoice/learn-more/",
      type: "POST",
      data: {
        'login_id': login_id,
        'skigit_id': skigit_id
      },
      success: function(data) {
        if (data.is_success) {
          window.open(url, '_blank');
        } else {
          message = data.message;
        }
      }
    });
  };

  plugInClick = function(skigit_id, url) {
    var message;
    $j.ajax({
      url: "/invoice/plugin-click/",
      type: "POST",
      data: { 'skigit_id': skigit_id },
      success: function(data) {
        if (data.is_success) {
          window.location.href = url
        } else {
          message = data.message;
        }
      }
    });
  };

  $j("#generalNPopover").popover({
    html: true,
    title: "Skigit Notifications",
    placement: "bottom",
    content: $j('#notifyContaint').html()
  });

  $j('#bug_report').on("click", function() {
    $j('#bugModal').modal('show');
  });

  $j('#id_bug_submit').click(function() {

    if ($j('#bug_description').val() != '' && $j("input[type='radio'][name=repeat]:checked").val() != undefined) {
      var data = {
        'skigit_id': $j('#id_bug_skigit').val(),
        'skigit_title': $j('#id_bug_skigit_title').val(),
        'bug_url': $j('#id_bug_page_url').val(),
        'bug_title': $j('#id_bug_title').val(),
        'bug_desc': $j('#bug_description').val(),
        'bug_repeated': $j("input[type='radio'][name=repeat]:checked").val()
      }
      $j('#id_bug_submit').attr("disabled", "disabled");
      $j('#id_bug_close').attr("disabled", "disabled");
      $j("#bug_msg").html('...').css('color', 'orange');
      $j.ajax({
        url: "/bug-management/",
        type: "POST",
        data: data,
        success: function(responce_data) {
          $j('#bug_report_form')[0].reset();
          $j("#bug_msg").html(responce_data.message).css('color', '#b1fab7');
          $j('#id_bug_submit').removeAttr('disabled');
          $j('#id_bug_close').removeAttr('disabled');
        }
      });
    } else {
      $j('#id_bug_submit').removeAttr('disabled');
      $j('#id_bug_close').removeAttr('disabled');
      if (($j("input[type='radio'][name=repeat]:checked").val() == '' ||
        $j("input[type='radio'][name=repeat]:checked").val() == undefined ) && $j('#bug_description').val() == '') {
        $j("#bug_msg").html("<span style='font-size:14px; color : #ffffff; font-family: laoui sans, sans-serif; text-align: center;'><img src='/static/images/error_icon.png' width='25'>Please enter a bug description </span><span>and select an option</span>")
      }
      else if ($j("#bug_description").val() == '') {
        $j("#bug_msg").html(" <span style='color : #ffffff; font-size : 14px; font-style:italic; text-align: center;'><img src='/static/images/error_icon.png' width='25'>Please enter a bug description </span><span>and select an option</span>").css({"color" : "#ffa3a3", "font-size" : "14px"});
      }
      else if (($j("input[type='radio'][name=repeat]:checked").val() == '' ||
        $j("input[type='radio'][name=repeat]:checked").val() == undefined )) {
        $j("#bug_msg").html("<img width='25' src='/static/images/error_icon.png'>Please select an option</span>").css({"color" : "#ffffff", "font-size" : "14px", "text-align" : "center"});
      }
      else {
        $j("#bug_msg").html("<img width='25' src='/static/images/error_icon.png'>Please select an option</span>").css({"color" : "#ffa3a3", "font-size" : "14px", "text-align" : "center"});
      }
    }

   /* setTimeout(function() {
      $j("#bug_msg > * ").fadeOut('slow');
      $j("#bug_msg").empty();
    }, 25000);*/
  });

  bugSubmit = function(skigit) {
    if ($j.trim($j('#id_bug_description' + skigit).val()).length > 0 &&
      $j("input[type='radio'][name=repeat]:checked").val() != undefined) {
      var data = {
        'skigit_id': $j('#id_bug_skigit').val(),
        'bug_url': window.location.origin + '/skigit_data/' + $j('#id_bug_skigit').val() + '/',
        'bug_title': $j('#id_bug_title').val(),
        'bug_description': $j('#id_bug_description' + skigit).val(),
        'bug_repeated': $j("input[type='radio'][name=repeat]:checked").val()
      };
      $j('#id_bug_submit1').attr("disabled", "disabled");
      $j('#inapp_form_can').attr("disabled", "disabled");
      $j("#bug_msg" + skigit).html('...').css('color', 'orange');
      $j.ajax({
        url: "/bug-management/",
        type: "POST",
        data: data,
        success: function(responce_data) {
          if (responce_data.is_success) {
            $j('#bug_report_form' + skigit)[0].reset();
            $j("#bug_msg" + skigit).empty();
			
            /* $j('.msg_success').html('Thanks for making Skigit better!')
             $j('#id_bug_submit1').removeAttr('disabled')
             $j('#inapp_form_can').removeAttr('disabled')
             $j(".dropdown").removeClass('open');
             $j('.msg_success').show()
             setTimeout(openPopup, 2500);*/

            $j('#id_bug_submit1').removeAttr('disabled');
            $j('#inapp_form_can').removeAttr('disabled');
            $j("#bug_msg" + skigit).html("<span class='text-error' style='padding: 0 !important; margin-top: 4px;'><img width='25' src='/static/images/success_icon.png'>  Thanks for making Skigit better!</span>").css('color', '#c8f2d1  ', 'margin-left' , '70px' , 'font-family' , 'v');
            setTimeout(function () {
              $j('#id_bug_submit1').removeAttr('disabled');
              $j('#inapp_form_can').removeAttr('disabled');
              $j('#bug_report_form' + skigit)[0].reset();
              $j("#bug_msg" + skigit).empty();
              $j('.dropdown').removeClass('open');
            }, 2500);
          }
        }
      });
    } else {
      $j('#id_bug_submit1').removeAttr('disabled');
      $j('#inapp_form_can').removeAttr('disabled');
      if ($j.trim($j('#id_bug_description' + skigit).val()).length <= 0) {
        $j("#bug_msg" + skigit).html("<span class='text-error' style='padding: 0 !important; margin-top: 4px;text-align: center;'><img width='25' src='/static/images/error_icon.png'> Please enter a bug description. </span><span>and select an option</span>").css({"color" : "#ffa3a3", "font-family" : "laoui sans, sans-serif" , "font-size" : "14px"});
      }
      else {
        $j("#bug_msg" + skigit).html("<span class='text-error' style='padding: 0 !important; margin-top: 4px;'><img width='25' src='/static/images/error_icon.png'>Please select an option</span>").css({"color" : "#ffa3a3", "font-family" : "Laoui sans, sans-serif" , "font-size" : "12px" , "text-align" : "center"});
      }
     /* setTimeout(function () {
        $j('#id_bug_submit1').removeAttr('disabled');
        $j('#inapp_form_can').removeAttr('disabled');
        //$j('#bug_report_form'+skigit)[0].reset()
        $j("#bug_msg" + skigit).empty()
      }, 25000);*/
    }
  };

  bugCancel = function(skigit) {
    $j(".dropdown").removeClass('open');
    $j('#id_bug_submit1').removeAttr('disabled');
    $j('#inapp_form_can').removeAttr('disabled');
    $j('#bug_report_form' + skigit)[0].reset();
    $j("#bug_msg" + skigit).empty()
  };

  flagSubmit = function(skigit) {
    input_tag = $j("input:radio[name=skigit_reasons]:checked");
    skigit_reasons = input_tag.attr("skigit_reasons");
    skigit_id = input_tag.attr("skigit_id");
    data = $j("#inapp_form").serialize();

    if ($j("input[name='skigit_reasons']:checked").val()) {
      $j('#flag_msg' + skigit).empty();
      $j('#flag_msg' + skigit).html('...').css('color', 'orange');
      $j('#inapp_form_sub').attr("disabled", "disabled");
      $j('#inapp_flag_can').attr("disabled", "disabled");
      $j.post("/skigit_inapp_reason/", {
        skigit_reasons: skigit_reasons,
        skigit_id: skigit_id
      }, function(data, status) {
        if (data.is_success) {
          /*$j('#inapp_form'+skigit)[0].reset()
           $j(".dropdown").removeClass('open');
           $j('#inapp_form_sub').removeAttr('disabled');
           $j('#inapp_flag_can').removeAttr('disabled');
           $j('#flag_msg'+skigit).empty()
           $j('.msg_success').html("<span class='sign1-error'><i class='glyphicon glyphicon-ok-circle ok1-pos'/></span><span class='text1-error'> Your request will be reviewed!</span>").css('color','#b1fab7');
           $j('.msg_success').show()
           setTimeout(openPopup, 2500);*/

          $j('#inapp_form_sub').removeAttr('disabled');
          $j('#inapp_flag_can').removeAttr('disabled');
          $j('#flag_msg' + skigit).empty();
          $j('#flag_msg' + skigit).html("<img width='25' src='/static/images/success_icon.png'><span class='text1-error'>  Thank you. Your request will be reviewed!</span>").css({"color" : "#b1fab7", "font-family" : "Laoui sans, sans-serif", "font-size" : "14px"});
          $j('#flag_msg' + skigit).html("<img width='25' src='/static/images/success_icon.png'><span class='text1-error'>  Your request will be reviewed!</span>").css({"color" : "#b1fab7", "font-family" : "Laoui sans, sans-serif", "font-size" : "14px"});

         setTimeout(function() {
            $j('#inapp_form' + skigit)[0].reset();
            $j("#flag_msg" + skigit).empty();
            $j('.dropdown').removeClass('open');
          }, 2000);
        } else {
          $j('#inapp_form_sub').removeAttr('disabled');
          $j('#inapp_flag_can').removeAttr('disabled');
          $j('#flag_msg' + skigit).empty()
        } 
      });
    } else {
      $j('#inapp_form_sub').removeAttr('disabled');
      $j('#inapp_flag_can').removeAttr('disabled');
      $j('#flag_msg' + skigit).empty();
      $j('#flag_msg' + skigit).html("<img width='25' src='/static/images/error_icon.png'><span class='text1-error'> Please mark an appropriate reason.</span>").css({"color" : "#ffa3a3", "font-family" : "Laoui sans, sans-serif", "font-size" : "14px"});

      /*setTimeout(function() {
        $j('#inapp_form' + skigit)[0].reset();
        $j("#flag_msg" + skigit).empty()
      }, 2000);*/
    }
  };


  flagCancel = function(skigit) {
    $j(".dropdown").removeClass('open');
    $j(".dropdown").removeClass('show');
    $j('#inapp_form' + skigit)[0].reset();
    $j("#flag_msg" + skigit).empty()
  };

  $j('#bug_description').on('keydown', function() {
    $j("#bug_msg").empty();
  });

  $j('#id_bug_close').click(function() {
    $j('#bug_report_form')[0].reset()
  });

  $j('#bugModal').on('hidden.bs.modal', function() {
    $j('#bug_report_form')[0].reset()
  });

  openMessage = function() {
    // $j(".modal-content").html("");
    // $j('#smallModal').css('top', '35');
    // $j('.modal').css('top', '35');
    // $j('.modal-content').css('border', 'none');
    $j('.notify_join_msg').find('div').css('top', '');
    $j('.notify_join_msg').find('div').css('top', '0');
    $j('.notify_join_msg').show();

    // $j('.notify_msg_div').append("<div style='top: 0px; z-index:99999;'  class='info message f_type'>" +
    //     "<h3 style='font-family: segoe_print !important;'>" +
    //     "You  must be a Skigit member to access this feature. <a style='color:#fff !important;" +
    //     " text-decoration:underline !important' ng-click='openLogin()'>Join Today!</a></h3></div>");
    setTimeout(function() {
      $j('.notify_join_msg').find('div').animate({ 'top': "-=52px" }, 1200);
    }, 5000);
    setTimeout(function() {
      $j('.notify_join_msg').hide();
    }, 6000);
  };

  get_date = function(video_id) {
    var currentTimezone = jstz.determine();
    var timezone = currentTimezone.name();
    $j.ajax({
      url: "/friends/share-skigit-date/",
      type: "POST",
      data: {
        'video_id': video_id,
        'time_zone': timezone,
        csrfmiddlewaretoken: getCookie('csrftoken')
      },
      success: function(result) {
        if (result.is_success) {
          for (var i = 0; i < (result.share_data).length; i++) {
            $j('#id_date_label' + video_id + result.share_data[i]['id']).text(result.share_data[i]['share_date'])
          }
        }
      }
    });
  };

  acceptFriendNotification = function(user_id) {
    // To view general profile in friends page for Business users!
    view_general_profile = '';
    if (VIEW_GENERAL_PROFILE == 'yes') {
      var view_general_profile = '?view-general=yes';
    }
    var user = user_id;
    $j.ajax({
      url: "/friends/friends-request-approve/",
      type: "POST",
      data: {
        'to_user': user_id,
        csrfmiddlewaretoken: getCookie('csrftoken')
      },
      success: function(data) {
        $j('#friend_li' + user).remove();
        if (data.result) {
          $j('#friend_li' + user).remove();
          $j('li').find('#friend_li' + user).remove();
          $j('#id_internal_friens' + user).attr('style', 'color:gray; font-size:large');
          $j('button[id^="id_invite_btn' + user + '"]').attr('disabled', true, 'title', 'Friend Request Accepted');

          var friend_box = '<div class="box_friend" data-skigt="' + user_id + '"><div class="box_imgcontain">' +
            '<div class="name_friend"><span class="heade_friend">' + data.username + '</span>' +
            '<span class="sub_namefriend">' + data.name + '</span><span class="friend_followers">' +
            'Followers :&nbsp;' + data.count + '</span></div><a href="/profile/' + data.username + '/' + view_general_profile + '"><div class="img_friend">' +
            '<img alt="skigit" src="' + data.image + '"></div></a><div class="icon_friend">' +
            '<a onclick="un_follow_follow(' + user_id + ')" id="follow_' + user_id + '"class = "unfollow"' +
            'data-cuid = "' + user_id + '" title = "Follow" style = "color: #58D68D; font-weight: 400;">' +
            '<span class="box_footer" id ="follow_btn' + user_id + '" style = "color: #cde7fd; font-weight: 400;"> Click to Follow </span></a>' +
            //'<img width="30" height="30" src='/static/images/error_icon.png' onclick="removeFriend(' + user_id + ')" class="close-friend"></div></div></div>'

           ' <img width="25" height="25" src="/static/images/error.png"   onclick="removeFriend(' + user_id + ')" class="close-friend"></div></div></div>'

          $j('#friendcontent').append(friend_box);

          if ($j('#friend_badge').text() > 1) {

            $j('#friend_badge').html($j('#friend_badge').text() - 1)

          } else {
            $j('#friend_badge').hide();
            var li = '<li class="f_type" style="color:#ffd6d4 ; font-size: smaller; text-align: center;font-family: segoe print;margin-left:-50px"> There are no pending Notifications.</li>'
            $j('#frnd_notification').append(li)
          }
        }
      }
    });
  };

  rejectFriendNotification = function(user_id) {
    $j.ajax({
      url: "/friends/friends-request-rejected/",
      type: "POST",
      data: {
        'to_user': user_id,
        csrfmiddlewaretoken: getCookie('csrftoken')
      },
      success: function(data) {
        if (data.result) {
          $j('#friend_li' + user_id).remove();
          $j('li').find('#friend_li' + user_id).remove();
          $j('button[id^="id_accept_btn' + user_id + '"]').remove();
          $j('button[id^="id_declain_btn' + user_id + '"]').remove();
          var html = '<button id="id_invite_btn' + user_id + '" style="float:right" onclick="inviteFriends(' + user_id + ')"><span style="font-size:large;" title="invite" id="id_internal_friens' + user_id + '" class="glyphicon glyphicon-user">&#43;</span></button>'
          $j('#button_sapn' + user_id).html(html);

          if ($j('#friend_badge').text() > 1) {
            $j('#friend_badge').html($j('#friend_badge').text() - 1)
          } else {
            $j('#friend_badge').hide();
            var li = '<li class="f_type" style="color:#bbb9b9; font-size: smaller; text-align: center;">There are no pending Friend Invites.</li>'
            $j('#frnd_notification').append(li)
          }
        }

      }
    });
  };

  notificationCount = function() {
    $j.ajax({
      url: "/friends/friend-count-notification/",
      type: "GET",
      success: function(data) {
        if (data.result) {
          if (data.count > 0) {
            $j('#friend_badge').show();
            $j('#friend_badge').html(data.count)
          } else {
            $j('#friend_badge').hide()
          }
        }
      }
    });
  };

  rmNotify = function(msg_typ, to_user, from_user, skigit_id, e) {
    $j.ajax({
      url: "/friends/notification-delete/",
      type: "POST",
      data: {
        'msg_type': msg_typ,
        'to_user': to_user,
        'from_user': from_user,
        'skigit_id': skigit_id,
        csrfmiddlewaretoken: getCookie('csrftoken')
      },
      success: function(data) {
        if (data.is_success) {
          // remove the notification immediately
          $j(e).parents('li.list-group-item').remove();

          // check if no more notification left then show default text
          if (!$j(e).parents('ul.notification_ul').children().length) {
            var li = '<li class="f_type" style="color:#bbb9b9; font-size: smaller; text-align: center;">There is no pending Notifications.</li>'
            $j(e).parents('ul.notification_ul').html(li);
          }
          if (skigit_id == null) {
            $j('#notify_li_' + msg_typ + '_' + to_user + '_' + from_user).slideUp('slow');
          } else {
            $j('#notify_li_' + msg_typ + '_' + to_user + '_' + from_user + '_' + skigit_id).slideUp('slow');
          }
        }
      }
    })
  };

  get_notify = function() {
    var currentTimezone = jstz.determine();
    var timezone = currentTimezone.name();
    $j.ajax({
      url: "/friends/notification-ski/",
      type: "POST",
      data: { 'time_zone': timezone, csrfmiddlewaretoken: getCookie('csrftoken') },
      success: function(data) {

        if (data.is_success) {
          if (data.notify_list.length > 0) {
            $j('#notify_ul').empty();
            for (var n = 0; n < data.notify_list.length; n++) {
              var li = '';

              if (data.notify_list[n].msg_type == 'like') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >';

                li += '<span class="notify_date" style="float:right; margin-top: -60;">';
                li += data.notify_list[n].date;
                //li += '<img src="static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">';
				
				 li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">';
				 
				 
                li += '</span>';

                //li += '<p class="content_notificationheaderfont"><img src="static/images/heart_liked.png" style="margin-right:12px;width:30px; display:none"> Congratulations!</p>'
				
				 li += '<p class="content_notificationheaderfont"><img src="/static/images/heart_liked.png" style="margin-right:12px;width:30px; display:none"> Congratulations!</p>'
				 
				 
				 
                li += '<div class="content_notificationnewpost"> <a href="/profile/';
                li += data.notify_list[n].from_username;
                li += '" target="_blank" style="color:#f6ee7a">';
                li += data.notify_list[n].from_username;
                li += '</a>';
                li += ' likes your skigit</label> ';
                li += ' <p class="f_type" style="color:#b2e0ff"> ';
                li += '<a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">';
                li += data.notify_list[n].vid_title;
                li += '</a></p></div>';

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'plug') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -20%;">'
                li += data.notify_list[n].date
                //li += '<img src="static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
				li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
                li += '</span>'


               // li += '<p class="content_notificationheaderfont"><img src="static/images/notify_plugin.png" style="margin-right:-18px;width: 70px; margin-left:-7px;display:none" /> Congratulations!</p>'
				
				 li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_plugin.png" style="margin-right:-18px;width: 70px; margin-left:-7px;display:none" /> Congratulations!</p>'
				 
				 
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' has plugged into your skigit '
                li += ' <p class="f_type" style="color:#b2e0ff"> '
                li += '<a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                li += data.notify_list[n].vid_title
                li += '</a></p></div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'plug-plug') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -100;">'
                li += data.notify_list[n].date
                //li += '<img src="static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
				li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
				
                li += '</span>'

                //li += '<p class="content_notificationheaderfont" id="notify_plugin_plus"><img src="static/images/notify_pluginplus.png" style="margin-left: -8px;width: 55px;display:none" /> Coincidence? I think not!</p>'
				
				li += '<p class="content_notificationheaderfont" id="notify_plugin_plus"><img src="/static/images/notify_pluginplus.png" style="margin-left: -8px;width: 55px;display:none" /> Coincidence? I think not!</p>'
				
				
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' has plugged into a Skigit that you plugged into'
                li += ' <span class="f_type" style="color:#b2e0ff"> '
                li += '<a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                li += data.notify_list[n].vid_title
                li += '</a></span></div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'friends') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" class="notify_date" style="float:right; margin-top: -54px;">'
                li += data.notify_list[n].date
               // li += '<img src="static/images/error.png"   class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
				  li += '<img src="/static/images/error.png"   class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				  
				  
                li += '</span>'

               // li += '<p class="content_notificationheaderfont"><img src="static/images/notify_follow_img.png" style="margin-right:8px;width:40px;display:none" /> Wanna new friend?</p>'
				 li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_follow_img.png" style="margin-right:8px;width:40px;display:none" /> Wanna new friend?</p>'
				 
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' wants to be friends with you.</div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'friends_accepted') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -35;">'
                li += data.notify_list[n].date
                //li += '<img src="static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
				li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
				
				
                li += '</span>'

               // li += '<p class="content_notificationheaderfont"><img src="static/images/friends_accept.png" style="margin-right:8px;width:40px;margin-bottom: 5px;display:none"/> Sure, let’s be friends!</p>'
				 li += '<p class="content_notificationheaderfont"><img src="/static/images/friends_accept.png" style="margin-right:8px;width:40px;margin-bottom: 5px;display:none"/> Sure, let’s be friends!</p>'
				 
				 
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' has accepted your friend request.</div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'un_plug') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -86px;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="17" height="17">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/unplug_notify.png" style="margin-right: 4px; width:40px;display:none" /> We’re sorry.. your got  unplugged.</p>'
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a> unplugged from your skigit'
                li += ' <span class="f_type" style="color:#b2e0ff"> '
                li += '<a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                li += data.notify_list[n].vid_title
                li += '</a></span></div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'new_post') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -56px;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="17" height="17">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_new.png" style="margin-right:4px;width:50px;margin-left: -7px;margin-top: -10px;display:none" /> Congratulations!</p>'
                li += '<p class="content_notificationnewpost" > Your Skigit '
                li += ' <a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                li += data.notify_list[n].vid_title
                li += '</a>&nbsp;has been posted to Skigit!</p> '
                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'video_uploaded') {
                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -56px;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="17" height="17">'
                li += '</span>'

               li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_new.png" style="margin-right:4px;width:50px;margin-left: -7px;margin-top: -10px;display:none" /> Video uploaded!</p>'
                li += '<p class="content_notificationnewpost" >Your Skigit named '
                li += '<a style="color:#d1fdcf" + >'
				li +=data.notify_list[n].vid_title 
                li += '</a> has been uploaded! You will be notified when it\'s posted</p> '			
                li += '</li>'
	
	
              } else if (data.notify_list[n].msg_type == 'video_not_uploaded') {
                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -56px;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="17" height="17">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_unapproved.png" style="margin-right:4px;display:none" /> Video not uploaded!</p>'
                li += '<p class="content_notificationnewpost" >Your Skigit was not uploaded! Please try again</p>'

                li += '</li>'

              }
              else if (data.notify_list[n].msg_type == 'new_post_follow') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -56px;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id+ ', this)"  width="17" height="17">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_follow_post.png" style="margin-left:-2px;width:60px;margin-top:-10px ;display:none"/> You&#39;re Following this Post! </p>'
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a> has  posted a new skigit '
                li += ' <a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                li += data.notify_list[n].vid_title
                li += '</a>'

                li += '</li>'

              }
              else if (data.notify_list[n].msg_type == 'follow') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -60;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_follow_img.png" style="margin-right:8px;width:40px;display:none" /> Congratulations!</p>'
                li += '<div class="content_notificationnewpost"> User <a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' started following you. </div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'unfollow') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -60;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_follow_img.png" style="margin-right:8px;width:40px;display:none" /> We’re sorry..</p>'
                li += '<div class="content_notificationnewpost"> User <a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' stopped following you. </div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'unapproved') {

                $j('#nf_loader').show();

                li += '<li  class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -56px;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="17" height="17">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><style="margin-right:4px;" /> We\'' + 're sorry...</p>';
                li += '<p class="content_notificationnewpost" > Your Skigit '
                li += '<a style="color:#fbaeae" + >'
				li += data.notify_list[n].vid_title
                li += '</a>&nbsp;has been rejected for posting.</p> '
                li += '</li>'
				
				/*
				li += '<p class="content_notificationheaderfont"><img src="static/images/notify_new.png" style="margin-right:4px;width:50px;margin-left: -7px;margin-top: -10px;display:none" /> Video uploaded!</p>'
                li += '<p class="content_notificationnewpost" >Your Skigit named '
                li += '<a style="color:#d1fdcf" + >'
				li +=data.notify_list[n].vid_title 
                li += '</a> has been uploaded! You will be notified when it\'s posted</p> '			
                li += '</li>'
				*/

              } else if (data.notify_list[n].msg_type == 'share') {

                $j('#nf_loader').show();

                li += '<li class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                li += '<span class="notify_date" style="float:right; margin-top: -100;">'
                li += data.notify_list[n].date
                li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
                li += '</span>'

                li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_radar.png" style="display:none">You&#39;re on the Radar!</p>'
                li += '<div class="content_notificationnewpost"><a href="/profile/'
                li += data.notify_list[n].from_username
                li += '" target="_blank" style="color:#f6ee7a ">'
                li += data.notify_list[n].from_username
                li += '</a>'
                li += ' has shared the awesome Skigit'
                li += '<p> <span class="f_type" style="color:#b2e0ff"> '
                li += '<a style="color:#b2e0ff" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                li += data.notify_list[n].vid_title
                li += '</a></span>  with you !</p></div>'

                li += '</li>'

              } else if (data.notify_list[n].msg_type == 'plug_primary') {

                $j('#nf_loader').show();
                if (data.notify_list[n].parent_title) {

                  li += '<li class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                  li += data.notify_list[n].parent_title
                  li += '</a></span> .</div>'
                  li += '<span class="notify_date" style="float:right; margin-top: -100;">'
                  li += data.notify_list[n].date
                  li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
                  li += '</span>'

                  li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_primary_delete.png" style="margin-right:4px;display:none" /> The Primary skigit</p>'
                  li += '<div class="content_notificationewpost"><span class="f_type" style="color:#f6ee7a"> '
                  li += data.notify_list[n].vid_title
                  li += '</span> was deleted. You&#39;re now connected to the next Plug-in in line '
                  li += '<span class="f_type" style="color:#f6ee7a">'
                  li += '<a style="color:#f6ee7a" target="_blank" href="/skigit_data/' + data.notify_list[n].parent_skigi_id + '/">'

                  li += '</li>'
                } else if (data.notify_list[n].child_title) {
                  li += '<li class="list-group-item f_type notifylist_li comefromtop" id="notify_li_' + data.notify_list[n].msg_type + '_' + data.notify_list[n].user + '_' + data.notify_list[n].from_user + '_' + data.notify_list[n].skigit_id + '" >'

                  li += '<span class="notify_date" style="float:right; margin-top: -100;">'
                  li += data.notify_list[n].date
                  li += '<img src="/static/images/error.png" class="notify_remove" onclick="rmNotify(\'' + data.notify_list[n].msg_type + '\',' + data.notify_list[n].user + ',' + data.notify_list[n].from_user + ',' + data.notify_list[n].skigit_id + ', this)"  width="20" height="20">'
                  li += '</span>'

                  li += '<p class="content_notificationheaderfont"><img src="/static/images/notify_primary_delete.png" style="margin-right:4px;display:none" /> The Primary skigit</p>'
                  li += '<div class="content_notificationnewpost"><span class="f_type" style="color:#f6ee7a">'
                  li += '<a style="color:#f6ee7a" target="_blank" href="/skigit_data/' + data.notify_list[n].play_back_id + '/">'
                  li += data.notify_list[n].vid_title
                  li += '</a></span> was deleted. You&#39;re now connected to the next Plug- in in line'
                  li += '<span class="f_type" style="color:#f6ee7a">'
                  li += '<a style="color:#f6ee7a" target="_blank" href="/skigit_data/' + data.notify_list[n].child_skigi_id + '/">'
                  li += data.notify_list[n].child_title
                  li += '</a></span>.</div>'

                  li += '</li>'
                }
              }

              $j('#nf_loader').hide();
              $j('#notify_ul').prepend($j('#notify_ul').append(li)).addClass('pushdown');
              setTimeout(function() {
                $j('#Trees').removeClass('pushdown');
              }, 600);
            }

          }
        }
        $j('#general_badge').hide();
        $j('#general_badge').text(0)
      }
    });
  };

  function refresh_global_notification() {
    $j.ajax({
      url: "/get_notification_count/",
      success: function(data) {
        if (data.count > 0) {
          $j('#general_badge').show();
          $j('#general_badge').text(data.count);
        } else {
          $j('#general_badge').hide();
          $j('#general_badge').text(0);
        }
      }
    });
    setTimeout(refresh_global_notification, 10000);
  }

  function refresh_friend_notification() {
    $j.ajax({
      url: "/friends/friend-count-notification/",
      type: "GET",
      success: function(data) {
        if (data.result) {
          if (data.count > 0) {
            $j('#friend_badge').show();
            $j('#friend_badge').text(data.count)
          } else {
            $j('#friend_badge').hide()
          }
        }
      }

    });
    setTimeout(refresh_friend_notification, 10000);
  }


  refresh_global_notification();
  refresh_friend_notification();

  friendsNotificaton = function(e) {

    $j.ajax({
      url: "/friends/friend-notification/",
      type: "GET",
      success: function(data) {
        $j('#frnd_notification').empty();

        if (data.result) {
          if (data.friend_list.length > 0) {

            $j('#friend_badge').show();
            $j('#friend_badge').html(data.friend_list.length);

            for (var f = 0; f < data.friend_list.length; f++) {
              if (data.friend_list[f].profile_img) {
                var l_img = data.friend_list[f].profile_img
              } else {
                l_img = '/static/images/noimage_user.png'
              }
              var li = '<li class="list-group-item comefromtop" id="friend_li' + data.friend_list[f].to_user + '" >' +
                '<img class="avatar" style="object-fit: cover;" src="' + l_img + '"/>' +
                '<label class="f_type" >' + '<p id="friend_name" > ' + data.friend_list[f].name + '</p>' + '<p id="friend_slogan" >wants to be friends with you</p></label> ' +
                '<span class="btn_span" id="button_sapn' + data.friend_list[f].to_user + '">' +
                '<p id="id_accept_btn' + data.friend_list[f].to_user + '" data-friend="" style="float:right; background: none !important; width: auto !important; height: auto !important; margin-right: 0px;" onclick="acceptFriendNotification(' + data.friend_list[f].to_user + ')" > ' +
                '<span title="Accept Request" id="id_accept_friens" class="glyphicon glyphicon-ok-circle"></span></p>' +
                '<p id="id_declain_btn' + data.friend_list[f].to_user + '" style="float:right; background: none !important; width: auto !important; height: auto !important; margin-right: 0px; padding-right: 0px; padding-left: 0px;" onclick="rejectFriendNotification(' + data.friend_list[f].to_user + ')">' +
                '<span  title="Reject Request" id="id_reject_friens" class="glyphicon glyphicon-remove-circle">' +
                '</span></p></span></li>'
              $j('#frnd_notification').append(li)
            }
          } else {
            var li = '<li class="f_type" style="color:#ffffff; font-size: smaller; text-align: center;">There are no pending Notifications.</li>'
            $j('#frnd_notification').empty();
            // $j('#frnd_notification').append(li);
            $j('#friend_badge').hide()
          }
        }
      }
    });
  };

  like_unlike_entry = function(like_class, like_id) {
    var skigit_id = like_id;
    var post_clas = $j("#" + like_class).attr('class');
    var post_id = like_class;
    var like_count = $j.trim($j('#like_count' + like_id).text());


    if (post_clas == 'unlike') {
      $j.ajax({
        type: "POST",
        url: "/skigit_i_like/",
        data: {
          'skigit_id': skigit_id,
          'csrfmiddlewaretoken': getCookie('csrftoken')
        },
        success: function(response) {
          if (response.is_success) {
            if (response.like == 1 || response.like == '1') {
              $j("#" + post_id).attr("title", "Unlike");
              $j("#" + post_id).removeClass("unlike");
              $j("#" + post_id).addClass("like");
			  // Skigit thumbnail control
             // $j("#" + post_id + "> img").attr("src", "static/images/heart_liked.png");
			    $j("#" + post_id + "> img").attr("src", "/static/images/heart_liked_thumb.png");
              $j('#like_count' + like_id).text(parseInt(like_count) + 1)
            }
          }
        },
        error: function(rs, e) {
          $j("#popup_msg").text("Error with liking the Skigit...! Please try again");
          $j("#popScreen").show();
        }
      });
    } else if (post_clas == 'like') {
      $j.ajax({
        type: "POST",
        url: "/skigit_i_unlike/",
        data: {
          'skigit_id': skigit_id,
          'csrfmiddlewaretoken': getCookie('csrftoken')
        },
		
			/*--- Controls thumbnaill Like----------------------->*/
			
        success: function(response) {
          if (response.is_success) {
            if (response.unlike == 1 || response.unlike == '1') {
              $j("#" + post_id).attr("title", "Like");
              $j("#" + post_id).removeClass("like");
              $j("#" + post_id).addClass("unlike");
              $j("#" + post_id + "> img").attr("src", "/static/images/heart_unliked_thumb.png");
              $j('#like_count' + like_id).text(parseInt(like_count) - 1)
            }
          }
        },
        error: function(rs, e) {
          $j("#popup_msg").text("Error Liking this Skigit...! Please try again");
          $j("#popScreen").show();
        }
      });
    }
  };

  // like_unlike_entry_2 - like/unlike for skigit popoup pge - created for blue heart icon =unlike

  like_unlike_entry_2 = function(like_class, like_id, video_detail_id) {
    var skigit_id = like_id;
    var post_clas = $j("#" + like_class).attr('class');
    var post_id = like_class;
    var like_count = $j.trim($j('#like_count' + like_id).text());


    if (post_clas == 'unlike') {
      $j.ajax({
        type: "POST",
        url: "/skigit_i_like/",
        data: {
          'skigit_id': skigit_id,
          'csrfmiddlewaretoken': getCookie('csrftoken')
        },
        success: function(response) {
          if (response.is_success) {
            if (response.like == 1 || response.like == '1') {
              $j("#" + post_id).attr("title", "Unlike");
              $j("#" + post_id).removeClass("unlike");
              $j("#" + post_id).addClass("like");
			  // Skigit detail page  control
              //$j("#" + post_id + "> img").attr("src", "static/images/heart_liked.png");
			  $j("#" + post_id + "> img").attr("src", "/static/images/heart_liked.png");
              $j('#like_count' + like_id).text(parseInt(like_count) + 1)
            }
            get_skigit_statistics(video_detail_id) // update skigit stats
          }
        },
        error: function(rs, e) {
          $j("#popup_msg").text("Error Liking this Skigit...! Please try again");
          $j("#popScreen").show();
        }
      });
    } else if (post_clas == 'like') {
      $j.ajax({
        type: "POST",
        url: "/skigit_i_unlike/",
        data: {
          'skigit_id': skigit_id,
          'csrfmiddlewaretoken': getCookie('csrftoken')
        },
		
		/*--- Controls Skigit Popup Like----------------------->*/
		
        success: function(response) {
          if (response.is_success) {
            if (response.unlike == 1 || response.unlike == '1') {
              $j("#" + post_id).attr("title", "Like");
              $j("#" + post_id).removeClass("like");
              $j("#" + post_id).addClass("unlike");
              $j("#" + post_id + "> img").attr("src", "/static/images/heart_unliked.png");
              $j('#like_count' + like_id).text(parseInt(like_count) - 1)
            }
            skigit_statistics(video_detail_id) // update skigit stats
          }
        },
        error: function(rs, e) {
          $j("#popup_msg").text("Error Liking this Skigit...! Please try again");
          $j("#popScreen").show();
        }
      });
    }
  };

  function unique(array) {
    return $j.grep(array, function(el, index) {
      return index === $j.inArray(el, array);
    });
  }

  shareToFriends = function(skigit_id) {
    var share_value = [];
    var plug_count = $j.trim($j('#share_count' + skigit_id).text());

    $j("input[type=checkbox]:checked").each(function() {
      if ($j(this).is(':checked')) {
        share_value.push(parseInt($j(this).val()));
      }
    });

    if (share_value.length > 0) {
      $j('#button_share' + skigit_id).prop('disabled', true);
      $j('.button_share').prop('disabled', true);
      $j('#msg' + skigit_id).html('...').css('color', 'orange', 'text-aling', 'center');
      $j('.msg').html('...').css('color', 'orange', 'text-aling', 'center');
      var currentTimezone = jstz.determine();
      var timezone = currentTimezone.name();
      $j.ajax({
        type: "POST",
        url: "/share-skigits/",
        data: {
          'vid_id': skigit_id,
          'friend_list[]': unique(share_value),
          'time_zone': timezone,
          'csrfmiddlewaretoken': getCookie('csrftoken')
        },
        success: function(data) {
          if (data.is_success) {
            $j(':checkbox').each(function() {
              this.checked = false;
            });
            $j('#msg' + skigit_id).html('<img width="25" src="/static/images/success_icon.png">  Thanks for sharing!').css('color', '#b1fab7', 'margin', '20px 0px 0px 20px', 'width', ' 100%', 'text-align', 'center');
            $j('.msg').html('<img width="25" src="/static/images/success_icon.png">  Thanks for sharing!').css('color' , '#b1fab7', 'margin', '20px 0px 0px 20px', 'width', '100%', 'text-align', 'center');
            $j('#button_share' + skigit_id).prop('disabled', false);
            $j('.button_share').prop('disabled', false);
            $j('#share_count' + skigit_id).text(parseInt(plug_count) + parseInt(unique(share_value).length));
            $j('.share_count').text(parseInt(plug_count) + parseInt(unique(share_value).length));
            for (var k = 0; k < unique(share_value).length; k++) {
              $j('#id_date_label' + skigit_id + unique(share_value)[k]).text(data.date)
            }
            setTimeout(function() {
              $j('#msg' + skigit_id).empty()
              $j('.msg').empty()
            }, 3000)
            get_skigit_statistics(skigit_id) // update skigit stats
          }
        },
        error: function (rs, e) {
          $j('#msg' + skigit_id).html("An error occured when sharing the Skigit Index Page. Please try again");
          $j('#button_share' + skigit_id).prop('disabled', false);
        }
      });
    }
    else {
	    $j('#msg' + skigit_id).html('<img width="25"  src="/static/images/error_icon.png">Select Skigit friends in order to share this Skigit.').css({'color' : '#ffa3a3', 'font-size' : '14px' , 'margin' : '10px 0 0 0px' , 'width' : '100%'  , 'display' : 'inline-block', 'line-height' : '1.4', 'border-radius' : '20px' , 'padding' : '5px' });
		
      /*setTimeout(function () {
        $j('#msg' + skigit_id).empty()
      }, 2500);*/
	  
      $j('#button_share' + skigit_id).prop('disabled', false);
      $j('#button_share' + skigit_id).prop('disabled', false);
    }
  };

  sharebox = function(friend_id, video_id) {
    var share_id = $j('#sharebox' + video_id + friend_id).attr('id');
    var skigit_id = video_id;

    if ($j('#select_all' + video_id).is(':checked')) {
      $j('#select_all' + video_id).prop('checked', false)
    }
  };

});

// modal
$j('#skigit-modal').on('show.bs.modal', function(event) {
  var address = $j(event.relatedTarget);
  $j('#skigit-modal .modal-content').load(address.attr('href'), function() {});
});

$j("#skigit-modal").on("hidden.bs.modal", function() {
  $j("#skigit-modal .modal-content").html("");

  $j("meta[property='og:image:width'], meta[property='og:image:height'], meta[property='twitter:title'], meta[property='twitter:url'], meta[property='twitter:description']").remove();
  $j("meta[property='og:image'], meta[property='twitter:image'], meta[itemprop='image']").attr('content', META_SITE_LOGO_IMAGE);
  $j("meta[property='og:url']").attr('content', META_SITE_DOMAIN);
  $j("meta[property='twitter:domain']").attr('content', META_SITE_DOMAIN);
  $j("meta[property='og:title']").attr('content', META_SITE_TITLE);
  $j("meta[property='og:description']").attr('content', META_SITE_DESCRIPTION);
});

$j("#button").click(function(e) {
  e.preventDefault()
  let searchVal = $j('#searchBox').val()
  $j.ajax({

    url: "/sperk",
    data: { search: searchVal },
    success: function(result) {
      $j("#sperk").html(result);
    }
  });
});

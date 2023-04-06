f$(document).ready(function () {

  $("b.sperk-logo-n").click(function () {
    $("ul.sperk-logo").addClass('open');
    $(".p_body").css("display", "block");

  });

  $("span#close-button").click(function () {
    $("ul.sperk-logo").removeClass('open');
    $(".p_body").css("display", "none");

  });

  $(".p_body").click(function () {
    $("ul.sperk-logo").removeClass('open');
    $(".p_body").css("display", "none");
  });

  $("#target").click(function () {
    $(".target-div").addClass('open');
    $(".p_body").css("display", "block");

  });

  $(".p_body").click(function () {
    $(".target-div").removeClass('open');
    $(".p_body").css("display", "none");
  });

  $("#close").click(function () {
    $(".target-div").removeClass('open');
    $(".p_body").css("display", "none");
  });

  $('#clear_form').click(function () {
    $('#skigit_form1')[0].reset()
    if ($('#id_video_link').val() == '') {
      $('.fileUpload').show();
    }
    ;
    speark_logo()
  });

});

$(document).ready(function () {

  if ($('#id_made_by_option').change(function () {
        $("#id_made_by").attr("disabled", "disabled");
        $("#show-me").hide();
        $("#logos").hide();
        $('.sperk-content').empty()
        if ($('#id_made_by_option').val() !== '' && $('#id_made_by_option').val() !== ' ')
          if ($("input[type='radio'][name=add_logo]:checked").val() === '1' ||
              $("input[type='radio'][name=add_logo]:checked").val() === 1) {
            $('#id_sperk_label').hide()
            $('.sperk-content').append("<center><img src='/static/skigit/images/opps_no_logo.png' width='65px;' height='50px;'></center><p><b>Oops!</b> The logo for your awesome thing is not available at this time. " +
                "We recommend that you select <b>&#10077 YES &#10078</b> to display the logo so that it can be added to your" +
                " Skigit at a later date if the maker becomes a member of Skigit </p>");
            $("ul.sperk-logo").addClass('open');
            $(".p_body").css("display", "block");
          }
          else {
            $('.sperk-content').empty()
            $('#id_sperk_label').hide()
            $('.sperk-content').empty()
            $('.sperk-content').append("<h2 class='sorry f_type' style='color:#FF0004 !important;' >We're Sorry!</h2>");
            $('.sperk-content').append("<center><p> This maker is not offering any Skigit incentives at this time. Check back later! </p></center>");
          }
        else {
          $('#id_sperk_label').show()
          $("#show-me").hide();
          $("#logos").hide();
        }

      }));
});
$(document).ready(function () {

  $("#id_add_logo_1").click(function () {
    $("#show-me").hide();
    $("#logos").hide();
  });


  $("#id_receive_donate_sperk_1").click(function () {

    $("#target").show();
  });

  $("#id_receive_donate_sperk_0").click(function () {

    $("#target").hide();
    $('input[name="donateGroup"]').prop('checked', false);
  });


});
$(document).ready(function () {
  $('#id_video_link').init(function () {
    if ($('#id_video_link').val() == '') {

      $('.fileUpload').show();
    }
    ;

    if ($('#id_video_link').val() != '') {
      $('.fileUpload').hide();
    }
  });


  if ($('.dropzone').change(function () {
        $("#id_video_link").attr("disabled", "disabled");
      }));
  if ($('#id_video_link').change(function () {
        $('#fileUpload').hide();
      }))


    $('#video_form').bind('change', function () {

      file_size = this.files[0].size / 1048576
      if (file_size < 20) {

        if (this.files[0].type.split('/')[0] == 'video') {
          return true;
        }
        else {
          alert('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> File type must be video .mkv | .avi | .mp4 | .3gp | .wmv ')
          $('#video_form').get(0)
          return false;
        }
      }
      else if (file_size > 30) {
        alert('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Video must be less then 20MB or maximum 20MB')
        $('#video_form').get(0).clear
        return false;
      }
    });
});

var upperlinkvalue = $('#video_form').get(0);
var lowerlinkvalue = '{{form2.video_link}}';
function check() {
  if (document.getElementById('id_video_link').value == ""
      && document.getElementById('video_form').value == "") {
    alert("Please Select one.");
    return false;
  }
}

/*** Spice up your Skigit thumbnail by adding your item logo Ajax jquery function ***/
function speark_logo() {

  if ($('#id_made_by').val() != '') {
    $("#id_made_by_option").attr('disabled', 'disabled');
  }
  else {
    $("#id_made_by_option").removeAttr('disabled');
  }
  jQuery.ajax({
    url: "/get-sperk/",
    type: "POST",
    data: {
      'user_id': $('#id_made_by option:selected').val(),
      csrfmiddlewaretoken: '{{ csrf_token }}'
    },
    success: function (data) {
      $('.sperk-content p').remove();
      $('.sperk-content h2').remove();
      if ($('#id_made_by_option').val() !== '') {

        if ($("input[type='radio'][name=add_logo]:checked").val() === '1' ||
            $("input[type='radio'][name=add_logo]:checked").val() === 1) {
          $('#id_sperk_label').hide()
          $('.sperk-content').empty()
          $('.sperk-content').append("<center><img src='/static/skigit/images/opps_no_logo.png' width='65px;' height='50px;'></center><p><b>Oops!</b> The logo for your awesome thing is not available at this time. " +
              "We recommend that you select <b>&#10077 YES &#10078</b> to display the logo so that it can be added to your" +
              " Skigit at a later date if the maker becomes a member of Skigit </p>");
          $("ul.sperk-logo").addClass('open');
          $(".p_body").css("display", "block");
        }
        else {
          $('#id_sperk_label').hide()
          $('.sperk-content').empty()
          $('.sperk-content').append("<span class='glyphicon glyphicon-triangle-top'></span><center><img src='/static/skigit/images/sperk.png' width='65px;' height='50px;'></center><h2 class='sorry f_type' style='color:#FF0004 !important;' >We're Sorry!</h2>");
          $('.sperk-content').append("<center><p> This maker is not offering any Skigit incentives at this time. Check back later! </p></center>");

        }
        $("#show-me").hide();
        $("#logos").hide();
      }
      else {

        if (data.incentive_detail) {
          $('.sperk-content').empty()
          $('.sperk-content').append("<center><img src='/static/skigit/images/sperk_awesome_logo.png' width='65px;' height='50px;'></center><h2 class='f_type'>Awesome</h2>");
          $('.sperk-content').append("<center><p>" + data.incentive_detail + "</p></center>");

          if ($("input[type='radio'][name=add_logo]:checked").val() === '1' ||
              $("input[type='radio'][name=add_logo]:checked").val() === 1 && $('#id_made_by option:selected').val() !== '') {

            $("#show-me").show();
          }
          else {
            $("#show-me").hide();
            $('#logos').hide()
          }
        }
        else {
          $('.sperk-content').empty()
          $('.sperk-content').append("<span class='glyphicon glyphicon-triangle-top'></span><center><img src='/static/skigit/images/sperk.png' width='65px;' height='50px;'></center><h2 class='sorry f_type' style='color:#FF0004 !important;' >We're Sorry!</h2>");
          $('.sperk-content').append("<center><p> This maker is not offering any Skigit incentives at this time. Check back later! </p></center>");
          $("#show-me").hide();

        }
        $('.logo-url .dz-image').remove()
        $('.logo-url label').remove()
        $('.logo-url .dz-image').remove()
        $('#logos').empty()
        if ($("input[type='radio'][name=add_logo]:checked").val() === '1' ||
            $("input[type='radio'][name=add_logo]:checked").val() === 1 && $('#id_made_by option:selected').val() !== ' ') {

          $("#logos").show();

        }
        else {
          $("#show-me").hide();
          $('#logos').hide()
        }
        $('#id_sperk_label').show()
      }

      var imagesCollection = data.all_business_logo;
      if (imagesCollection) {
        for (var i = 0; i < imagesCollection.length; i++) {
          var idd = imagesCollection[i][0];
          if ((idd.length == 0)) {
            continue;
          }
          var image_div = ' <input type="radio"  id=' + idd + ' value=' + idd + ' name="select_logo" checked/>' + '<label for=' + idd + ' class="label"><div class="dz-image"> <img data-dz-thumbnail="" alt="skigit/logo/ebf7e1f9-5356-40cc-bb56-0bd0bbecfecc" src=' + imagesCollection[i][1] + '></div></label>'
          $('.logo-url').append(image_div);
        }
      }
      else {
        $('#logos').hide()
      }

    }
  });
}
$(document).ready(function () {
  if ($('#id_made_by option:selected').val() === '') {
    $("#show-me").hide();
    $('#logos').hide()
  }
  $('#id_made_by').on('change', function () {
    speark_logo()
  });

  $("#id_add_logo").click(function () {
    speark_logo()
  });
});


$(document).ready(function () {
  var form;
  form = $("#skigit_form1");
  $("#id_bought_at").on("keyup", function (e) {
    $(this).val().trim()
  });

  $("#id_video_link").on("keyup", function (e) {
    var str;
    str = $(this).val();
    str = str.replace(/\s/g, '');
    $(this).val(str);
  });

  $("#id_video_link").on("keyup", function (e) {
    var str;
    str = $(this).val();
    if (!(str == ' ' || str == '')) {
    } else {
      str = str.replace(/\s/g, '');
      $(this).val(str);
      $('#fileUploadform').show()
      $('#file_uplod_div').show()
      $('#file_uplode_note').show()
    }
  });

  $("#id_title, #id_made_by_option, #id_why_rocks").on("keyup", function (e) {
    var str;
    str = $(this).val().trim();
    if (!(str == ' ' || str == '')) {
    } else {
      str = str.replace(/\s/g, '');
      $(this).val(str);
    }
  });

  /*** Progress Bar ***/
  var val = 0;
  var progressLabel = $(".progress-label");
  var progressbar = $("#progressbar-5");

  function progress() {
    val = progressbar.progressbar("value") || 0;
    progressbar.progressbar("value", val + 1);
    if (val < 99) {
      setTimeout(progress, 100);
    }
  }

  $('#skigit_form1').bind('input', 'keydown', function () {
    if ($('#msg').text() == '✔ Your Skigit was successfully uploaded and is being processed. You will be notified when posted. Thanks for your patience!') {
      $('#msg').hide()
    }
  });

  $('input[name=add_logo]').change(function () {
    if ($("input[type='radio'][name='add_logo']:checked").val() !== '1') {
      $('#msg_donate').hide()
      $('#target').hide()
      $('input[name="donateGroup"]').prop('checked', false);
      $('input[type="radio"][name="receive_donate_sperk"][value="2"]').prop('checked', true);
    }
  });

  $("input[name=donateGroup],#id_add_logo_1").click(function () {
    $('#msg_donate').hide()
  });

  $("#id_receive_donate_sperk_1").click(function () {

    if ($("input[type='radio'][name=receive_donate_sperk]:checked").val() === '1') {
      if ($("input[type='radio'][name='donateGroup']:checked").val()) {
        $('#msg_donate').hide()
      }
      else {
        $('#msg_donate').empty()
        $('#msg_donate').show()
        $('#msg_donate').html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Please select target organization and chose Donation option').addClass('f_type');
      }
    }
  });

  $("#id_receive_donate_sperk_0").click(function () {
    $('#msg_donate').hide()
  });

  var progressLabel = $(".progress-label");
  $("#progressbar-5").progressbar({
    value: false,
    change: function () {
      progressLabel.text(
          progressbar.progressbar("value") + "%");
    },
    complete: function () {
      progressLabel.text("Uploading Completed");
      $('.box_fulllodar').hide();
      myDropzone.removeAllFiles();
      $("#msg").html("<span style='font-size:20px;'><i class='glyphicon glyphicon-ok-circle' style='top: 5px !important;' /></span> Your Skigit was successfully uploaded and is being processed. You will be notified when posted. Thanks for your patience!").css('color', 'green')
      $("#msg").addClass('f_type')
      $("#msg").show()
      clearrecord();
      setTimeout(function () {
            $("#msg").empty();
            $("#msg").hide();
          },
          5000)
    }
  });

  Dropzone.autoDiscover = false;
  myDropzone = new Dropzone("#myId", {
    url: '/youtube/direct-upload', maxFiles: 1, createImageThumbnails: true,
    uploadMultiple: false,
    paramName: "file_on_server",
    autoProcessQueue: false,
    previewsContainer: null,
    hiddenInputContainer: "body",
    addRemoveLinks: "true",
    thumbnailWidth: "250",
    thumbnailHeight: "250",
    maxFilesize: 20,
    acceptedFiles: 'video/*,.3gpp,.mp4,.WMV,.mpeg4,.wmv, .avi, .flv, .wbem, .mov, .wvx, .wm, .wmx, .3ggp2, .3gp, 3g2',
    dictDefaultMessage: "Drag Files here or Click to Upload",
    dictFallbackMessage: "Your browser does not support drag'n'drop file uploads.",
    dictFallbackText: "Please use the fallback form below to upload your files like in the olden days.",
    dictFileTooBig: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> File is too big. Max filesize:20MB.',
    dictInvalidFileType: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> You can\'t upload files of this type.',
    dictCancelUpload: "Cancel upload",
    dictCancelUploadConfirmation: "Are you sure you want to cancel this upload?",
    dictRemoveFile: "Remove",
    dictRemoveFileConfirmation: null,
    dictMaxFilesExceeded: "You can not upload any more files.",
    error: function (file, response) {
      $('.box_fulllodar').hide();
      if ($.type(response) === "string") {
        //dropzone sends it's own error messages in
        $('#msg').empty()
        $('#msg').html(response).css('color', 'red')
        $('#msg').show()
      }
      else {
        file.previewElement.classList.add("dz-error");
        _ref = file.previewElement.querySelectorAll("[data-dz-errormessage]");
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          node = _ref[_i];
          _results.push(node.textContent = response.message);
        }
        $('#msg').empty()
        $('#msg').html(_results).css('color', 'red')
        $('#msg').show()
        return _results;
      }
    }
  });

  function clearrecord() {
    $("#id_made_by_option").removeAttr('disabled');
    $("#id_made_by").removeAttr('disabled');
    $('#skigit_form1')[0].reset()
    $('#fileUploadform').show()
    $('#file_uplod_div').show()
    $('#file_uplode_note').show()
    $('#id_sperk_label').show()
    $('#target').hide()
    $('#id_video_link').val('')
    speark_logo()
  }

  function videolink_ajax(video_data) {
    $('.box_fulllodar').show()
    $.ajax({
      url: '/youtube/link-upload',
      type: "POST", // http method
      data: video_data, // data sent with the post request
      success: function (data) {
        if (data.is_success == true) {
          progressbar.progressbar("value", 0);
          setTimeout(progress, 100);
        }
        else {
          $('.box_fulllodar').hide()
          $("#msg").show()
          $("#msg").html(data.message).css('color', 'red')
        }
      },
      // handle a non-successful response
      error: function (xhr, errmsg, err) {
        //Error Messages
      }
    });
  }

  $('#vidsubmit').click(function () {

    form.validate({
      errorLabelContainer: '#errors',
      rules: {
        'title': {
          required: true,
          maxlength: 40
        },
        'category': {
          required: true
        },
        'subject_category': {
          required: true
        },
        'made_by': {
          required: true
        },
        'made_by_option': {
          required: false
        },
        'bought_at': {
          required: function (element) {
            return document.getElementById('id_made_by').value != "";
          },
        },
        'why_rocks': {
          required: true,
          maxlength: 200
        },
        'donateGroup': {
          required: true
        }
      },
      messages: {
        'title': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> My Skigit Title field is required',
          maxlength: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Enter at most 40 characters',
        },
        'category': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> My Skigit Category field is required',

        }, 'subject_category': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> My Subject Category field is required',

        }, 'made_by': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> My awesome thing was made by or add maker or proprietor name field is required <br>(You must either select a name from dropdown list or if the name doesnot exists <br>&nbsp; enter the appropriate name in the text entry box)',

        }, 'made_by_option': {
          required: ' '

        }, 'bought_at': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> I bought my awesome thing at * field is required',
        }, 'why_rocks': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Why my awesome thing rocks! field is required',
          maxlength: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Why my awesome thing rocks! field has limit of max 200 characters.'
        },
        'donateGroup': {
          required: '<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Please select Donation Options'
        }
      }
    });
    form.valid()
    if (form.valid()) {

      $("#progressbar-5").progressbar({value: false});
      progressLabel.text("0%");
      var file_size;
      file_size = 0
      myDropzone.on("sending", function (file, xhr, formData) {
        file_size = parseInt(file.size, 10) / 1048576
        if (file_size > 20) {
          $('#msg').html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Video must be less then 20MB or maximum 20MB').css('color', 'red')
        }

        formData.append("title", $('#id_title').val());
        formData.append("why_rocks", $("#id_why_rocks").val());
        formData.append("category", $('#id_category').val());
        formData.append("subject_category", $('#id_subject_category').val());
        formData.append("made_by", $('#id_made_by').val());
        formData.append("made_by_option", $('#id_made_by_option').val());
        formData.append("donate_skigit", $('#id_donate_skigit').val());
        formData.append("bought_at", $('#id_bought_at').val().trim());
        formData.append("add_logo", $("input[type='radio'][name=add_logo]:checked").val());
        formData.append("receive_donate_sperk", $("input[type='radio'][name=receive_donate_sperk]:checked").val());
        formData.append("select_logo", $("input[type='radio'][name='select_logo']:checked").val());
      });

      if ($('#id_video_link').val() == '' && $('#id_title').val() != ''
          && $('#id_category').val() != ''
          && $('#id_subject_category').val() != ''
          && ($('#id_made_by').val() != '' || $('#id_made_by_option').val())
          && $('#id_why_rocks').val() != ''
          && myDropzone.getQueuedFiles().length !== 0
      ) {

        /* VIDEO DIRECT UPLOADING DROP-ZONE PROCESSING CALL */
        if ($("input[type='radio'][name=receive_donate_sperk]:checked").val() == '1') {
          if ($("input[type='radio'][name='donateGroup']:checked").val()) {
            $('#msg_donate').empty()
            $('#msg_donate').hide()
            $('#msg').empty()
            $('#msg').hide()
            $(".dz-progress").remove();
            $(".dz-remove").remove();
            $('.box_fulllodar').show();
            myDropzone.processQueue();
          }
          else {
            $("#msg_donate").empty()
            $("#msg_donate").show()
            $("#msg_donate").html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Please select target organization and chose Donation option').addClass('f_type');
            return false;
          }
        }
        else if ($("input[type='radio'][name=receive_donate_sperk]:checked").val() == '2') {
          $("#msg_donate").empty()
          $("#msg_donate").hide()
          $("#msg").empty()
          $("#msg").hide()
          $(".dz-progress").remove();
          $(".dz-remove").remove();
          $('.box_fulllodar').show();
          myDropzone.processQueue();
        } else {
          $("#msg_donate").empty()
          $("#msg_donate").hide()
          $("#msg").empty()
          $("#msg").hide()
          $(".dz-progress").remove();
          $(".dz-remove").remove();
          $('.box_fulllodar').show();
          myDropzone.processQueue();
        }
      }
      else if ($('#id_video_link').val() != ''
          && $('#id_title').val() != ''
          && ($('#id_made_by').val() != '' || $('#id_made_by_option').val())
          && $('#id_category').val() != ''
          && $('#id_why_rocks').val() != ''
          && $('#id_subject_category').val() != '' &&
          urlVerify($('#id_video_link').val()) == true) {

        var video_data;
        video_data = {
          "title": $('#id_title').val(),
          "category": $('#id_category').val(),
          "subject_category": $('#id_subject_category').val(),
          "made_by": $('#id_made_by').val(),
          "made_by_option": $('#id_made_by_option').val(),
          "bought_at": $('#id_bought_at').val().trim(),
          "add_logo": $("input[type='radio'][name=add_logo]:checked").val(),
          "receive_donate_sperk": $("input[type='radio'][name=receive_donate_sperk]:checked").val(),
          "select_logo": $("input[type='radio'][name='select_logo']:checked").val(),
          "why_rocks": $("#id_why_rocks").val(),
          "video_link": $("#id_video_link").val(),
          "donate_sperk": $("input[type='radio'][name='donateGroup']:checked").val()
        }

        /* VIDEO LINK UPLODING AJAX CALL */
        if ($("input[type='radio'][name=receive_donate_sperk]:checked").val() == '1') {
          if ($("input[type='radio'][name='donateGroup']:checked").val()) {
            $('#msg_donate').empty()
            $('#msg_donate').hide()
            $('#msg').empty()
            $('#msg').hide()
            videolink_ajax(video_data)
          }
          else {
            $("#msg_donate").empty()
            $("#msg_donate").show()
            $("#msg_donate").html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Please select target organization and chose Donation option')
            return false;
          }
        }
        else if ($("input[type='radio'][name=receive_donate_sperk]:checked").val() == '2') {
          $("#msg_donate").empty()
          $("#msg_donate").hide()
          $("#msg").empty()
          $("#msg").hide()
          videolink_ajax(video_data)
        } else {
          $("#msg_donate").empty()
          $("#msg_donate").hide()
          $("#msg").empty()
          $("#msg").hide()
          videolink_ajax(video_data)
        }
      }
      else {
        if ($('#id_bought_at').val().trim() != '' && urlVerify($('#id_bought_at').val().trim()) == false) {
          $("#msg").empty()
          $("#msg").show()
          $("#msg").html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Acceptable Upload URL Format needs to Be Corrected (I bought my awesome thing at )').css("color", "red")
        }
        else if ($('#id_video_link').val() != '' && urlVerify($('#id_video_link').val()) == false) {
          $("#msg").empty()
          $("#msg").show()
          $("#msg").html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> You must enter valid video URL in order to proceed').css('color', 'red')
        }
        else if ($('#id_video_link').val() == '' && myDropzone.getQueuedFiles().length === 0) {

          $("#msg").empty()
          $("#msg").show()
          $("#msg").html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> You must either upload a video or link to a video file in order to proceed').css('color', 'red')
        }
        else if ($('#id_video_link').val() == '' && urlVerify($('#id_video_link').val()) == true && myDropzone.getQueuedFiles().length !== 0) {
          $("#msg").empty()
          $("#msg").hide()
        }

        if ($("input[type='radio'][name=receive_donate_sperk]:checked").val() === '1') {
          if ($("input[type='radio'][name='donateGroup']:checked").val()) {
            $('#msg_donate').hide()
          }
          else {
            $('#msg_donate').show()
            $('#msg_donate').html('<span style="font-size:20px;"><i class="glyphicon glyphicon-remove-circle" style="top: 5px !important;" /></span> Please select target organization and chose Donation option')
          }
        }
      }


      myDropzone.on("success", function (file, responseText) {

        if (responseText.is_success == true) {
          $("#msg").empty()
          $("#msg").show()
          $("#msg").html(responseText.message).css('color', 'green')
          setTimeout(progress, 200)
        }
        else {
          $('.box_fulllodar').hide();
          myDropzone.removeAllFiles();
          $("#msg").empty()
          $("#msg").show()
          $("#msg").html(responseText.message).css('color', 'red')

        }
      });
    } else {

    }
  });

  function urlVerify(url_value) {
    var regexp = /^http:\/\/|(www\.)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/;
    return regexp.test(url_value);
  }

  $('#id_video_link').on('input', function () {

    if ($("#id_video_link").val() == '') {
      /* Display the DROP ZONE FIELD if Link field is empty or not provided */
      $("#fileUploadform").show()
      $("#file_uplod_div").show()
      $("#file_uplode_note").show()
      $("#msg").empty()
      $("#msg").hide()
    }
    else {
      /* HIDES THE DROP ZONE FIELD IF VIDEO IS UPLOADED BY LINK */
      $("#fileUploadform").hide()
      $("#file_uplod_div").hide()
      $("#file_uplode_note").hide()
      myDropzone.removeAllFiles();
    }
  });

  /* CANCEL BUTTON CLICK CLEAR DROP ZONE FIELD <FILE UPLOAD FIELD> */
  $('#clear_form').click(function () {
    myDropzone.removeAllFiles();
    $("#msg").empty()
    $("#msg").hide()
    $("#msg_donate").hide()
    $("#errors").empty()
    $('#target').hide()
    $('.cancel').removeClass()
    clearrecord();
  });

  $('#id_made_by_option').on('change keyup', function () {
    if ($('#id_made_by_option').val() == '') {
      $("#id_made_by").removeAttr('disabled');
      speark_logo()
    }
  });

});
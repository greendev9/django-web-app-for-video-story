$j = jQuery.noConflict();

var registrationForm = $j("#registration_form");

var validator = registrationForm.validate({
    ignore: "", //Hidden inputs
    rules: {
      'username': {
        required: true,
        nospace: true,
      },
      'email': {
        required: {
          depends: function () {

            $j(this).val($j.trim($j(this).val()));
            return true;
          }
        },
        customemail: true,

      },
      'password1': {
        required: {
          depends: function () {
            $j(this).val($j.trim($j(this).val()));
            return true;
          }
        },
        oneuppercaseletter: true,
        minlength: 8,
        maxlength: 16
      },
      'password2': {
        required: true,
        equalTo: "#id_password1"
      },
      'type_check': {
        required: true
      },
      'usepolicy_check': {
        required: true
      },
      'ageconfirm_check': {
        required: true
      }
    },
    messages: {
      'username': {
        required: "<img width='25' src='/static/images/error_icon.png'>A username is required",
        nospace: "<img width='25' src='/static/images/error_icon.png'>Your username must contain only letters, numbers and underscores. Spaces are NOT allowed.",
      },
      'email': {
        required: "<img width='25' src='/static/images/error_icon.png'>Email address is required.",
        customemail: "<img width='25' src='/static/images/error_icon.png'>Please enter a valid email address."
      },
      'password1': {
        required: "<img width='25' src='/static/images/error_icon.png'>A password is required",
        minlength: "<img width='25' src='/static/images/error_icon.png'>Your password must contain minimum of 8 characters with at least one upper case character",
        oneuppercaseletter: "<img width='25' src='/static/images/error_icon.png'>Your password must contain between 8 and 16 characters with at least 1 number and 1 upper case letter. Special characters are allowed.",
        maxlength: "<img width='25' src='/static/images/error_icon.png'>Your password must contain between 8 and 16 characters with at least 1 number and 1 upper case letter. Special characters are allowed.",
      },
      'password2': {
        required: "<img width='25' src='/static/images/error_icon.png'>Your password verification did not match. Please re-type your password.",
        equalTo: "<img width='25' src='/static/images/error_icon.png'>Your password verification did not match. Please re-type your password."
      },
      'type_check': {
        required: "<div class='checkbox-error-msg'><span><img width='25' src='/static/images/error_icon.png'>Please check the box to proceed</span></div>",
      },
      'usepolicy_check': {
        required: "<div class='checkbox-error-msg'><span><img width='25' src='/static/images/error_icon.png'>Please check the box to proceed</span></div>",
      },
      'ageconfirm_check': {
        required: "<div class='checkbox-error-msg'><span><img width='25' src='/static/images/error_icon.png'>Please check the box to proceed</span></div>",
      }
    }
  });

$j(function () {

    if(username_error) {
        validator.showErrors({
            "username": username_error
        })
    }

    if(email_error) {
        validator.showErrors({
            "email": email_error
        })
    }

    if(password1_error) {
        validator.showErrors({
            "password1": password1_error
        })
    }

    if(password2_error) {
        validator.showErrors({
            "password2": password2_error
        })
    }

    $j('#pass_chang_form').on('focus', ':input', function () {
        $j(this).attr('autocomplete', 'off');
    });

      $j('.form-control').on('keypress', function () {
        $j('.errorlist').empty()
        $j('.errorlist').hide()
      });

      function RegisterFormValidation() {
        return registrationForm.valid();
      }

      $j('#form_submit').click(function () {
        RegisterFormValidation();
        $j('.errorlist').show();
      });

});

function myFunction1() {
    var x = document.getElementById(password1_label_text);
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password";
    }
}

function myFunction2() {
    var x = document.getElementById(password2_label_text);
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password";
    }
}

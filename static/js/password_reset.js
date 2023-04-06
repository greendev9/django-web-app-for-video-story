$j = jQuery.noConflict();

var passwordResetForm = $j("#password_reset_form");

passwordReset_validator = passwordResetForm.validate({
ignore: "", //Hidden inputs
rules: {
  'email': {
    required: {
      depends: function () {
        $j(this).val($j.trim($j(this).val()));
        return true;
      }
    },
    customemail: true
  }
},
messages: {
  'email': {
    required: "<img width='25' src='/static/images/error_icon.png'>Email address is required.",
    customemail: "<img width='25' src='/static/images/error_icon.png'>Please enter a valid email address associated with a Skigit account."
  }
}
});

$j(function () {
  function passwordResetFormValidation() {
      return passwordResetForm.valid()
  }

  function check_social_user(email) {
    var res = false
    $j.ajax({
      url: "/check_social_user/", // the endpoint
      type: "POST", // http method
      data: {'email': email},
      success: function(response) {
        if (response.user_exist){
          passwordReset_validator.showErrors({
            "email": `<img width='25' src='/static/images/error_icon.png'>This email address is associated
             to an <a style="font-weight: bold; color: #20c6f4;" href="${response.login_url}">${response.provider}</a>  account. You cannot change password through Skigit.
            You must login to <a style="font-weight: bold; color: #20c6f4;" href="${response.login_url}">${response.provider}</a> to use their password change feature to
            change your password. The next time you login to Skigit, the new password will be linked to your credentials`
        });
          res = true
        }
      },
      async: false
    });
    return res
  }

  $j('#form_submit').click(function () {
    is_valid = passwordResetFormValidation();
    if (is_valid){
        var id_email = $j('#id_email').val().trim();
        var id_email = id_email.toLowerCase();
        $j.ajax({
          url: "/email_exits_check/", // the endpoint
          type: "POST", // http method
          data: {'email': id_email.toLowerCase()},
          success: function(response) {
            if (response.is_success){
              var is_socail_user = check_social_user(id_email)
              if (!is_socail_user) $j("#password_reset_form").submit();
            } else {
              passwordReset_validator.showErrors({
                  "email": "<img width='25' src='/static/images/error_icon.png'>This email address is not associated with a Skigit account. Please try again."
              });
            }
          }
        });
    }
    return false;
  });

});

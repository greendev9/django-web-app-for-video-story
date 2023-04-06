function business_verified(user_id) {
    // Get the checkbox
    //var checkBox = document.getElementById("business_verified");
    const checkState = document.getElementById(user_id);
    var host = window.location.host;

    //const rejectButton = document.querySelector('#'+user_id+'_btn')
    if (checkState.checked)
    {
        $.post("https://"+host+"/verifyBusinessAccount/", {user_id: user_id}, function(result){

        });
    }else{
        $.post("https://"+host+"/rejectBusinessAccount/", {user_id: user_id, reason: "Your account is deactivated. Please Contact to Admin."}, function(result){

        });
    }
}

function rejectEmail(user_id){
    var host = window.location.host;
    var reason = document.getElementById(user_id+"_btn").value;
    const checkState = document.getElementById(user_id);
    $.post("https://"+host+"/rejectBusinessAccount/", {user_id: user_id, reason: reason}, function(result){
        if(result.status == 'success') {
            checkState.checked = false; 
        }
    });
}

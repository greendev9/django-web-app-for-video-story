
// Ask the browser for permission to show notifications
// Taken from https://developer.mozilla.org/en-US/docs/Web   /API/Notification/Using_Web_Notifications
window.addEventListener('load', function () {
    Notification.requestPermission(function (status) {
        // This allows to use Notification.permission with Chrome/Safari
        if (Notification.permission !== status) {
            Notification.permission = status;
        }
    });
});


// Create an instance of vanilla dragon
// var dragon = swampdragon.open({onopen:  onOpen, onchannelmessage:    onChannelMessage});

// New channel message received
swampdragon.onChannelMessage(function(channels, message){
// Add the notification
    addNotification((message.data));

});

// SwampDragon connection open
swampdragon.open(function() {
// Once the connection is open, subscribe to notifications
    swampdragon.subscribe('notifications', 'notifications');
});


// Add new notifications
function addNotification(notification) {
    var $ = jQuery.noConflict()
// If we have permission to show browser notifications
// we can show the notifiaction
    if (window.Notification && Notification.permission === "granted") {
        if(notification.msg_type=='friends' || notification.msg_type=='like' || notification.msg_type=='follow' || notification.msg_type=='plug' || notification.msg_type=='plug-plug' || notification.msg_type=='friends_accepted' || notification.msg_type=='un_plug' || notification.msg_type=='new_post' || notification.msg_type=='share' || notification.msg_type=='plug_primary' ){
            new Notification(notification.message);

            var general_badge = $('#general_badge').text();
            var friends_badge = $('#friend_badge').text();

            if(parseInt(general_badge)>=0){
                $('#general_badge').css('visibility','visible');
            }

            $('#general_badge').text(parseInt($('#general_badge').text())+1);

            if(notification.msg_type=='friends'){
                if(parseInt(friends_badge)>=0){
                    $('#friend_badge').css('visibility','visible');
                }
                $('#friend_badge').text(parseInt($('#friend_badge').text())+1);
            }

            $('#notify_ul :first').append('<li class="list_group_item">'+notification.message+'</li>');
        }
    }
}

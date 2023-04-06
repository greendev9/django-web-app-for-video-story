'use strict';

var app = angular.module('userNotification', ['ngAnimate', 'ngSanitize', 'ui.bootstrap']);

app.controller('notificationCtrl', function($scope) {

  $scope.notificationsPopover = {
    title: '',
    templateUrl: '/static/templates/notifications.html',
    open: function open() {
      $scope.notificationsPopover.isOpen = true
    }
  };

});

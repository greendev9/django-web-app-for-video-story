'use strict';

var userLogin = angular.module('userLogin', ['core.modalForm']);

userLogin.run(['$rootScope', '$window', 'formService', function ($rootScope, $window, formService) {
  // $rootScope.user = {
  //   email: "test@google.com",
  //   password: "test123456"
  // };

  $rootScope.init = function () {
//    $window.location.reload();
  };

  // open modal form dynamically
  $rootScope.openLogin = formService({
    data: $rootScope.user,
    templateUrl: '/static/templates/login.html',
    method: 'POST',
    callback: $rootScope.init,
    path: '/login_ajax/',
    dialogClass: 'login-modal',
    closeOnSuccess: true,
    redirect: '/'
  });
}]);



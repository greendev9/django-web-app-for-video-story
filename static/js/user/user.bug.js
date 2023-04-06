'use strict';

var userBug = angular.module('userBug', ['core.modalForm']);

userBug.run(['$rootScope', '$window', 'formService', function ($rootScope, $window, formService) {

  $rootScope.bug = {
    id_bug_page_url: $window.location.href,
    id_bug_title: $window.location.pathname
  };

  $rootScope.init = function () {
    $window.location.reload();
  };

  // open modal form dynamically
  $rootScope.open = formService({
    data: $rootScope.bug,
    templateUrl: '/static/templates/bug_report.html',
    method: 'POST',
    callback: $rootScope.init,
    path: '/bug-management/',
    dialogClass: 'small',
    closeOnSuccess: true
  });
}]);

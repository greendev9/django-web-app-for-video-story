'use strict';

var userShare = angular.module('userShare', ['core.modalForm']);

userShare.run(['$rootScope', '$window', 'formService', function ($rootScope, $window, formService) {

  $rootScope.share = {
    id_bug_page_url: $window.location.href,
    id_bug_title: $window.location.pathname
  };

  $rootScope.init = function () {
    $window.location.reload();
  };

  // open modal form dynamically
  $rootScope.open = formService({
    data: $rootScope.share,
    templateUrl: '/static/templates/share.html',
    method: 'POST',
    callback: $rootScope.init,
    // path: '/bug-management/',
    dialogClass: 'small',
    closeOnSuccess: true
  });
}]);

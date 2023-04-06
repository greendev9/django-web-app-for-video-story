'use strict';

angular.module('skigitApp', [
  'ui.bootstrap',
  'ngCookies',
  'coreSkigit',
  'userSkigit',
  'popoverSkigit'
]).config(['$httpProvider', function ($httpProvider) {
  $httpProvider.defaults.xsrfCookieName = 'csrftoken';
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);


'use strict';var app=angular.module('formsUpload',['ui.validate']);app.controller('ValidateUpload',function($scope,$timeout,$q){$scope.showsperklogo=function(){angular.element(document.querySelector('ul.sperk-logo')).addClass('open');angular.element(document.querySelector('.p_body')).css("display","block")};$scope.pbody=function(){angular.element(document.querySelector('.target-div')).removeClass('open');angular.element(document.querySelector('ul.sperk-logo')).removeClass('open');angular.element(document.querySelector('.p_body')).css("display","none")};$scope.target=function(){angular.element(document.querySelector('.target-div')).addClass('open');angular.element(document.querySelector('.p_body')).css("display","block")};$scope.changemadeby=function(){$scope.ops=!1;$scope.sorry=!1;angular.element(document.querySelector('#id_made_by')).attr('disabled','disabled');if($scope.changemade.length===0||typeof $scope.changemade==='undefined'){if($scope.add_logo==='1'||$scope.add_logo===1){$scope.ops=!0;angular.element(document.querySelector('ul.sperk-logo')).addClass('open');angular.element(document.querySelector('.p_body')).css("display","block")}else{$scope.sorry=!0}}}})
'use strict';
angular.module('core.modalForm', ['ui.bootstrap']).factory('formService', ['$uibModal', '$log', function($uibModal, $log) {
    var ModalInstanceCtrl = function($scope, $http, $window, $document, $timeout, $uibModalInstance, config) {
        $scope.sync = !1;
        $scope.error = '';
        $scope.formInvalid = !1;
        $scope.data = config.field ? config.data[config.field] : config.data;
        $scope.redirect = $document.find('#login-modal-blk').attr('redirect');
        $scope.ok = function(f) {
            if (f.$invalid) {
                $scope.formInvalid = !0;
                $scope.form = f;
                return
            }
            if (config.path) {
                $scope.sync = !0;
                $scope.error = '';
                $scope.succ = !1;
                $http({
                    method: config.method || 'POST',
                    url: config.path,
                    data: $scope.data
                }).then(function(data, status, headers, cfg) {
                    if (data.data.is_success && data.data.status !== 'CodeSent') {

                        $scope.success = data.data.message;
                        $timeout(function() {
                            $scope.succ = !0
                        }, 3000);
                        if ($scope.redirect || config.redirect) {
                            $window.location.hash = "";
                            $timeout(function() {
                                if ($scope.redirect) {
                                    $window.location.href = $scope.redirect
                                } else {
                                    $window.location.href = config.redirect
                                }
                            }, 2900)
                        } else {
                            if (config.callback) {
                                config.callback(config.data, data)
                            }
                            if (config.closeOnSuccess) {
                                return $uibModalInstance.close()
                            }
                            $scope.succ = !0;
                            $scope.sync = !1
                        }
                    }
                    else if(data.data.is_success) {
                        $uibModalInstance.close();
                        jQuery('#two-fa-modal').modal();
                        jQuery('#two-fa-modal').find('.two-fa-code').val('');
                        jQuery('#two-fa-modal').find('input[name="email"]').val($scope.data.email);
                    }
                    else {
                        $scope.sync = !1;
                        $scope.error = data.data.message;
                        $timeout(function() {
                            $scope.error = ''
                        }, 5000)
                    }
                }).catch(function(error, response) {
                    $scope.sync = !1;
                    if (typeof(response) === 'undefined') {
                        $scope.error = error.statusText || 'server response: ' + error.status
                    } else {
                        $scope.error = response.data.message || 'server response:' + response.status
                    }
                    $timeout(function() {
                        $scope.error = ''
                    }, 5000)
                })
            } else {
                if (config.callback) {
                    config.callback(config.data, null)
                }
                if (config.closeOnSuccess) {
                    $uibModalInstance.close()
                }
            }
        };
        $scope.cancel = function() {
            $uibModalInstance.dismiss('cancel')
        }
    };
    var openModal = function(params) {
        params.data = params.data || {};
        if (!params.closeOnSuccess || params.closeOnSuccess === 'true') {
            params.closeOnSuccess = !0
        } else {
            params.closeOnSuccess = !1
        }
        params.method = params.method || 'POST';
        var modalInstance = $uibModal.open({
            templateUrl: params.templateUrl,
            controller: ModalInstanceCtrl,
            windowClass: params.dialogClass,
            resolve: {
                config: function() {
                    return params
                }
            }
        });
        modalInstance.result.then(function(data) {
            $log.info('modal closed.')
        }, function() {
            $log.info('modal dismissed.')
        })
    };
    return function(params) {
        return openModal.bind(null, params)
    }
}]).directive('modalForm', function() {
    return {
        restrict: 'EA',
        scope: {
            data: "=?",
            field: "@",
            templateUrl: "@",
            method: "@",
            path: "@",
            dialogClass: "@",
            redirect: "@",
            closeOnSuccess: "@",
            callback: "&"
        },
        controller: ['$scope', 'formService', function($scope, formService) {
            $scope.open = formService($scope)
        }],
        link: function(scope, element, attrs) {
            element.click(function() {
                scope.open()
            })
        }
    }
})
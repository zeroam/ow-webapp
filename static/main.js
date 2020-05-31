(function () {
  'use strict'

  var app = angular.module('App', [])

  app.controller('Controller', ['$scope', '$log', '$http', '$timeout',
    function ($scope, $log, $http, $timeout) {

      $scope.loading = false
      $scope.imagePath = "/static/img/default.jpg"

      $scope.getResults = function () {
        var userInput = $scope.url
        console.log(userInput)

        $http.post('/obj_detect', { 'url': userInput }).then(
          function (results) {
            var jobID = results.data
            $log.log(jobID)
            getResults(jobID)
            $scope.loading = true
            $scope.objects = null
            $scope.imageSize = null
          },
          function (error) {
            $log.log(error)
          }
        )
      }

      function getResults(jobID) {
        var timeout = ""

        var poller = function () {
          $http.get('results/' + jobID).then(
            function (resp) {
              if (resp.status === 202) {
                $log.log(resp.data, resp.status)
              } else if (resp.status === 200) {
                $log.log(resp.data)
                $scope.loading = false
                $scope.imageSize = resp.data.image_size
                $scope.imagePath = resp.data.url_path
                $scope.objects = resp.data.objects
                $timeout.cancel(timeout)
                return false
              }
              timeout = $timeout(poller, 2000)
            },
            function (error) {
              $log.log(error)
              $scope.loading = false
            }
          )
        }

        poller()
      }
    }])
}())
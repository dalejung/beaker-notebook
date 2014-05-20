/*
 *  Copyright 2014 TWO SIGMA OPEN SOURCE, LLC
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */
/**
 * bkCellMenuPluginManager
 * bkCellMenuPluginManager load and manages loaded cell menu plugins.
 */
(function() {
  'use strict';
  var module = angular.module('bk.cellMenuPluginManager', [
    'bk.utils',
    'bk.helper'  // This is only for ensuring that window.bkHelper is set, don't use bkHelper directly
  ]);
  module.factory('bkCellMenuPluginManager', function(bkUtils) {
    // loaded plugins
    var _cellMenuPlugins = {};

    var addPlugin = function(cellType, items) {
      if (!_cellMenuPlugins[cellType]) {
        _cellMenuPlugins[cellType] = [];
      }
      _(items).each(function(it) {
        _cellMenuPlugins[cellType].push(it);
      });
    };

    return {
      reset: function() {
        var self = this;
        bkUtils.httpGet('../beaker/rest/util/getCellMenuPlugins')
            .success(function(menuUrls) {
              menuUrls.forEach(self.loadPlugin);
            });
      },
      loadPlugin: function(url) {
        return bkUtils.loadModule(url).then(function(ex) {
          if (_.isArray(ex.cellType)) {
            _(ex.cellType).each(function(cType) {
              addPlugin(cType, ex.plugin);
            });
          } else {
            addPlugin(ex.cellType, ex.plugin);
          }
          return ex.plugin;
        });
      },
      getPlugin: function(cellType) {
        return _cellMenuPlugins[cellType];
      },
      getMenuItems: function(cellType, scope) {
        var menuItemGetters = _cellMenuPlugins[cellType];
        var newItems = [];
        _(menuItemGetters).each(function(getter) {
          newItems.push(getter(scope));
        });
        return newItems;
      }
    };
  });
})();

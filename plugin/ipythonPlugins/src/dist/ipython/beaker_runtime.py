# Copyright 2014 TWO SIGMA OPEN SOURCE, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, urllib, urllib2, json, pandas, yaml, numpy, IPython, datetime
from IPython.utils.traitlets import Unicode

# should be inner class to Beaker
class DataFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        # similarly handle Panels.
        # make this extensible by the user to handle their own types.
        if type(obj) == datetime.datetime:
            out = {}
            out['type'] = "Date"
            out['value'] = obj.strftime("%b %d, %Y %I:%M:%S %p")
            return out
        if type(obj) == pandas.core.frame.DataFrame:
            out = {}
            out['type'] = "TableDisplay"
            out['columnNames'] = obj.columns.tolist()
            out['values'] = obj.values.tolist()
            out['subtype'] = "TableDisplay"
            ty = []
            num = len(obj.columns.tolist())
            x = 0;
            for x in range(0,num):
              	ty.append( type(obj.values[0][x]).__name__)
            out['types'] = ty
            return out
        if type(obj) == pandas.core.series.Series:
            return obj.to_dict()
        if isinstance(obj, numpy.ndarray) and obj.ndim == 2:
        	# this should become a table like above
            return obj.tolist()
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        if isinstance(obj, numpy.generic):
            return obj.item()
        return json.JSONEncoder.default(self, obj)

class MyJSONFormatter(IPython.core.formatters.BaseFormatter):
    format_type = Unicode('application/json')
    def __call__(self, obj):
        try:
            return json.dumps(obj, cls=DataFrameEncoder)
        except:
            return None

class Beaker:
    """Runtime support for Python code in Beaker."""
    session_id = ''
    registered = False
    core_url = '127.0.0.1:' + os.environ['beaker_core_port']
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, core_url, 'beaker',
                              os.environ['beaker_core_password'])
    urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(password_mgr)))

    def set4(self, var, val, unset, sync):
        args = {'name': var, 'session':self.session_id, 'sync':sync}
        if not unset:
          args['value'] = json.dumps(val, cls=DataFrameEncoder)
        req = urllib2.Request('http://' + self.core_url + '/rest/namespace/set',
                              urllib.urlencode(args))
        conn = urllib2.urlopen(req)
        reply = conn.read()
        if reply != 'ok':
            raise NameError(reply)
  
    def get(self, var):
        req = urllib2.Request('http://' + self.core_url + '/rest/namespace/get?' + 
                              urllib.urlencode({'name': var, 'session':self.session_id}))
        conn = urllib2.urlopen(req)
        result = yaml.load(conn.read()) # would use json.loads but it returns unicode
        if not result['defined']:
            raise NameError('name \'' + var + '\' is not defined in notebook namespace')
        return result['value']

    def set_session(self, id):
        self.session_id = id

    def register_output(self):
        if (self.registered == False):
            ip = IPython.InteractiveShell.instance()
            ip.display_formatter.formatters['application/json'] = MyJSONFormatter(parent=ip.display_formatter)
            self.registered = True

    def set(self, var, val):
        return self.set4(var, val, False, True)

    def __setattr__(self, name, value):
        if 'session_id' == name:
            self.__dict__['session_id'] = value
            return
        return self.set(name, value)

    def __getattr__(self, name):
        return self.get(name)


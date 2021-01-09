import os
import flask
import inspect
import tgbf.constants as con

from flask import Flask, request, render_template


class EndpointAction(object):

    def __init__(self, action, secret=None):
        self.action = action
        self.secret = secret

    def __call__(self):
        if self.secret:
            secret = request.args.get('secret')
            if not secret or secret != self.secret:
                return render_template("default.html")

        if self.action:
            param = str(inspect.signature(self.action))[1:-1]

            if param:
                param = request.args.get(param)

                if param:
                    result = self.action(param)
                else:
                    result = self.action(None)
            else:
                result = self.action()
        else:
            return render_template("default.html")

        # Create the answer (bundle it in a correctly formatted HTTP answer)
        if isinstance(result, str):
            # If it's a string, we bundle it in a HTML-like answer
            self.response = flask.Response(result, status=200, headers={})
        else:
            # If it's something else (dict, ..) we jsonify and send it
            self.response = flask.jsonify(result)

        # Send it
        return self.response


class FlaskAppWrapper(object):

    def __init__(self, name, port=None):
        self.port = port if port else 5000
        template_dir = os.path.join(os.pardir, con.DIR_RES, con.DIR_TEM)
        self.app = Flask(name, template_folder=template_dir)

    def run(self, debug=False):
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)

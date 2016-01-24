from . import app

from flask import jsonify


@app.errorhandler(404)
def error_404(e):
    return jsonify(errors=[dict(status=404, title='Not Found')]), 404

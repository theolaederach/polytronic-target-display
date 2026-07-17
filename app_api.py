from flask import Blueprint, request
from write_target import write_target
from random_shot import random_shot

api = Blueprint('api', __name__,template_folder='templates')

@api.route('/render_target', methods=['GET'])
def render_target():
    if request.method == 'GET':
        target_number = request.args['target_number']

        write_target("assets/template.png", random_shot(7), f"static/target{target_number}.png")
        return f"Target {target_number} written"
    else:
        return "Method not allowed"

@api.route('/')
def hello_world():
    return 'Hello, World!'

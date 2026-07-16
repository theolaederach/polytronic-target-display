from flask import Blueprint, request
from write_target import write_target

api = Blueprint('api', __name__,template_folder='templates')

@api.route('/render_target', methods=['GET'])
def render_target():
    if request.method == 'GET':
        target_number = request.args['target_number']

        write_target("assets/template.png", [(434,123),(567,234),(890,345),(234,567),(789,78),(901,34),(456,78)], f"static/target{target_number}.png")
        return f"Target {target_number} written"
    else:
        return "Method not allowed"

@api.route('/')
def hello_world():
    return 'Hello, World!'

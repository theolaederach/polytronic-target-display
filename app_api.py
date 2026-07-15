from flask import Blueprint
from write_target import write_target

api = Blueprint('api', __name__,template_folder='templates')

@api.route('/render_target')
def render_target():
    write_target("assets/template.png", [(434,123),(567,234),(890,345)], "assets/result.png")
    return "Target written"

@api.route('/')
def hello_world():
    return 'Hello, World!'

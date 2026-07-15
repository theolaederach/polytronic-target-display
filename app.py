# Title : main file
# Author : Théo
# Last update : 15.07.2026
# Description : file who init the project and the web server. Run this file to start the project.

from flask import Flask, render_template

from app_api import api

app = Flask(__name__)


app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def index():
    return render_template('home.html')






if __name__ == '__main__':
    app.run(debug=True)

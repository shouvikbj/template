from flask import Flask, flash, redirect, render_template, request, session, url_for, Response, make_response
from flask_session import Session
from tempfile import gettempdir
import json
from sql import *



app = Flask(__name__)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
def index():
    return render_template('layout.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)


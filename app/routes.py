from app import app
from flask import render_template
QUE = ["count chocula"]

@app.route('/')
@app.route('/index')
@app.route('/index/<name>')
def index(name=None):
    if name:
        QUE.append(name)
    return render_template('signin.html', que=QUE)

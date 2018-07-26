from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField

QUE = [
    {"name": "count chocula", "reason": "Get coco ceral"},
    {"name": "Silly Rabit", "reason": "Get Trix"},
]
# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()])
    reason = TextField('Reason for visit:', validators=[validators.required()])


@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)
    if request.method == 'POST':
        name = request.form['name']
        reason = request.form['reason']
        if form.validate():
            student = {"name":name, "reason": reason}
            QUE.append(student)
        else:
            flash('Error: All the form fields are required. ')
    wait = str(len(QUE)) + " min"
    return render_template('check_in.html', form=form, que=QUE, wait=wait)

@app.route("/advisor", methods=['GET', 'POST'])
def advisor():
    form = ReusableForm(request.form)
    if request.method == 'POST':
        if len(QUE) > 0:
            student = QUE.pop(0)
        else:
            student = None
        return render_template('advisor.html', form=form, student=student, que=QUE)
    else:
        return render_template('advisor.html', form=form, student=None, que=QUE)

if __name__ == "__main__":
    app.run()

from flask import Flask, render_template, flash, request, g, redirect
from wtforms import Form, TextField, IntegerField, TextAreaField, validators, StringField, SubmitField
from flask_oidc import OpenIDConnect
from okta import UsersClient
from code_db import CodeSystem
okta_client = UsersClient("https://dev-505726.oktapreview.com/", "00HEKJlOz4Wpxb_IZMNplxxapvwQJyvhcZCp1FI9uB")

CODE_DB = CodeSystem()
QUE = [
    {"name": "count chocula", "reason": "Get coco ceral"},
    {"name": "Silly Rabit", "reason": "Get Trix"},
]
# App config.
DEBUG = True
app = Flask(__name__)

app.config.from_object(__name__)
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'
oidc = OpenIDConnect(app)

@app.before_request
def before_request():
    if oidc.user_loggedin:
        g.user = okta_client.get_user(oidc.user_getfield("sub"))
    else:
        g.user = None

class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()])
    reason = TextField('Reason for visit:', validators=[validators.required()])

class OptCodeForm(Form):
    code = IntegerField('Workshop Code:')

class NewCodeForm(Form):
    uses = IntegerField('Number of Uses')

@app.route("/", methods=['GET', 'POST'])
def check_in():
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
@oidc.require_login
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

@app.route("/appointment", methods=['GET', 'POST'])
@oidc.require_login
def appointments():
    "appointment system. validates that a user has gone to opt appointment"
    if g.user.profile.email in CODE_DB:
        return redirect('https://calendar.google.com/calendar/selfsched?sstoken=UUxrUmkyT1FMUXMxfGRlZmF1bHR8YzBkYWVkZGQ4Njk1ZmMyMzc2YzlkMjU4ZDBlMzU2YzM')
    if request.method == 'POST':
        code = int(request.form['code'])
        print(code)
        valid = CODE_DB.check_code_validity(code, g.user.profile.email)
        print(valid)
        if valid:
            return redirect('https://calendar.google.com/calendar/selfsched?sstoken=UUxrUmkyT1FMUXMxfGRlZmF1bHR8YzBkYWVkZGQ4Njk1ZmMyMzc2YzlkMjU4ZDBlMzU2YzM')
    form = OptCodeForm(request.form)
    return render_template('opt_workshop.html', form=form)

@app.route("/appointment/admin", methods=['GET', 'POST'])
@oidc.require_login
def appointments_admin():
    "appointment system. generate a code"
    if request.method == 'POST':
        uses = int(request.form['uses'])
        code = CODE_DB.add_code(limit=uses)
    else:
        code = None
    form = OptCodeForm(request.form)
    return render_template('code_generator.html', form=form, code=code)


@app.route("/appointment/admin/codes", methods=['GET', 'POST'])
@oidc.require_login
def appointments_admin_codes():
    "appointment system. View codes"
    codes  = []
    for record in CODE_DB:
        print(CODE_DB[record])
        if CODE_DB[record] is True:
            pass
        elif 'limit' in CODE_DB[record]:
            CODE_DB[record].update({'code':record})
            codes.append(CODE_DB[record])
    return render_template('view_codes.html', codes=codes)

if __name__ == "__main__":
    app.run()

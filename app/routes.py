from flask import Flask, render_template, flash, request, g, redirect
from wtforms import Form, TextField, IntegerField, TextAreaField, validators, StringField, SubmitField
from flask_oidc import OpenIDConnect
from okta import UsersClient

# local imports
from code_db import CodeSystem
from opt_logger import Logger, datetime

# Configuration
okta_client = UsersClient("https://dev-505726.oktapreview.com/", "00HEKJlOz4Wpxb_IZMNplxxapvwQJyvhcZCp1FI9uB")


CODE_DB = CodeSystem("codedb2.json")
ADIVSOR_DB = CodeSystem("advisors.json")
QUE = []
QUE_LOGGER = Logger(filename="que_logs.log")
QUE_SEEN_LOGGER = Logger(filename="que_seen_logs.log")
WS_LOGGER = Logger(filename="workshop_logs.log")
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


### JUNK FOR TESTING
ADIVSOR_DB.update({'bblack@scu.edu':'Brandon'})


#######################################################
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

class adminForm(Form):
    advisor = TextField('Advisor Email')

def check_rbac(email):
    if email in ADIVSOR_DB:
        return True
    else:
        return False
#######################################################
##                     ROUTES                        ##
#######################################################

#######################################################
##                  LANDING ROUTES                   ##
#######################################################

@app.route("/", methods=['GET', 'POST'])
def landing():
    return render_template('main_page.html')

#######################################################
##                  DROP IN ROUTES                   ##
#######################################################

@app.route("/drop_in", methods=['GET', 'POST'])
def check_in():
    form = ReusableForm(request.form)
    if request.method == 'POST':
        name = request.form['name']
        reason = request.form['reason']
        QUE_LOGGER.info("%s checked in for %s" %(name, reason))
        if form.validate():
            student = {"name":name, "reason": reason}
            QUE.append(student)
        else:
            flash('Error: All the form fields are required. ')
    wait = str(len(QUE)) + " min"
    return render_template('check_in.html', form=form, que=QUE, wait=wait)

@app.route("/drop_in/advisor", methods=['GET', 'POST'])
@oidc.require_login
def advisor():
    form = ReusableForm(request.form)
    if request.method == 'POST':
        if len(QUE) > 0:
            student = QUE.pop(0)
            QUE_LOGGER.info("%s checked out by %s" % (student['name'], g.user.profile.email))
            msg = "%s,%s,%s,%s" % (datetime.now().date(), student['name'], student['reason'], g.user.profile.email)
            QUE_SEEN_LOGGER.raw(msg)
        else:
            student = None
        return render_template('advisor.html', form=form, student=student, que=QUE)
    else:
        return render_template('advisor.html', form=form, student=None, que=QUE)


#######################################################
##                  OPT/CPT ROUTES                   ##
#######################################################
@app.route("/workshop", methods=['GET', 'POST'])
@oidc.require_login
def workshop():
    return render_template('cpt_opt_selection.html')

@app.route("/workshop/opt", methods=['GET', 'POST'])
@oidc.require_login
def opt_workshop():
    "appointment system. validates that a user has gone to opt appointment"
    if g.user.profile.email in CODE_DB:
        return redirect('https://calendar.google.com/calendar/selfsched?sstoken=UUxrUmkyT1FMUXMxfGRlZmF1bHR8YzBkYWVkZGQ4Njk1ZmMyMzc2YzlkMjU4ZDBlMzU2YzM')
    if request.method == 'POST':
        code = int(request.form['code'])
        valid = CODE_DB.check_code_validity(code, g.user.profile.email)
        if valid:
            return redirect('https://calendar.google.com/calendar/selfsched?sstoken=UUxrUmkyT1FMUXMxfGRlZmF1bHR8YzBkYWVkZGQ4Njk1ZmMyMzc2YzlkMjU4ZDBlMzU2YzM')
    form = OptCodeForm(request.form)
    return render_template('opt_workshop.html', form=form)

@app.route("/workshop/cpt", methods=['GET', 'POST'])
@oidc.require_login
def cpt_workshop():
    "appointment system. validates that a user has gone to cpt appointment"
    if g.user.profile.email in CODE_DB:
        return redirect('https://calendar.google.com/calendar/selfsched?sstoken=UUxrUmkyT1FMUXMxfGRlZmF1bHR8YzBkYWVkZGQ4Njk1ZmMyMzc2YzlkMjU4ZDBlMzU2YzM')
    elif request.method == 'POST':
        code = int(request.form['code'])
        valid = CODE_DB.check_code_validity(code, g.user.profile.email)
        if valid:
            return redirect('https://calendar.google.com/calendar/selfsched?sstoken=UUxrUmkyT1FMUXMxfGRlZmF1bHR8YzBkYWVkZGQ4Njk1ZmMyMzc2YzlkMjU4ZDBlMzU2YzM')
    form = OptCodeForm(request.form)
    return render_template('cpt_workshop.html', form=form)

#TODO Routes to log video completion & redirect to calender

#######################################################
##                    ADMIN ROUTES                   ##
#######################################################

@app.route("/admin", methods=['GET'])
@oidc.require_login
def admin():
    "Return the admin landing page"
    if check_rbac(g.user.profile.email):
        return render_template('admin_front_page.html')
    else:
        return render_template('main_page.html')

@app.route("/admin/manage", methods=['GET', 'POST'])
@oidc.require_login
def manage_admin():
    "Manage admin / advisors students"
    if check_rbac(g.user.profile.email):
        form = adminForm(request.form)
        if request.method == 'POST':
            ADIVSOR_DB.update({request.form['advisor']:"admin"})
        advisors = [advisor for advisor in ADIVSOR_DB]
        return render_template('advisors.html', form=form, advisors=advisors)
    else:
        return render_template('main_page.html')

@app.route("/admin/stats", methods=['GET'])
@oidc.require_login
def admin_stats():
    "Return the admin landing page"
    return render_template('stat.html')

@app.route("/admin/code_generator", methods=['GET', 'POST'])
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


@app.route("/admin/active_code", methods=['GET', 'POST'])
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

@app.route("/admin/log_mgmt", methods=['GET'])
@oidc.require_login
def logs_display():
    "Display the logs of System Check-In"
    records = QUE_SEEN_LOGGER.load()
    records.reverse()
    records = [record.split(',') for record in records]
    return render_template('log_mgmt.html', records=records)




if __name__ == "__main__":
    app.run()

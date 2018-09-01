from flask import Flask, render_template, flash, request, g, redirect
from wtforms import Form, TextField, IntegerField, TextAreaField, validators, StringField, SubmitField
from flask_oidc import OpenIDConnect
from okta import UsersClient
from datetime import datetime
from collections import Counter
import config
import thread

# local imports
from code_db import CodeSystem
from code_db import CodeDB
from opt_logger import Logger, datetime
from rbac import RbacSystem

# Configuration
okta_client = UsersClient(config.okta['account'], config.okta['token'])


CODE_DB = CodeSystem("codedb2.json")
ADIVSOR_DB = CodeSystem("advisors.json")

REASONS_COUNTER = CodeSystem("reasons.json")
REASONS_COUNTER.start = datetime.now().month
WEEKS_COUNTER = CodeDB("weeks_reasons.json")
WEEKS_COUNTER.start = datetime.now().day

QUE = []

QUE_LOGGER = Logger(filename="que_logs.log")
CODE_LOGGER = Logger(filename="code_logs.log")
RBAC_LOGGER = Logger(filename="rbac_logs.log")
QUE_SEEN_LOGGER = Logger(filename="que_seen_logs.log")
WS_LOGGER = Logger(filename="workshop_logs.log")

RBAC= RbacSystem("rbac.json")
RBAC.add_role('GSA')
RBAC.add_role('advisor', sub_roles=['GSA'])
RBAC.add_role('admin', sub_roles=['advisor'])
RBAC.add_user('bblack@scu.edu', 'admin')

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


def clear_dbs():
    today = datetime.now()
    if (WEEKS_COUNTER.start + 7) > today.day:
        WEEKS_COUNTER.clear()
        WEEKS_COUNTER.start = today.day
    if REASONS_COUNTER.start == today:
        REASONS_COUNTER.clear()
        REASONS_COUNTER.start = today.month

def nightly_purge():
    import time
    while True:
        time.sleep(360)
        if datetime.now().hour == 20:
            QUE = []

thread.start_new_thread(nightly_purge, ())


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

class adminRemoveForm(Form):
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
            if reason not in REASONS_COUNTER:
                REASONS_COUNTER.update({reason:0})
            if reason not in WEEKS_COUNTER:
                WEEKS_COUNTER.update({reason:0})
            REASONS_COUNTER.update({reason:REASONS_COUNTER[reason]+1})
            WEEKS_COUNTER.update({reason:WEEKS_COUNTER[reason]+1})
            student = {"name":name, "reason": reason}
            QUE.append(student)
        else:
            flash('Error: All the form fields are required. ')
    wait = str(len(QUE)) + " min"
    return render_template('check_in.html', form=form, que=QUE, wait=wait)

@app.route("/drop_in/advisor", methods=['GET', 'POST'])
@oidc.require_login
def advisor():
    if RBAC.check_access(g.user.profile.email, 'advisor'):
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
    render_template('main_page.html')


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
        CODE_LOGGER.info(g.user.profile.email+"entered OPT code "+ str(code)+ " status was "+ str(valid))
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
        CODE_LOGGER.info(g.user.profile.email+"entered CPT code "+ str(code)+ " status was "+ str(valid))
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
    print g.user.profile.email
    print RBAC.check_access(g.user.profile.email, 'advisor')
    if RBAC.check_access(g.user.profile.email, 'GSA'):
        return render_template('admin_front_page.html')
    else:
        return render_template('main_page.html')

@app.route("/admin/manage", methods=['GET', 'POST'])
@oidc.require_login
def manage_admin():
    "Manage admin / advisors accounts"
    form = adminForm(request.form)
    removeForm = adminRemoveForm(request.form)
    if RBAC.check_access(g.user.profile.email, 'admin'):

        if request.method == 'POST':
            if 'advisor' in request.form:
                RBAC_LOGGER.info(g.user.profile.email+ " added admin: " + request.form['advisor'])
                ADIVSOR_DB.update({request.form['advisor']:"admin"})
            else:
                try:
                    del ADIVSOR_DB[request.form['to_remove']]
                    RBAC_LOGGER.info(g.user.profile.email+ " removed admin: " + request.form['to_remove'])
                except:
                    pass
        advisors = [advisor for advisor in ADIVSOR_DB]
        return render_template('advisors.html', form=form, remove_form=removeForm, advisors=advisors)
    else:
        return render_template('admin_front_page.html')

@app.route("/admin/stats", methods=['GET'])
@oidc.require_login
def admin_stats():
    "Return the admin landing page"
    clear_dbs()
    if RBAC.check_access(g.user.profile.email, 'GSA'):
        return render_template('stat.html', weeks=WEEKS_COUNTER, years=REASONS_COUNTER)
    else:
        return render_template('admin_front_page.html')

@app.route("/admin/code_generator", methods=['GET', 'POST'])
@oidc.require_login
def appointments_admin():
    "appointment system. generate a code"
    if RBAC.check_access(g.user.profile.email, 'advisor'):
        if request.method == 'POST':
            uses = int(request.form['uses'])
            code = CODE_DB.add_code(limit=uses)
            CODE_LOGGER.info(g.user.profile.email+" generated code "+str(code)+" with "+str(uses)+" uses")
        else:
            code = None
        form = OptCodeForm(request.form)
        return render_template('code_generator.html', form=form, code=code)
    return render_template('admin_front_page.html')


@app.route("/admin/active_code", methods=['GET', 'POST'])
@oidc.require_login
def appointments_admin_codes():
    "appointment system. View codes"
    if RBAC.check_access(g.user.profile.email, 'GSA'):
        codes  = []
        for record in CODE_DB:
            print(CODE_DB[record])
            if CODE_DB[record] is True:
                pass
            elif 'limit' in CODE_DB[record]:
                CODE_DB[record].update({'code':record})
                codes.append(CODE_DB[record])
        return render_template('view_codes.html', codes=codes)
    return render_template('admin_front_page.html')

@app.route("/admin/log_mgmt", methods=['GET'])
@oidc.require_login
def logs_display():
    "Display the logs of System Check-In"
    if RBAC.check_access(g.user.profile.email, 'GSA'):
        records = QUE_SEEN_LOGGER.load()
        records.reverse()
        records = [record.split(',') for record in records]
        return render_template('log_mgmt.html', records=records)
    return render_template('admin_front_page.html')



#######################################################
##                    API ROUTES                     ##
#######################################################

@app.route("/api", methods=['GET'])
def api_menu():
    "Return the API option"
    options = [
    "appointment_stats",
    "drop_in_stats",
    ]
    return str(options)

@app.route("/api/drop_in_stats", methods=['GET'])
def api_drop_in():
    "Return the drop in statistics"

    return str(WEEKS_COUNTER)

if __name__ == "__main__":
    app.run()

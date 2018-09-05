# Santa Clara University Capstone

This project contains the source code for the Santa Clara university
GEO Capstone project.

## Design

This project builds upon the Flask Microframework http://flask.pocoo.org/.

All HTML can be found inside app/templates.

Application logic is located within app/routes.py


# Usage

First install all system pre-requisites:
```
pip install -r requirements.txt
```

To start the server:

cd to the scu-capstone/app directory

run `python routes.py`

This will start the server running on port 5000

To access the app, go to localhost:5000 to sign into the Que.
Then to access the advisor page go to localhost:5000/advisor

## Port and Host Parameters

To run the application on the servers external IP address and a non-defualt port (5000)

run the following bash commands to set up the flask enviroment to accept parameters:

```
export FLASK_APP=routes.py
python -m flask run --host=0.0.0.0 --port=80 --debug=False
```

# Etc

## Dev OKTA info:


To update the the SSO system update the configuration file `client_secrets.json` wiht you systems tokens and account.

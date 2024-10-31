"""Python Flask WebApp Auth0 integration example
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request
import requests

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")


oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

def get_token():
    url = f"https://{env.get("AUTH0_DOMAIN")}/oauth/token"
    payload = json.dumps({
        "client_id": env.get("AUTH0_CLIENT_ID"),
        "client_secret": env.get("AUTH0_CLIENT_SECRET"),
        "audience": f"https://{env.get("AUTH0_DOMAIN")}/api/v2/",
        "grant_type": "client_credentials"
    })
    headers = {
        'content-type': 'application/json',
        'Cookie': 'did=s%3Av0%3A17946aea-fcea-4be8-91ef-822cd289a9d6.nJv%2FWXH8DoS01m4KuluIxFWd1GZ102GshpCAhHEPLoE; did_compat=s%3Av0%3A17946aea-fcea-4be8-91ef-822cd289a9d6.nJv%2FWXH8DoS01m4KuluIxFWd1GZ102GshpCAhHEPLoE'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_metadata = {
            "tipo_documento": request.form.get("documentType"),
            "numero_documento": request.form.get("documentNumber"),
            "direccion": request.form.get("address"),
            "telefono": request.form.get("phone")
        }
    update_data = json.dumps({"user_metadata": user_metadata})
    url = f'https://{env["AUTH0_DOMAIN"]}/api/v2/users/{session.get("user")["userinfo"]["sub"]}'
    headers = {
            'authorization': f'Bearer {get_token()}',
            'Content-Type': 'application/json'
        }
    response = requests.request("PATCH", url, headers=headers, data=update_data)
    return render_template(
        "form.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        update_data=update_data,
        response=response
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))

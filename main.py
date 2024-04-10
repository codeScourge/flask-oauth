
from flask import Flask, redirect, request, session, current_app, render_template
from authlib.integrations.flask_client import OAuth
import requests
import dotenv
import os


# --- environs ---
dotenv.load_dotenv()
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


# --- init ---
app = Flask(__name__)
app.secret_key = "nsdjkafuz9nwe8qcroiwsufjanduhwp80"
log = lambda msg: current_app.logger.info(msg)


oauth = OAuth(app)
github = oauth.register(
    name="github",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)


# --- helpers ---
def exchange_code_for_access_token(code):
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
    }

    headers = {
        "Accept": "application/json",
    }

    response = requests.post(
        "https://github.com/login/oauth/access_token", json=payload, headers=headers
    )

    if response.status_code == 200:
        access_token = response.json()["access_token"]
        log(response.json())
        return access_token
    
    else:
        return None
    

def get_user_info(access_token):
    if access_token:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get("https://api.github.com/user", headers=headers)

        if response.status_code == 200:
            data = response.json()
            log(data)
            return data

    return None


# --- routes ---
@app.errorhandler(404)
def notFoundHandler(error):
    return redirect("/")

@app.get("/")
def indexRoute():
    return render_template("index.html")


@app.get("/home")
def homeRoute():
    username = session.get("username")
    access_token = session.get("access_token")

    if username and access_token:
        return render_template("home.html", username=username)
    
    else:
        return redirect("/authenticate")


@app.get("/authenticate")
def loginRoute():
    return github.authorize_redirect(f"{request.host_url}callback")


@app.get("/callback")
def callbackRoute():
    code = request.args.get("code")
    access_token = exchange_code_for_access_token(code)

    session["access_token"] = access_token
    user_info = get_user_info(access_token)
    session["username"] = user_info["login"]

    return redirect("/home")


@app.get("/logout")
def logoutRoute():
    session.pop("access_token")
    session.pop("username")
    return redirect("/")


# --- main ---
if __name__ == "__main__":
    app.run(debug=True, port=8080)
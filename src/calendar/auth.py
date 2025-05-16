import time
import json
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

import google_auth_oauthlib.flow


CLIENT_SECRETS_FILE = "client_secret.json"
CREDENTIALS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://localhost:8080"


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urlparse(self.path).query
        code = parse_qs(query).get("code")
        message = b"Authentication complete. You can close this window."

        if code:
            self.server.auth_code = code[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message)
        else:
            self.send_response(400)
            self.end_headers()


def get_auth_code(authorization_url: str) -> str:
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, OAuthHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    webbrowser.open(authorization_url)

    poll_timing = 5

    while not hasattr(httpd, "auth_code"):
        time.sleep(poll_timing)

    code = getattr(httpd, "auth_code")
    return code


def get_google_credentials() -> dict[str, str]:
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )

    flow.redirect_uri = REDIRECT_URI

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt='consent'
    )

    code = get_auth_code(authorization_url)
    flow.fetch_token(code=code)
    _credentials = flow.credentials

    return {
        "token": _credentials.token,
        "refresh_token": _credentials.refresh_token,
        "token_uri": _credentials.token_uri,
        "client_id": _credentials.client_id,
        "client_secret": _credentials.client_secret,
        "granted_scopes": _credentials.granted_scopes
    }


if __name__ == "__main__":
    credentials = get_google_credentials()

    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as fp:
        json.dump(credentials, fp, indent=4)

    print("Credentials are stored successfully!")

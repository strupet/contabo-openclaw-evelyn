#!/usr/bin/env python3
"""
Withings Health API Sync Tool
Synchronizes sleep, activity, and health metrics from Withings Cloud API.

Usage:
  # 1. Setup & Auth
  python3 withings_sync.py auth-url
  python3 withings_sync.py exchange --code <AUTHORIZATION_CODE>
  # OR Interactive Browser Flow:
  python3 withings_sync.py auth-server --port 8080

  # 2. Daily Sync (Fetches data & writes CSV/JSON)
  python3 withings_sync.py sync --days 7

  # 3. Check Token Status
  python3 withings_sync.py status
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "withings_config.json")
TOKENS_FILE = os.path.join(SCRIPT_DIR, "withings_tokens.json")
DATA_DIR = os.path.join(SCRIPT_DIR, "health_data", "withings")

DEFAULT_SCOPES = "user.info,user.metrics,user.activity,user.sleepevents"

def load_config():
    """Loads Withings API credentials from config file or environment variables."""
    cfg = {
        "client_id": os.getenv("WITHINGS_CLIENT_ID", ""),
        "client_secret": os.getenv("WITHINGS_CLIENT_SECRET", ""),
        "redirect_uri": os.getenv("WITHINGS_REDIRECT_URI", "http://localhost:8080/callback"),
        "scopes": os.getenv("WITHINGS_SCOPES", DEFAULT_SCOPES)
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg.update(data)
        except Exception as e:
            print(f"Warning: Could not read {CONFIG_FILE}: {e}", file=sys.stderr)
    return cfg

def save_config(cfg):
    """Saves API credentials to withings_config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"Config saved to {CONFIG_FILE}")

def load_tokens():
    """Loads OAuth tokens."""
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read {TOKENS_FILE}: {e}", file=sys.stderr)
    return None

def save_tokens(tokens):
    """Saves OAuth tokens securely."""
    tokens["updated_at"] = int(time.time())
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKENS_FILE, 0o600)
    print(f"Tokens saved to {TOKENS_FILE}")

def make_api_request(url, params=None, headers=None, data=None):
    """Utility to make HTTP requests using urllib."""
    if headers is None:
        headers = {}
    
    encoded_data = None
    if data is not None:
        if isinstance(data, dict):
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, (bytes, bytearray)):
            encoded_data = data
        elif isinstance(data, str):
            encoded_data = data.encode("utf-8")

    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}" if "?" not in url else f"{url}&{query_string}"

    req = urllib.request.Request(url, data=encoded_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"HTTP Error {e.code} for {url}: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Request failed for {url}: {e}")

def get_auth_url(config):
    """Generates OAuth2 Authorization URL."""
    if not config.get("client_id"):
        raise ValueError("client_id is missing. Please set WITHINGS_CLIENT_ID or update withings_config.json.")
    
    base_url = "https://account.withings.com/oauth2_user/authorize2"
    params = {
        "response_type": "code",
        "client_id": config["client_id"],
        "scope": config.get("scopes", DEFAULT_SCOPES),
        "redirect_uri": config["redirect_uri"],
        "state": "withings_auth_" + str(int(time.time()))
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def exchange_code(config, code):
    """Exchanges authorization code for access and refresh tokens."""
    url = "https://wbsapi.withings.net/v2/oauth2"
    payload = {
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "code": code.strip(),
        "redirect_uri": config["redirect_uri"]
    }
    res = make_api_request(url, data=payload)
    if res.get("status") != 0:
        raise RuntimeError(f"Token exchange failed: status={res.get('status')}, error={res.get('error')}")
    body = res.get("body", {})
    tokens = {
        "access_token": body.get("access_token"),
        "refresh_token": body.get("refresh_token"),
        "expires_in": body.get("expires_in", 10800),
        "expires_at": int(time.time()) + body.get("expires_in", 10800),
        "userid": body.get("userid"),
        "token_type": body.get("token_type", "Bearer"),
        "scope": body.get("scope")
    }
    save_tokens(tokens)
    return tokens

def refresh_access_token(config, tokens):
    """Refreshes the access token using the refresh token."""
    url = "https://wbsapi.withings.net/v2/oauth2"
    payload = {
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "refresh_token": tokens["refresh_token"]
    }
    res = make_api_request(url, data=payload)
    if res.get("status") != 0:
        raise RuntimeError(f"Token refresh failed: status={res.get('status')}, error={res.get('error')}")
    body = res.get("body", {})
    new_tokens = {
        "access_token": body.get("access_token"),
        "refresh_token": body.get("refresh_token"),
        "expires_in": body.get("expires_in", 10800),
        "expires_at": int(time.time()) + body.get("expires_in", 10800),
        "userid": body.get("userid", tokens.get("userid")),
        "token_type": body.get("token_type", "Bearer"),
        "scope": body.get("scope", tokens.get("scope"))
    }
    save_tokens(new_tokens)
    return new_tokens

def get_valid_access_token(config):
    """Retrieves a valid access token, refreshing if necessary."""
    tokens = load_tokens()
    if not tokens or not tokens.get("refresh_token"):
        raise RuntimeError("No tokens found. Run 'python3 withings_sync.py auth-url' or 'auth-server' first.")
    
    expires_at = tokens.get("expires_at", 0)
    # Refresh if expires in less than 5 minutes
    if time.time() > (expires_at - 300):
        print("Access token expired or expiring soon. Refreshing...", file=sys.stderr)
        tokens = refresh_access_token(config, tokens)
    return tokens["access_token"]

def fetch_sleep_summary(access_token, start_date_str, end_date_str):
    """Fetches sleep summaries between start_date and end_date."""
    url = "https://wbsapi.withings.net/v2/sleep"
    fields = (
        "total_sleep_time,total_timeinbed,asleepduration,lightsleepduration,"
        "deepsleepduration,remsleepduration,durationtosleep,durationtowakeup,"
        "wakeupcount,wakeupduration,sleep_efficiency,sleep_score,snoring,"
        "snoringepisodecount,hr_average,hr_min,hr_max,rr_average,rr_min,rr_max,"
        "breathing_disturbances_intensity,waso"
    )
    payload = {
        "action": "getsummary",
        "startdateymd": start_date_str,
        "enddateymd": end_date_str,
        "data_fields": fields
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    res = make_api_request(url, data=payload, headers=headers)
    if res.get("status") != 0:
        raise RuntimeError(f"Failed to fetch sleep summary: status={res.get('status')}, error={res.get('error')}")
    return res.get("body", {}).get("series", [])

def fetch_activity_summary(access_token, start_date_str, end_date_str):
    """Fetches daily activity summaries between start_date and end_date."""
    url = "https://wbsapi.withings.net/v2/measure"
    fields = (
        "steps,distance,elevation,calories,totalcalories,hr_average,hr_min,hr_max,"
        "hr_zone_0,hr_zone_1,hr_zone_2,hr_zone_3,sleep_duration"
    )
    payload = {
        "action": "getactivity",
        "startdateymd": start_date_str,
        "enddateymd": end_date_str,
        "data_fields": fields
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    res = make_api_request(url, data=payload, headers=headers)
    if res.get("status") != 0:
        raise RuntimeError(f"Failed to fetch activity: status={res.get('status')}, error={res.get('error')}")
    return res.get("body", {}).get("activities", [])

def fetch_measurements(access_token, start_date_ts):
    """Fetches body measurements (weight, fat ratio, etc.) since start_date timestamp."""
    url = "https://wbsapi.withings.net/v2/measure"
    payload = {
        "action": "getmeas",
        "startdate": start_date_ts,
        "category": 1
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    res = make_api_request(url, data=payload, headers=headers)
    if res.get("status") != 0:
        raise RuntimeError(f"Failed to fetch measures: status={res.get('status')}, error={res.get('error')}")
    return res.get("body", {})

def run_sync(config, days=7, output_dir=DATA_DIR):
    """Executes full synchronization of Withings health metrics."""
    os.makedirs(output_dir, exist_ok=True)
    access_token = get_valid_access_token(config)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    start_ts = int(start_date.timestamp())

    print(f"--- Synchronizing Withings data from {start_str} to {end_str} ---")

    # 1. Fetch & Save Sleep
    try:
        sleep_series = fetch_sleep_summary(access_token, start_str, end_str)
        sleep_json_path = os.path.join(output_dir, "sleep_summary.json")
        with open(sleep_json_path, "w", encoding="utf-8") as f:
            json.dump(sleep_series, f, indent=2)
        
        # Save Sleep CSV
        sleep_csv_path = os.path.join(output_dir, "sleep_summary.csv")
        with open(sleep_csv_path, "w", encoding="utf-8") as f:
            headers = [
                "date", "start_time", "end_time", "sleep_score", "duration_hours",
                "light_sleep_min", "deep_sleep_min", "rem_sleep_min", "awake_min",
                "sleep_efficiency", "hr_average", "hr_min", "hr_max", "snoring_min"
            ]
            f.write(",".join(headers) + "\n")
            for item in sleep_series:
                data = item.get("data", {})
                start_dt = datetime.fromtimestamp(item.get("startdate", 0)).strftime("%Y-%m-%d %H:%M:%S") if item.get("startdate") else ""
                end_dt = datetime.fromtimestamp(item.get("enddate", 0)).strftime("%Y-%m-%d %H:%M:%S") if item.get("enddate") else ""
                row = [
                    item.get("date", ""),
                    start_dt,
                    end_dt,
                    str(data.get("sleep_score", "")),
                    f"{(data.get('total_sleep_time', 0) / 3600):.2f}",
                    str(int(data.get("lightsleepduration", 0) / 60)),
                    str(int(data.get("deepsleepduration", 0) / 60)),
                    str(int(data.get("remsleepduration", 0) / 60)),
                    str(int(data.get("wakeupduration", 0) / 60)),
                    f"{(data.get('sleep_efficiency', 0) * 100):.1f}%" if data.get("sleep_efficiency") is not None else "",
                    str(data.get("hr_average", "")),
                    str(data.get("hr_min", "")),
                    str(data.get("hr_max", "")),
                    str(int(data.get("snoring", 0) / 60))
                ]
                f.write(",".join(row) + "\n")
        print(f"✓ Sleep: {len(sleep_series)} nights saved to {sleep_csv_path}")
    except Exception as e:
        print(f"✗ Sleep sync failed: {e}", file=sys.stderr)

    # 2. Fetch & Save Activity
    try:
        activities = fetch_activity_summary(access_token, start_str, end_str)
        activity_json_path = os.path.join(output_dir, "activity_summary.json")
        with open(activity_json_path, "w", encoding="utf-8") as f:
            json.dump(activities, f, indent=2)

        activity_csv_path = os.path.join(output_dir, "activity_summary.csv")
        with open(activity_csv_path, "w", encoding="utf-8") as f:
            headers = ["date", "steps", "distance_km", "calories", "total_calories", "elevation_m", "hr_average", "hr_min", "hr_max"]
            f.write(",".join(headers) + "\n")
            for act in activities:
                row = [
                    act.get("date", ""),
                    str(act.get("steps", 0)),
                    f"{(act.get('distance', 0) / 1000.0):.2f}",
                    str(act.get("calories", 0)),
                    str(act.get("totalcalories", 0)),
                    str(act.get("elevation", 0)),
                    str(act.get("hr_average", "")),
                    str(act.get("hr_min", "")),
                    str(act.get("hr_max", ""))
                ]
                f.write(",".join(row) + "\n")
        print(f"✓ Activity: {len(activities)} days saved to {activity_csv_path}")
    except Exception as e:
        print(f"✗ Activity sync failed: {e}", file=sys.stderr)

    # 3. Fetch & Save Measures (Weight, Body Fat)
    try:
        measures = fetch_measurements(access_token, start_ts)
        meas_json_path = os.path.join(output_dir, "measures.json")
        with open(meas_json_path, "w", encoding="utf-8") as f:
            json.dump(measures, f, indent=2)

        meas_csv_path = os.path.join(output_dir, "measures.csv")
        meas_groups = measures.get("measuregrps", [])
        with open(meas_csv_path, "w", encoding="utf-8") as f:
            headers = ["datetime", "weight_kg", "fat_ratio_pct", "muscle_mass_kg", "hydration_pct"]
            f.write(",".join(headers) + "\n")
            for grp in meas_groups:
                dt_str = datetime.fromtimestamp(grp.get("date", 0)).strftime("%Y-%m-%d %H:%M:%S")
                vals = {}
                for m in grp.get("measures", []):
                    m_type = m.get("type")
                    real_val = m.get("value", 0) * (10 ** m.get("unit", 0))
                    vals[m_type] = real_val
                
                # Type 1 = Weight (kg), Type 6 = Fat Ratio (%), Type 76 = Muscle Mass (kg), Type 77 = Hydration (%)
                w = f"{vals[1]:.2f}" if 1 in vals else ""
                f_pct = f"{vals[6]:.1f}" if 6 in vals else ""
                m_mass = f"{vals[76]:.2f}" if 76 in vals else ""
                hyd = f"{vals[77]:.1f}" if 77 in vals else ""
                f.write(f"{dt_str},{w},{f_pct},{m_mass},{hyd}\n")
        print(f"✓ Measures: {len(meas_groups)} records saved to {meas_csv_path}")
    except Exception as e:
        print(f"✗ Measures sync failed: {e}", file=sys.stderr)

    print("--- Synchronization complete! ---")

def run_auth_server(config, port=8080):
    """Starts a local HTTP server to handle OAuth redirect automatically."""
    callback_code = None

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal callback_code
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            if "code" in params:
                callback_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <html>
                <head><title>Withings Auth Successful</title></head>
                <body style="font-family:sans-serif; text-align:center; padding:50px; background:#f4f6f9;">
                    <div style="background:white; max-width:500px; margin:auto; padding:30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                        <h2 style="color:#27ae60;">✓ Withings Verknüpfung Erfolgreich!</h2>
                        <p>Der Autorisierungs-Code wurde empfangen und die Tokens werden gespeichert.</p>
                        <p style="color:#7f8c8d; font-size:14px;">Du kannst dieses Browserfenster jetzt schließen.</p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Error: Missing code parameter")

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("0.0.0.0", port), CallbackHandler)
    auth_url = get_auth_url(config)
    print("\n" + "="*70)
    print("WITHINGS OAUTH AUTHORIZATION")
    print("="*70)
    print(f"1. Öffne diesen Link im Browser:\n\n   {auth_url}\n")
    print(f"2. Warte auf Autorisierungs-Rückruf auf Port {port}...")
    print("="*70 + "\n")

    while callback_code is None:
        server.handle_request()

    print(f"✓ Autorisierungs-Code empfangen: {callback_code}")
    tokens = exchange_code(config, callback_code)
    print("✓ Initialer Token-Austausch erfolgreich abgeschlossen!")
    return tokens

def show_status(config):
    """Displays token information and validity."""
    tokens = load_tokens()
    if not tokens:
        print("Status: Keine Withings-Tokens vorhanden. Bitte Autorisierung durchführen.")
        return
    
    expires_at = tokens.get("expires_at", 0)
    now = time.time()
    remaining = expires_at - now
    
    print("=== Withings Token Status ===")
    print(f"User ID:        {tokens.get('userid')}")
    print(f"Scope:          {tokens.get('scope')}")
    print(f"Token Expiry:   {datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')} (in {int(remaining/60)} Min)")
    print(f"Refresh Token:  {'Vorhanden' if tokens.get('refresh_token') else 'Fehlt'}")
    if remaining <= 0:
        print("Status:         Abgelaufen (wird beim nächsten Sync automatisch erneuert)")
    else:
        print("Status:         Gültig")

def main():
    parser = argparse.ArgumentParser(description="Withings Health Data Sync Script")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: auth-url
    subparsers.add_parser("auth-url", help="Generate authorization URL")

    # Command: exchange
    ex_parser = subparsers.add_parser("exchange", help="Exchange authorization code for tokens")
    ex_parser.add_argument("--code", required=True, help="Authorization code from Withings redirect")

    # Command: auth-server
    srv_parser = subparsers.add_parser("auth-server", help="Run local callback server for OAuth authorization")
    srv_parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")

    # Command: sync
    sync_parser = subparsers.add_parser("sync", help="Sync health data (sleep, activity, measures)")
    sync_parser.add_argument("--days", type=int, default=7, help="Number of past days to sync (default: 7)")
    sync_parser.add_argument("--output-dir", default=DATA_DIR, help=f"Directory to store output (default: {DATA_DIR})")

    # Command: status
    subparsers.add_parser("status", help="Show current token status")

    # Command: init-config
    cfg_parser = subparsers.add_parser("init-config", help="Create or update withings_config.json")
    cfg_parser.add_argument("--client-id", required=True, help="Withings Client ID")
    cfg_parser.add_argument("--client-secret", required=True, help="Withings Client Secret")
    cfg_parser.add_argument("--redirect-uri", default="http://localhost:8080/callback", help="OAuth Redirect URI")

    args = parser.parse_args()
    config = load_config()

    if args.command == "init-config":
        new_cfg = {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "redirect_uri": args.redirect_uri,
            "scopes": DEFAULT_SCOPES
        }
        save_config(new_cfg)
    elif args.command == "auth-url":
        print(get_auth_url(config))
    elif args.command == "exchange":
        exchange_code(config, args.code)
    elif args.command == "auth-server":
        run_auth_server(config, port=args.port)
    elif args.command == "sync":
        run_sync(config, days=args.days, output_dir=args.output_dir)
    elif args.command == "status":
        show_status(config)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

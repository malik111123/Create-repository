"""Run once on your computer/phone (Python) to get TIKTOK_REFRESH_TOKEN.

    python scripts/tiktok_auth.py

1. It prints a link. Open it, log in to TikTok and press "Authorize".
2. TikTok sends you to your redirect URL; copy the `code=` value from the address bar.
3. Paste it here. The script prints the refresh token -> save it as GitHub secret TIKTOK_REFRESH_TOKEN.
"""
import secrets
import urllib.parse

import requests

key = input("TikTok client key: ").strip()
secret = input("TikTok client secret: ").strip()
redirect = input("Redirect URI (exactly as in the TikTok developer portal): ").strip()

url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
    "client_key": key, "scope": "user.info.basic,video.publish", "response_type": "code",
    "redirect_uri": redirect, "state": secrets.token_hex(8)})
print("\nOpen this link:\n" + url + "\n")
code = urllib.parse.unquote(input("Paste the code= value: ").strip())

r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
    "client_key": key, "client_secret": secret, "code": code,
    "grant_type": "authorization_code", "redirect_uri": redirect}).json()
if "refresh_token" in r:
    print("\nTIKTOK_REFRESH_TOKEN =", r["refresh_token"])
else:
    print("Error:", r)

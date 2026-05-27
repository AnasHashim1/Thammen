"""Phase 0 probe — Heroku dyno egress IP (single point estimate)."""
import urllib.request, json

r = urllib.request.urlopen('https://api.ipify.org?format=json', timeout=10)
print(json.loads(r.read())['ip'])

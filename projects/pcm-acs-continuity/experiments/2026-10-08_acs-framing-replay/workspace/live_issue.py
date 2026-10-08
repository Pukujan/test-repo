"""Read the owning GitHub issue and all current comments; read-only, uncached."""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen

BASE = "https://api.github.com/repos/Pukujan/test-repo/issues/8"
headers = {"Accept": "application/vnd.github+json", "User-Agent": "pcm-acs-lab/0.1", "Cache-Control": "no-cache"}
token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if token:
    headers["Authorization"] = "Bearer " + token

def get(url):
    with urlopen(Request(url, headers=headers), timeout=15) as resp:
        return json.load(resp)

issue = get(BASE)
print(json.dumps({"url":issue.get("html_url"),"state":issue.get("state"),"updated_at":issue.get("updated_at"),
                  "title":issue.get("title"),"body":issue.get("body")},indent=2))
page = 1
while True:
    comments = get(BASE+f"/comments?per_page=100&page={page}")
    for c in comments:
        print(json.dumps({"url":c.get("html_url"),"created_at":c.get("created_at"),
                          "updated_at":c.get("updated_at"),"author":(c.get("user") or {}).get("login"),
                          "body":c.get("body")},indent=2))
    if len(comments)<100:
        break
    page+=1

import json
import os
import smtplib
import urllib.request
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

API = "https://api.github.com"
TS = "%Y-%m-%dT%H:%M:%SZ"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "oss-bug-notifier"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def parse(ts):
    return datetime.strptime(ts, TS).replace(tzinfo=timezone.utc)


def new_issues(repo, since):
    found = []
    for page in range(1, 6):
        batch = get(f"{API}/repos/{repo}/issues?state=open&sort=created&direction=desc&per_page=100&page={page}")
        for issue in batch:
            if parse(issue["created_at"]) <= since:
                return found
            found.append(issue)
        if len(batch) < 100:
            break
    return found


def wanted(issue, labels):
    if "pull_request" in issue or issue["assignee"]:
        return False
    if "*" in labels:
        return True
    names = [l["name"].lower() for l in issue["labels"]]
    return any(want.lower() in name for want in labels for name in names)


def label_text(issue):
    return ", ".join(l["name"] for l in issue["labels"]) or "no labels"


def build_email(report, config):
    total = sum(len(v) for v in report.values())
    subject = f"[OSS] {total} new issue{'s' * (total > 1)}: " + ", ".join(f"{r.split('/')[1]} {len(v)}" for r, v in report.items())
    lines = []
    for repo, issues in report.items():
        lines.append(f"========== {repo} ==========")
        if config["repos"][repo].get("note"):
            lines.append(f"NOTE: {config['repos'][repo]['note']}\n")
        for i in issues:
            preview = " ".join((i["body"] or "").split())[:400]
            lines.append(f"#{i['number']} {i['title']}")
            lines.append(f"[{label_text(i)}] opened {i['created_at']}")
            lines.append(i["html_url"])
            if preview:
                lines.append(f"Preview: {preview}")
            lines.append("")
    return subject, "\n".join(lines)


def send(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["GMAIL_USER"]
    msg["To"] = os.environ.get("TO_EMAIL") or os.environ["GMAIL_USER"]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
        s.send_message(msg)


def main():
    config = json.load(open("config.json"))
    try:
        state = json.load(open("state.json"))
    except FileNotFoundError:
        state = {}
    now = datetime.now(timezone.utc)
    report = {}
    for repo, settings in config["repos"].items():
        since = parse(state[repo]) if repo in state else now - timedelta(days=1)
        try:
            issues = new_issues(repo, since)
        except Exception as e:
            print(f"{repo}: {e}")
            continue
        state[repo] = max([i["created_at"] for i in issues], default=since.strftime(TS))
        hits = [i for i in issues if wanted(i, settings["labels"])]
        if hits:
            report[repo] = hits

    if report:
        subject, body = build_email(report, config)
        if os.environ.get("DRY_RUN"):
            print(subject, body, sep="\n\n")
        else:
            send(subject, body)
    json.dump(state, open("state.json", "w"), indent=2)
    print(f"Checked {len(config['repos'])} repos, {sum(len(v) for v in report.values())} new issues reported")


if __name__ == "__main__":
    main()

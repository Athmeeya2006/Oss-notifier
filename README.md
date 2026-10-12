# OSS bug notifier

Checks GitHub repos every 15 minutes and emails one digest of newly opened, unassigned issues, each with a short preview of the issue text.

## Setup (about 10 minutes)

1. **Create a public GitHub repo** named `oss-notifier` (public means unlimited free Actions minutes; a private repo running every 15 minutes would exceed the 2000 free minutes a month).
2. **Upload the files**: upload `notify.py`, `config.json` and `README.md`. Then Add file > Create new file, name it `.github/workflows/notify.yml`, paste the workflow contents, and commit (drag and drop often skips hidden folders).
3. **Create a Gmail app password**: turn on 2-Step Verification in your Google Account, go to myaccount.google.com/apppasswords, create one named "notifier", and copy the 16-character password.
4. **Add repo secrets**: repo Settings > Secrets and variables > Actions > New repository secret:
   - `GMAIL_USER`: your Gmail address
   - `GMAIL_APP_PASSWORD`: the 16-character app password
   - `TO_EMAIL`: where alerts go (optional, defaults to `GMAIL_USER`)
5. **Allow the workflow to save state**: Settings > Actions > General > Workflow permissions > "Read and write permissions" > Save.
6. **Test it**: Actions tab > enable workflows if asked > "OSS bug notifier" > Run workflow. The first run emails issues from the last 24 hours; later runs only new ones.

## config.json

Each repo has:
- `labels`: `["*"]` reports every new issue; `["good first issue", "bug"]` reports issues whose labels contain any of those words
- `note` (optional): a line printed above that repo's issues in the email

## Troubleshooting

Open the failed run in the Actions tab and read the log.
- `SMTPAuthenticationError`: wrong app password or `GMAIL_USER`
- push "Permission denied": step 5 not saved
- `HTTP Error 404` for a repo: repo name misspelled in `config.json`

GitHub often delays scheduled runs by 5 to 20 minutes, and pauses scheduled workflows in repos inactive for 60 days (state commits count as activity). Local test without emailing: `DRY_RUN=1 python3 notify.py`

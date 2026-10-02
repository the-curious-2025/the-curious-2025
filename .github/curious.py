# Checks an issue that claims to have found the flag.
# The proof is sha256("<flag>:<username>") of whoever opened it, so a
# solved issue doesn't give the answer away to anyone else. It comes from
# the issue form, or the title for anyone who opens a plain issue.

import datetime
import hashlib
import os
import re
import subprocess
import sys

START = "<!-- curious-ones:start -->"
END = "<!-- curious-ones:end -->"

text = os.environ["TITLE"] + " " + os.environ.get("BODY", "")
login = os.environ["LOGIN"]
number = os.environ["NUMBER"]
flag = os.environ.get("FLAG", "")


def gh(*args):
    subprocess.run(["gh", "issue", *args, number], check=True)


def git(*args):
    subprocess.run(["git", *args], check=True)


# not a submission, leave the issue alone
found = re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", text)
if not found:
    sys.exit(0)
proof = found.group(0).lower()

if not flag:
    sys.exit("CURIOUS_FLAG secret is missing, leaving the issue open")

if not re.fullmatch(r"[A-Za-z0-9-]+", login):
    sys.exit(f"unexpected login: {login!r}")

valid = {hashlib.sha256(f"{flag}:{name}".encode()).hexdigest() for name in (login, login.lower())}
if proof not in valid:
    gh("edit", "--title", "not quite")
    gh("comment", "--body", "Not quite. The username part has to be yours, exactly as it is on GitHub.")
    gh("close", "--reason", "not planned")
    sys.exit(0)

readme = open("README.md", encoding="utf-8").read()
head, rest = readme.split(START)
block, tail = rest.split(END)
entries = [line for line in block.strip().splitlines() if re.match(r"\d+\. ", line)]

if any(f"github.com/{login.lower()})" in line.lower() for line in entries):
    gh("edit", "--title", f"@{login} found the flag")
    gh("comment", "--body", "You're already on the list.")
    gh("close", "--reason", "completed")
    sys.exit(0)

today = datetime.date.today().isoformat()
entries.append(f"{len(entries) + 1}. [@{login}](https://github.com/{login}) &nbsp;<sub>{today}</sub>")
open("README.md", "w", encoding="utf-8").write(f"{head}{START}\n" + "\n".join(entries) + f"\n{END}{tail}")

git("config", "user.name", "github-actions[bot]")
git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
git("commit", "-am", f"@{login} found the flag")
for attempt in range(3):
    if subprocess.run(["git", "push"]).returncode == 0:
        break
    git("pull", "--rebase")
else:
    sys.exit("push failed")

gh("edit", "--title", f"@{login} found the flag")
gh("comment", "--body", f"You found it. You're #{len(entries)} on the list.")
gh("close", "--reason", "completed")

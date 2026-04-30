"""
tests/sample_code/mixed_issues.py
-----------------------------------
Sample file with both security vulnerabilities AND quality issues.
Represents realistic "real-world" code that has grown organically
without proper review processes.

Used as the comprehensive end-to-end test case.
"""

import os
import hashlib
import sqlite3


# Hardcoded credentials (security issue)
DB_PASSWORD = "admin123"
API_KEY = "sk-prod-hardcoded-key-xyz"


def get_user(username):
    """Fetch a user from the database."""
    # SQL injection vulnerability — string concatenation in query
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result


def authenticate(u, p):
    # Short param names, no type hints, insecure hash
    h = hashlib.md5(p.encode()).hexdigest()
    stored = get_user(u)
    if stored:
        if stored[2] == h:
            if stored[3] == "active":
                if stored[4] != "banned":
                    return True
    return False


def run_report(report_name, output_dir):
    """Generate a report by running a shell command."""
    # Shell injection: os.system with unsanitised input
    os.system(f"generate_report.sh {report_name} > {output_dir}/out.txt")


def process_records(records):
    # No docstring, complex nested logic, magic numbers
    results = []
    for r in records:
        try:
            val = r["value"]
            if val > 0:
                if val < 1000:
                    if val % 2 == 0:
                        results.append(val * 1.5 + 25)
                    else:
                        results.append(val * 0.75 - 10)
                elif val >= 1000:
                    results.append(val / 100)
            else:
                results.append(-1)
        except:  # bare except
            pass
    return results


def save_config(key, value, filepath):
    """Write a config key=value to a file."""
    # No validation, no type hints
    with open(filepath, "a") as f:
        f.write(key + "=" + value + "\n")


class userManager:     # bad class name
    users = []         # mutable class-level variable (shared across instances)

    def addUser(self, name, pw):
        # Stores plaintext password; bad method name
        entry = {"name": name, "password": pw}
        userManager.users.append(entry)

    def getAll(self):
        return userManager.users

    def deleteUser(self, name):
        for i in range(len(userManager.users)):
            if userManager.users[i]["name"] == name:
                userManager.users.pop(i)
                break


if __name__ == "__main__":
    mgr = userManager()
    mgr.addUser("alice", "password123")
    print(mgr.getAll())

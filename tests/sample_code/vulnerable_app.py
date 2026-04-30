"""
tests/sample_code/vulnerable_app.py
-------------------------------------
Sample file with intentional HIGH-severity security vulnerabilities.
Used for demonstrating the Security Audit Agent.

DO NOT deploy this code. It is intentionally insecure for testing purposes.
"""

import os
import pickle
import subprocess

# B105 – Hardcoded credentials
password = "supersecret123"
secret = "my_api_token_abc"
token = "ghp_hardcodedtoken"

DEBUG = True  # B501 – Debug mode enabled


def login(username, password):
    """Authenticate user — intentionally insecure."""
    # B608 – SQL injection risk (string formatting in query)
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)
    print("Executing:", query)
    return query


def run_command(user_input):
    """Run a system command — shell injection risk."""
    # B605 – os.system with user input
    os.system("ls " + user_input)
    # B602 – shell=True subprocess
    subprocess.call("echo " + user_input, shell=True)


def load_data(filepath):
    """Load serialised data — pickle deserialization risk."""
    # B301 – pickle.loads
    with open(filepath, "rb") as f:
        return pickle.loads(f.read())


def dangerous_eval(expression):
    """Evaluate arbitrary expression — code execution risk."""
    # B307 – eval()
    return eval(expression)


def hash_password(pw):
    """Hash a password using a weak algorithm."""
    import hashlib
    # B303 – MD5
    return hashlib.md5(pw.encode()).hexdigest()


if __name__ == "__main__":
    result = dangerous_eval("1 + 1")
    print(result)

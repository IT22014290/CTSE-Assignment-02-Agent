"""
tests/sample_code/bad_quality_code.py
---------------------------------------
Sample file with intentional code quality issues.
Used for demonstrating the Code Analysis Agent.

Issues deliberately introduced:
- Very long functions (high cognitive complexity)
- Magic numbers
- Bare except clauses
- Poor variable naming
- No type hints
- Deeply nested code
- No docstrings
- Duplicate code blocks
"""


x = 42          # magic number, no context
y = 3.14159     # magic number
z = 1000        # magic number


def a(b, c, d):
    # No docstring, single-letter names
    r = []
    for i in range(b):
        for j in range(c):
            for k in range(d):
                if i > 0:
                    if j > 0:
                        if k > 0:
                            if (i + j + k) % 2 == 0:
                                r.append(i * j * k)
    return r


def calculate(data):
    # No docstring, bare except, magic numbers
    total = 0
    count = 0
    try:
        for item in data:
            if item > 0:
                total = total + item
                count = count + 1
            elif item == -999:  # magic number used as sentinel
                break
        avg = total / count
        result = avg * 1.15 * 0.9   # unexplained coefficients
        if result > 100:
            result = 100
        if result > 50:
            status = "high"
        elif result > 25:
            status = "medium"
        else:
            status = "low"
        return result, status
    except:   # bare except — swallows all errors silently
        return 0, "unknown"


def process_user(u, p, e, a, ph, c):
    # Too many parameters, no docstring, poor names
    if u == None:
        return False
    if p == None:
        return False
    if e == None:
        return False
    if a == None:
        return False
    # Duplicate validation blocks — should be a loop
    if len(u) < 3:
        return False
    if len(p) < 8:
        return False
    if "@" not in e:
        return False
    if len(ph) != 10:
        return False
    result = {
        "username": u,
        "password": p,     # storing plaintext password — also a security smell
        "email": e,
        "address": a,
        "phone": ph,
        "country": c
    }
    return result


def do_stuff(lst):
    # Meaningless name, no docstring
    new_lst = []
    for i in range(len(lst)):      # should use enumerate
        if lst[i] != None:         # should use 'is not None'
            new_lst.append(lst[i])
    return new_lst


def another_function(n):
    # Recursive function with no base-case guard
    return n * another_function(n - 1)


class data_processor:      # class name not PascalCase
    def __init__(self):
        self.Data = []     # attribute name not snake_case

    def Add(self, item):   # method name not snake_case
        self.Data.append(item)

    def Process(self):     # method name not snake_case
        results = []
        for d in self.Data:
            # Duplicate of calculate() logic above
            total = 0
            count = 0
            try:
                for item in d:
                    total += item
                    count += 1
                results.append(total / count)
            except:
                results.append(0)
        return results

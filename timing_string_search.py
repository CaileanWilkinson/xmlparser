import random
import re
from timeit import timeit
import string

print("GENERATING")
m_string_index = -1
r1_string_index = -1
r2_string_index = -1
f_string_index = -1

strings = [
    ''.join(random.choice(string.ascii_letters + string.digits) for x in range(1000))
    for string_index in range(0, 10_001)
]

print("DONE GENERATING")

def manual():
    global m_string_index
    m_string_index += 1
    string = strings[m_string_index]
    index = None
    for i, x in enumerate(string):
        if x in "1234":
            index = i
            break

def regex1(reg):
    global r1_string_index
    r1_string_index += 1
    string = strings[r1_string_index]
    match = reg.search(string)
    if match:
        index = match.start()

def regex2():
    global r2_string_index
    r2_string_index += 1
    string = strings[r2_string_index]
    match = re.search("[1234]", string)
    if match:
        index = match.start()

def find():
    global f_string_index
    f_string_index += 1
    string = strings[f_string_index]
    index = min(string.find("1"), string.find("2"), string.find("3"), string.find("4"))


setup = f"""
from __main__ import manual, regex1, regex2, find, strings
import re
m_string_index = -1
r1_string_index = -1
r2_string_index = -1
f_string_index = -1
reg = re.compile("[1234]")
"""

print("----")

print(f"MANUAL: {timeit('manual()', setup, number=10_000)}")
print(f"REGEX1: {timeit('regex1(reg)', setup, number=10_000)}")
print(f"REGEX2: {timeit('regex2()', setup, number=10_000)}")
print(f"FIND: {timeit('find()', setup, number=10_000)}")

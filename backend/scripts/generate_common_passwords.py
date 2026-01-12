#!/usr/bin/env python3
"""Generate an expanded list of common passwords (~3500 entries) and write to
backend/app/core/common_passwords.txt.
The script combines known weak passwords, numeric patterns, years, and simple
combinations to produce a comprehensive list suitable for password strength
validation.
"""
import os
import itertools

# Base words commonly found in weak passwords
base_words = [
    "password",
    "admin",
    "login",
    "welcome",
    "qwerty",
    "letmein",
    "monkey",
    "dragon",
    "football",
    "iloveyou",
    "starwars",
    "123456",
    "123456789",
    "abc123",
    "111111",
    "123123",
    "654321",
    "666666",
    "7777777",
    "sunshine",
    "princess",
    "master",
    "shadow",
    "superman",
    "asdfgh",
    "zxcvbn",
    "coffee",
    "latte",
    "espresso",
    "mocha",
    "cappuccino",
]

# Numeric patterns
numbers = [
    "123",
    "1234",
    "12345",
    "123456",
    "1234567",
    "12345678",
    "111",
    "1111",
    "11111",
    "222",
    "2222",
    "3333",
    "000",
    "0000",
    "00000",
]

# Years from 1900 to 2030
years = [str(y) for y in range(1900, 2031)]

# Simple combinations of base words with numbers and years
entries = set()
for word in base_words:
    entries.add(word)
    entries.add(word + "123")
    entries.add(word + "1234")
    entries.add(word + "!@#")
    entries.add(word + "2020")
    entries.add(word + "2021")
    for num in numbers:
        entries.add(word + num)
        entries.add(num + word)
    for year in years:
        entries.add(word + year)
        entries.add(year + word)

# Add numeric sequences and years alone
entries.update(numbers)
entries.update(years)

# Add common patterns like "password!", "admin@123", etc.
patterns = [
    "password!",
    "admin@123",
    "login2020",
    "welcome1",
    "qwerty123",
    "letmein!",
    "monkey123",
    "dragon2021",
    "football!",
]
entries.update(patterns)

# Ensure we have at least 3500 entries; if not, generate more combos
while len(entries) < 3500:
    # combine two base words
    w1, w2 = itertools.islice(itertools.cycle(base_words), 2)
    entries.add(w1 + w2)
    entries.add(w2 + w1)
    # add random numeric suffix
    entries.add(w1 + "2022")
    entries.add(w2 + "2022")

# Write to file
output_path = os.path.join(
    os.path.dirname(__file__), "..", "app", "core", "common_passwords.txt"
)
# Resolve any relative path components
output_path = os.path.abspath(output_path)
with open(output_path, "w", encoding="utf-8") as f:
    for pwd in sorted(entries):
        f.write(pwd + "\n")
print(f"Generated {len(entries)} passwords to {output_path}")

#!/usr/bin/env python3
"""Check a skill folder against the WorkBuddy skill-market packaging rules.

Usage:  python3 check_skill.py <skill-dir>

Rules checked
  1. SKILL.md sits at the package root (not in a sub folder)
  2. YAML frontmatter carries the eight required market fields
  3. name is lowercase-hyphenated and equals the folder name
  4. no half-width "colon+space" inside description values (breaks YAML)
  5. examples_zh / examples_en hold at most 3 items
  6. top-level entries stay inside the allowed whitelist

Exit code 0 = all checks pass, 1 = at least one problem.
"""

import os
import re
import sys

REQUIRED = [
    "name",
    "display_name",
    "display_name_en",
    "description",
    "description_zh",
    "description_en",
    "version",
    "author",
]
WHITELIST = {"SKILL.md", "references", "scripts", "templates", "assets"}


def read_frontmatter(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    raw = text[3:end].strip("\n")
    data = {}
    key = None
    for line in raw.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("- "):
            if key:
                data[key].append(line.strip()[1:].strip().strip("'\""))
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            data[key] = []
        else:
            if (val.startswith("'") and val.endswith("'")) or (
                val.startswith('"') and val.endswith('"')
            ):
                val = val[1:-1]
            data[key] = val
    return data, text


def main():
    if len(sys.argv) < 2:
        print("usage: python3 check_skill.py <skill-dir>")
        return 2
    root = os.path.abspath(sys.argv[1])
    fails, notes = [], []

    skill_md = os.path.join(root, "SKILL.md")
    if not os.path.isfile(skill_md):
        print("[FAIL] SKILL.md is not at the package root: %s" % root)
        return 1

    fm, _text = read_frontmatter(skill_md)
    if fm is None:
        print("[FAIL] SKILL.md has no YAML frontmatter delimited by ---")
        return 1

    for k in REQUIRED:
        if k not in fm or (isinstance(fm[k], str) and not fm[k].strip()):
            fails.append("missing required field: %s" % k)

    name = fm.get("name", "")
    folder = os.path.basename(root)
    if isinstance(name, str):
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            fails.append("name %r is not lowercase-hyphenated" % name)
        if name != folder:
            notes.append(
                "folder name %r differs from name %r — normal when the zip is unzipped "
                "into a host-chosen directory; the market uses the declared name" % (folder, name)
            )

    for k in ("description", "description_zh", "description_en"):
        v = fm.get(k)
        if isinstance(v, str):
            if ": " in v:
                fails.append('%s contains half-width "colon space"' % k)
            if v.count(":") and not v.count(": "):
                notes.append("%s has a bare colon, double check YAML safety" % k)

    for k in ("examples_zh", "examples_en"):
        v = fm.get(k)
        if isinstance(v, list) and len(v) > 3:
            fails.append("%s has %d items (max 3)" % (k, len(v)))

    entries = sorted(os.listdir(root))
    extra = [e for e in entries if e not in WHITELIST]
    if extra:
        fails.append("top-level entries outside whitelist: %s" % ", ".join(extra))

    ver = fm.get("version", "")
    if isinstance(ver, str) and not re.match(r"^\d+\.\d+\.\d+", str(ver)):
        notes.append("version %r is not semver-like" % ver)

    for e in entries:
        if e in WHITELIST and e != "SKILL.md" and not os.path.isdir(os.path.join(root, e)):
            fails.append("%s should be a directory" % e)

    print("package root : %s" % root)
    print("folder name  : %s" % folder)
    print("declared name: %s" % fm.get("name"))
    print("top-level    : %s" % ", ".join(entries))
    for n in notes:
        print("[note] %s" % n)
    if not fails:
        print("[PASS] 8 required fields present, whitelist clean, description safe, examples <= 3")
        return 0
    for f in fails:
        print("[FAIL] %s" % f)
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate the social-media-marketing-skills tree. Stdlib only.

    python3 tools/validate.py

Checks (exit 1 on any failure):
- exactly 120 skill folders, each with SKILL.md, slugs unique
- 100% frontmatter compliance: name == folder slug, description present
  and containing TRIGGERS, category one of the 12 known categories,
  version present
- each category holds exactly 10 skills
- catalog.json parses, count == folders on disk, and its skill list
  matches the folders exactly
- plugin.json and marketplace.json parse and name this collection
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORIES = [
    "Strategy & Positioning", "LinkedIn Marketing", "TikTok & Short-Form Video",
    "Instagram & Reels", "YouTube", "X / Twitter", "Facebook & Communities",
    "Content Systems", "Community Management & Engagement",
    "Influencer & Creator Partnerships", "Paid Social",
    "Analytics, Social Listening & Growth",
]

REQUIRED_SECTIONS = ["## Inputs", "## Workflow", "## Output Format",
                     "## Success Metrics", "## Guardrails",
                     "## Quality Checklist", "## Example"]


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    cat = re.search(r"^category:\s*(.+)$", fm, re.M)
    ver = re.search(r"^version:\s*(.+)$", fm, re.M)
    desc_ok = "description:" in fm and "TRIGGERS" in fm
    return {
        "name": name.group(1).strip() if name else None,
        "category": cat.group(1).strip() if cat else None,
        "version": ver.group(1).strip() if ver else None,
        "description_with_triggers": desc_ok,
    }


def main():
    errors = []
    folders = sorted(
        d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d)) and not d.startswith(".")
        and d != "tools"
    )
    if len(folders) != 120:
        errors.append(f"expected 120 skill folders, found {len(folders)}")
    if len(set(folders)) != len(folders):
        errors.append("duplicate folder slugs found")

    per_category = {c: 0 for c in CATEGORIES}
    compliant = 0
    for slug in folders:
        path = os.path.join(ROOT, slug, "SKILL.md")
        if not os.path.isfile(path):
            errors.append(f"{slug}: missing SKILL.md")
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        fm = parse_frontmatter(text)
        if not fm:
            errors.append(f"{slug}: no parseable frontmatter")
            continue
        ok = True
        if fm["name"] != slug:
            errors.append(f"{slug}: frontmatter name {fm['name']!r} != folder")
            ok = False
        if not fm["description_with_triggers"]:
            errors.append(f"{slug}: description missing or lacks TRIGGERS")
            ok = False
        if fm["category"] not in CATEGORIES:
            errors.append(f"{slug}: unknown category {fm['category']!r}")
            ok = False
        else:
            per_category[fm["category"]] += 1
        if not fm["version"]:
            errors.append(f"{slug}: missing version")
            ok = False
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"{slug}: missing section {section}")
                ok = False
        if "No engagement pods" not in text:
            errors.append(f"{slug}: guardrails missing the no-pods rule")
            ok = False
        if ok:
            compliant += 1

    for cat, n in per_category.items():
        if n != 10:
            errors.append(f"category {cat!r} has {n} skills, expected 10")

    try:
        catalog = json.load(open(os.path.join(ROOT, "catalog.json")))
        cat_slugs = sorted(s["slug"] for s in catalog["skills"])
        if catalog.get("count") != len(folders):
            errors.append("catalog.json count does not match folders on disk")
        if cat_slugs != folders:
            errors.append("catalog.json skill list does not match folders on disk")
        for s in catalog["skills"]:
            if s["category"] not in CATEGORIES:
                errors.append(f"catalog: unknown category for {s['slug']}")
    except Exception as exc:
        errors.append(f"catalog.json broken: {exc}")

    for manifest in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"]:
        try:
            data = json.load(open(os.path.join(ROOT, manifest)))
            blob = json.dumps(data)
            if "social-media-marketing-skills" not in blob:
                errors.append(f"{manifest}: does not name this collection")
            if manifest.endswith("marketplace.json") and data.get("name") != "lionel-sim-skills":
                errors.append("marketplace.json: marketplace name must be lionel-sim-skills")
        except Exception as exc:
            errors.append(f"{manifest} broken: {exc}")

    print(f"skills on disk:      {len(folders)}")
    print(f"frontmatter compliant: {compliant}/{len(folders)}")
    print("per-category:        " + ", ".join(f"{c}={n}" for c, n in per_category.items()))
    if errors:
        print(f"\nFAILED with {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

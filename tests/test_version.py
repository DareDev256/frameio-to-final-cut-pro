"""One version, one name: the release carries both in more than one file.

A version bumped in pyproject.toml but not in server.json ships a registry
entry that disagrees with PyPI; a project URL left on the old repository
name sends PyPI and registry readers to a redirect, or (for the website) to
a 404 (the repository was renamed to frameio-to-final-cut-pro on
2026-11-15).
"""
import json
import re
from pathlib import Path

import cutreview

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/DareDev256/frameio-to-final-cut-pro"
SITE = "https://daredev256.github.io/frameio-to-final-cut-pro/"


def _pyproject():
    """The two pyproject fields these tests read. tomllib is 3.11+ and this
    package supports 3.10, so read them with a pattern, not a TOML parser."""
    text = (ROOT / "pyproject.toml").read_text()
    version = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M).group(1)
    block = re.search(r"^\[project\.urls\]\n(.*?)(?:^\[|\Z)", text, re.M | re.S).group(1)
    urls = dict(re.findall(r'^(\w+)\s*=\s*"([^"]+)"', block, re.M))
    return {"project": {"version": version, "urls": urls}}


def test_every_version_location_agrees():
    server = json.loads((ROOT / "server.json").read_text())
    versions = {
        "pyproject.toml": _pyproject()["project"]["version"],
        "cutreview.__version__": cutreview.__version__,
        "server.json version": server["version"],
        "server.json package": server["packages"][0]["version"],
    }
    assert len(set(versions.values())) == 1, versions


def test_project_urls_use_the_new_names():
    urls = _pyproject()["project"]["urls"]
    assert urls["Homepage"] == SITE
    assert all(u.startswith((REPO, SITE)) for u in urls.values()), urls
    server = json.loads((ROOT / "server.json").read_text())
    assert server["repository"]["url"] == REPO
    assert server["websiteUrl"] == SITE


def test_no_old_repository_link_is_left_in_what_ships():
    old = re.compile(r"github\.com/DareDev256/cutreview|github\.io/cutreview|DareDev256/cutreview/")
    shipped = [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / "server.json",
               *sorted((ROOT / "docs").glob("*.html")), ROOT / "docs" / "llms.txt", ROOT / "docs" / "sitemap.xml"]
    hits = [f"{p.name}: {m.group(0)}" for p in shipped for m in old.finditer(p.read_text())]
    assert hits == []

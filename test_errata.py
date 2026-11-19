#!/usr/bin/env python3
"""Fixtures for errata: a receipt is only as honest as its commit resolution."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build

REAL_REPO = os.environ.get("ERRATA_REPO", "/opt/data/soul-repo")


def mk(sha, before="I was wrong", after="the truth"):
    return {"commit": sha, "before": before, "after": after,
            "category": "test", "id": "fixture", "note": "", "date": "1999-01-01"}


def test_real_commit_resolves():
    ok, full, date, subject = build.resolve_commit(REAL_REPO, "fd041a9")
    assert ok and len(full) == 40 and date.startswith("2026-"), (ok, full, date, subject)
    print("PASS real commit resolves with git-supplied date/subject")


def test_bogus_commit_unverified():
    ok, full, date, subject = build.resolve_commit(REAL_REPO, "deadbeefdeadbeef")
    assert not ok
    print("PASS bogus commit does not resolve")


def test_invalid_sha_chars_rejected():
    ok, *_ = build.resolve_commit(REAL_REPO, "not-a-sha!!")
    assert not ok
    print("PASS invalid sha characters rejected before git")


def test_git_metadata_overrides_handwritten_date():
    r = build.verify({"corrections": [mk("fd041a9")]}, REAL_REPO)
    it = r["items"][0]
    assert it["verified"] and it["date"] != "1999-01-01", it
    print("PASS handwritten date overwritten by git date")


def test_broken_receipt_flips_verdict():
    good = build.verify({"corrections": [mk("fd041a9")]}, REAL_REPO)
    assert good["verdict"] == "PASS", good
    bad = build.verify({"corrections": [mk("fd041a9"), mk("0000000")]}, REAL_REPO)
    assert bad["verdict"] == "FAIL" and len(bad["bad"]) == 1, bad
    print("PASS one broken receipt flips whole verdict to FAIL")


def test_missing_content_flagged():
    r = build.verify({"corrections": [mk("fd041a9", before="", after="x")]}, REAL_REPO)
    assert r["verdict"] == "FAIL" and r["items"][0]["verified"], r
    print("PASS empty before-text flagged even though commit is real")


def test_category_counts():
    d = {"corrections": [mk("fd041a9"), dict(mk("e4d30af"), category="identity")]}
    r = build.verify(d, REAL_REPO)
    assert r["categories"] == {"test": 1, "identity": 1}, r["categories"]
    print("PASS category counts derived from data")


def test_render_escapes_html():
    r = build.verify({"corrections": [mk("fd041a9", before="<script>x</script>")]}, REAL_REPO)
    out = build.render(r, {"repo": "https://example.com"})
    assert "<script>x</script>" not in out and "&lt;script&gt;" in out
    print("PASS HTML in data escaped in rendered output")


def test_empty_ledger_fails():
    r = build.verify({"corrections": []}, REAL_REPO)
    assert r["verdict"] == "FAIL"
    print("PASS empty ledger fails (no green on no evidence)")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print("ALL %d FIXTURES PASS" % len(tests))

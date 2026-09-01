#!/usr/bin/env python3
"""Parse official FL/TX/NY mold license extracts into JSON. No invented names."""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"
RETRIEVED = "2026-09-01"

FL_FIELDS = [
    "board",
    "occ",
    "name",
    "dba",
    "class_code",
    "addr1",
    "addr2",
    "addr3",
    "city",
    "state",
    "zip",
    "county_code",
    "license",
    "primary_status",
    "secondary_status",
    "orig_date",
    "effective",
    "expiration",
    "blank",
    "renewal",
    "alt_lic",
    "ce_exempt",
]

FL_COUNTY = {
    "11": "Alachua",
    "12": "Baker",
    "13": "Bay",
    "14": "Bradford",
    "15": "Brevard",
    "16": "Broward",
    "17": "Calhoun",
    "18": "Charlotte",
    "19": "Citrus",
    "20": "Clay",
    "21": "Collier",
    "22": "Columbia",
    "23": "Miami-Dade",
    "24": "DeSoto",
    "25": "Dixie",
    "26": "Duval",
    "27": "Escambia",
    "28": "Flagler",
    "29": "Franklin",
    "30": "Gadsden",
    "31": "Gilchrist",
    "32": "Glades",
    "33": "Gulf",
    "34": "Hamilton",
    "35": "Hardee",
    "36": "Hendry",
    "37": "Hernando",
    "38": "Highlands",
    "39": "Hillsborough",
    "40": "Holmes",
    "41": "Indian River",
    "42": "Jackson",
    "43": "Jefferson",
    "44": "Lafayette",
    "45": "Lake",
    "46": "Lee",
    "47": "Leon",
    "48": "Levy",
    "49": "Liberty",
    "50": "Madison",
    "51": "Manatee",
    "52": "Marion",
    "53": "Martin",
    "54": "Monroe",
    "55": "Nassau",
    "56": "Okaloosa",
    "57": "Okeechobee",
    "58": "Orange",
    "59": "Osceola",
    "60": "Palm Beach",
    "61": "Pasco",
    "62": "Pinellas",
    "63": "Polk",
    "64": "Putnam",
    "65": "St. Johns",
    "66": "St. Lucie",
    "67": "Santa Rosa",
    "68": "Sarasota",
    "69": "Seminole",
    "70": "Sumter",
    "71": "Suwannee",
    "72": "Taylor",
    "73": "Union",
    "74": "Volusia",
    "75": "Wakulla",
    "76": "Walton",
    "77": "Washington",
    "78": "Unknown",
    "99": "Unknown",
}

FL_OCC = {
    "MRSA": ("assessor", "Mold Assessor"),
    "MRSR": ("remediator", "Mold Remediator"),
}


def fl_county_name(code: str) -> str:
    code = (code or "").strip()
    if code in FL_COUNTY:
        return FL_COUNTY[code]
    if code.isdigit():
        n = int(code)
        if 701 <= n <= 799 or n == 79:
            return "Out of state"
        if 801 <= n <= 899 or n == 80:
            return "Foreign"
    if not code:
        return "Unknown"
    return f"County code {code}"


def title_city(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # Keep ALL-CAPS source cities readable without inventing a new name.
    if s.isupper() and any(c.isalpha() for c in s):
        return s.title()
    return s


def compile_florida() -> dict:
    path = RAW / "fl-lic07mold.csv"
    rows_out = []
    skipped = Counter()
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for raw in csv.reader(f):
            raw = raw + [""] * (len(FL_FIELDS) - len(raw))
            d = dict(zip(FL_FIELDS, raw[: len(FL_FIELDS)]))
            occ = (d["occ"] or "").strip()
            if occ not in FL_OCC:
                skipped[occ] += 1
                continue
            role, role_label = FL_OCC[occ]
            primary = (d["primary_status"] or "").strip()
            secondary = (d["secondary_status"] or "").strip()
            status = "active" if secondary == "A" else "inactive" if secondary == "I" else "current"
            status_label = {
                "active": "Current / Active",
                "inactive": "Current / Inactive",
                "current": "Current",
            }[status]
            license_pub = (d["alt_lic"] or "").strip() or (d["license"] or "").strip()
            rows_out.append(
                {
                    "name": (d["name"] or "").strip(),
                    "dba": (d["dba"] or "").strip(),
                    "city": title_city(d["city"]),
                    "city_raw": (d["city"] or "").strip(),
                    "state": (d["state"] or "").strip(),
                    "zip": (d["zip"] or "").strip(),
                    "county_code": (d["county_code"] or "").strip(),
                    "county": fl_county_name(d["county_code"]),
                    "license": license_pub,
                    "license_numeric": (d["license"] or "").strip(),
                    "role": role,
                    "role_label": role_label,
                    "occ": occ,
                    "status": status,
                    "status_label": status_label,
                    "primary_status": primary,
                    "secondary_status": secondary,
                    "expiration": (d["expiration"] or "").strip(),
                }
            )
    rows_out.sort(key=lambda r: (r["county"], r["city"].lower(), r["name"].lower(), r["role"]))
    c_role_status = Counter((r["role"], r["status"]) for r in rows_out)
    return {
        "meta": {
            "state": "FL",
            "source_name": "Florida DBPR Mold-Related Services weekly extract (lic07mold.csv)",
            "source_url": "https://www2.myfloridalicense.com/sto/file_download/extracts/lic07mold.csv",
            "program_url": "https://www2.myfloridalicense.com/mold-related-services/public-records/",
            "codes_url": "https://www2.myfloridalicense.com/about-us/understanding-dbpr-codes/",
            "file_last_modified": "2026-08-29",
            "retrieved": RETRIEVED,
            "rows_in_file": 6721,
            "rows_used": len(rows_out),
            "skipped_not_assessor_or_remediator": dict(skipped),
            "active_assessors": c_role_status[("assessor", "active")],
            "inactive_assessors": c_role_status[("assessor", "inactive")],
            "active_remediators": c_role_status[("remediator", "active")],
            "inactive_remediators": c_role_status[("remediator", "inactive")],
            "note": (
                "File includes Current licensees only (primary status C). "
                "Secondary A = Active, I = Inactive. CE providers (PVDR) and CE courses (CRS1) "
                "are in the extract and were not listed as assessors or remediators. "
                "Florida licenses individuals, not businesses."
            ),
        },
        "people": rows_out,
    }


def compile_texas() -> dict:
    companies = []
    for fname, role, role_label, last_mod in [
        (
            "tx-vsMoldAssessmentCompany.csv",
            "assessor",
            "Mold Assessment Company",
            "2026-09-01",
        ),
        (
            "tx-vsMoldRemediationCompany.csv",
            "remediator",
            "Mold Remediation Company",
            "2026-09-01",
        ),
    ]:
        path = RAW / fname
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            for d in csv.DictReader(f):
                st = (d.get("License Status") or "").strip()
                status = "active" if st.upper() == "CURRENT" else "expired" if st.upper() == "EXPIRED" else st.lower() or "unknown"
                status_label = "Current" if status == "active" else "Expired" if status == "expired" else st
                county = (d.get("County") or "").strip() or "Unknown"
                if county.upper() in {"OUT OF STATE/UNKNOWN", "OUT OF STATE"}:
                    county = "Out of state / unknown"
                companies.append(
                    {
                        "name": (d.get("Licensee") or "").strip(),
                        "license": (d.get("License Number") or "").strip(),
                        "profession": (d.get("Profession") or "").strip(),
                        "role": role,
                        "role_label": role_label,
                        "status": status,
                        "status_label": status_label,
                        "expiration": (d.get("License Expiration Date") or "").strip(),
                        "addr1": (d.get("Address 1") or "").strip(),
                        "addr2": (d.get("Address 2") or "").strip(),
                        "city": title_city(d.get("City") or ""),
                        "city_raw": (d.get("City") or "").strip(),
                        "state": (d.get("State") or "").strip(),
                        "county": county.title() if county != "Out of state / unknown" else county,
                        "county_raw": (d.get("County") or "").strip(),
                        "zip": (d.get("Zip") or "").strip(),
                        "phone": (d.get("Phone") or "").strip(),
                    }
                )
    companies.sort(key=lambda r: (r["county"], r["city"].lower(), r["name"].lower(), r["role"]))
    c = Counter((r["role"], r["status"]) for r in companies)
    return {
        "meta": {
            "state": "TX",
            "source_name": "Texas TDLR mold company extracts",
            "assessment_url": "https://www.tdlr.texas.gov/dbproduction2/vsMoldAssessmentCompany.csv",
            "remediation_url": "https://www.tdlr.texas.gov/dbproduction2/vsMoldRemediationCompany.csv",
            "program_url": "https://www.tdlr.texas.gov/mld/",
            "search_url": "https://www.tdlr.texas.gov/LicenseSearch/",
            "file_last_modified": "2026-09-01",
            "retrieved": RETRIEVED,
            "assessment_companies_in_file": 252,
            "remediation_companies_in_file": 590,
            "rows_used": len(companies),
            "current_assessment_companies": c[("assessor", "active")],
            "expired_assessment_companies": c[("assessor", "expired")],
            "current_remediation_companies": c[("remediator", "active")],
            "expired_remediation_companies": c[("remediator", "expired")],
            "note": (
                "Parsed the two company CSVs TDLR publishes at /dbproduction2/. "
                "TDLR also publishes individual consultant, technician, and worker extracts; "
                "those were confirmed live and were not transcribed. This page lists companies."
            ),
        },
        "companies": companies,
    }


def compile_newyork() -> dict:
    path = RAW / "ny-mold-contractor-licenses.csv"
    rows_out = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for d in csv.DictReader(f):
            ltype = (d.get("License Type") or "").strip()
            if "Assessment" in ltype:
                role, role_label = "assessor", "Mold Assessment Contractor (SH125)"
            elif "Remediation" in ltype:
                role, role_label = "remediator", "Mold Remediation Contractor (SH126)"
            else:
                role, role_label = "other", ltype
            st = (d.get("License Status") or "").strip()
            status = "active" if st.lower() == "active" else "expired" if st.lower() == "expired" else st.lower() or "unknown"
            rows_out.append(
                {
                    "name": (d.get("Business Name") or "").strip(),
                    "dba": (d.get("DBA Name") or "").strip(),
                    "license": (d.get("License Number") or "").strip(),
                    "license_type": ltype,
                    "role": role,
                    "role_label": role_label,
                    "status": status,
                    "status_label": st or status.title(),
                    "issued": (d.get("Issued Date") or "").strip(),
                    "expiration": (d.get("Expiration Date") or "").strip(),
                    "addr1": (d.get("Address") or "").strip(),
                    "addr2": (d.get("Address 2") or "").strip(),
                    "city": title_city(d.get("City") or ""),
                    "city_raw": (d.get("City") or "").strip(),
                    "state": (d.get("State") or "").strip(),
                    "zip": (d.get("Zip Code") or "").strip(),
                    "phone": (d.get("Phone") or "").strip(),
                }
            )
    rows_out.sort(key=lambda r: (r["city"].lower(), r["name"].lower(), r["role"]))
    c = Counter((r["role"], r["status"]) for r in rows_out)
    return {
        "meta": {
            "state": "NY",
            "source_name": "NY Open Data — Mold Contractor Licenses (Four Year Window)",
            "source_url": "https://data.ny.gov/api/views/ikqx-ispy/rows.csv?accessType=DOWNLOAD",
            "dataset_url": "https://data.ny.gov/Economic-Development/Mold-Contractor-Licenses-Four-Year-Window-/ikqx-ispy",
            "program_url": "https://dol.ny.gov/mold-program",
            "faq_url": "https://dol.ny.gov/mold-frequently-asked-questions",
            "file_last_modified": "2026-09-01",
            "retrieved": RETRIEVED,
            "rows_in_file": len(rows_out),
            "active_assessment_contractors": c[("assessor", "active")],
            "expired_assessment_contractors": c[("assessor", "expired")],
            "active_remediation_contractors": c[("remediator", "active")],
            "expired_remediation_contractors": c[("remediator", "expired")],
            "note": (
                "Four-year window includes Active and Expired contractor (business) licenses. "
                "NY DOL also licenses individuals (assessors, abatement workers, supervisors); "
                "those records were not in this contractor extract and were not invented."
            ),
        },
        "contractors": rows_out,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fl = compile_florida()
    tx = compile_texas()
    ny = compile_newyork()
    (OUT / "florida.json").write_text(json.dumps(fl, indent=None, separators=(",", ":")))
    (OUT / "texas.json").write_text(json.dumps(tx, indent=None, separators=(",", ":")))
    (OUT / "newyork.json").write_text(json.dumps(ny, indent=None, separators=(",", ":")))
    summary = {
        "retrieved": RETRIEVED,
        "compiled_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "florida": {k: v for k, v in fl["meta"].items() if k != "note"},
        "texas": {k: v for k, v in tx["meta"].items() if k != "note"},
        "newyork": {k: v for k, v in ny["meta"].items() if k != "note"},
        "louisiana": {
            "state": "LA",
            "mode": "verify-only",
            "reason": "LSLBC public search is a JavaScript form; roster download is a paid request, not a free bulk file.",
            "search_url": "https://arlspublic.lslbc.louisiana.gov/Public/Search",
            "verify_url": "https://www.lslbc.louisiana.gov/verify-licensure/",
            "retrieved": RETRIEVED,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print("Florida used", fl["meta"]["rows_used"], "active assessors", fl["meta"]["active_assessors"], "active remediators", fl["meta"]["active_remediators"])
    print("Texas current assess", tx["meta"]["current_assessment_companies"], "current remediate", tx["meta"]["current_remediation_companies"])
    print("NY active assess", ny["meta"]["active_assessment_contractors"], "active remediate", ny["meta"]["active_remediation_contractors"])


if __name__ == "__main__":
    main()

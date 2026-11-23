"""Cut Yale New Haven's full price transparency file down to ED-relevant rows.

The full file (about 122 MB, 725k rows) is too big for GitHub. This keeps the
two attestation rows, the column header, and every row whose code is an ED visit
level, critical care, or a common ED lab, imaging study, infusion or procedure,
plus any other procedure row whose description mentions the ED/ER. It also
keeps observation-stay codes and the inpatient DRGs for the most common
admissions from the ED, and a short list of common ED medicines from the pharmacy rows.

Usage:
    python scripts/extract_ed_rows.py raw/ynhh_standard_charges_full.csv data/ynhh_ed_standard_charges.csv

Download the full file from the URL in data/SOURCE.md first.
"""

import csv
import re
import sys

ED_CODES = {
    # ED facility visit levels, critical care, trauma activation
    "99281", "99282", "99283", "99284", "99285", "99291", "99292", "G0390",
    # Observation stays (billed as outpatient)
    "G0378", "G0379", "99221", "99222", "99223",
    # ECG, echo, cardiac
    "93005", "93000", "93041", "93306", "92950", "92953", "92960",
    # Labs
    "36415", "80048", "80053", "80069", "80076", "80305", "80307", "81001", "81003", "81025",
    "82040", "82077", "82150", "82272", "82374", "82550", "82565", "82803", "82947", "82962",
    "83036", "83605", "83690", "83735", "83880", "84132", "84145", "84295", "84443", "84484",
    "84520", "84702", "84703", "85025", "85027", "85379", "85610", "85651", "85652", "85730",
    "86140", "86592", "86850", "86900", "86901", "87040", "87081", "87086", "87210", "87491",
    "87591", "87631", "87635", "87637", "87804", "87880", "0241U", "86308",
    # X-ray
    "71045", "71046", "71100", "72040", "72070", "72100", "72170", "73030", "73060", "73080",
    "73090", "73110", "73130", "73502", "73562", "73564", "73600", "73610", "73630", "74018",
    # CT and MRI
    "70450", "70480", "70486", "70490", "70491", "70496", "70498", "70544", "70551", "70553",
    "71250", "71260", "71270", "71275", "72125", "72131", "72141", "72148", "72192", "72193",
    "73200", "73221", "73700", "73721", "74170", "74174", "74176", "74177", "74178",
    # Ultrasound
    "76536", "76604", "76700", "76705", "76770", "76815", "76817", "76830", "76856", "76870",
    "76882", "93970", "93971",
    # Breathing treatments, injections, infusions, sedation
    "94060", "94640", "94664", "94760", "94761", "96360", "96361", "96365", "96366", "96367",
    "96372", "96374", "96375", "96376", "96523", "36000", "99151", "99152", "99153",
    "90471", "90715", "J7030", "J7050", "97161", "97162",
    # Wound care and procedures
    "10060", "10061", "10120", "10121", "10160", "11730", "11740", "11750", "11760",
    "12001", "12002", "12004", "12005", "12011", "12013", "12031", "12032", "12051", "12052",
    "13131", "13132", "16020", "16025", "20600", "20605", "20610", "30901", "31500", "31575",
    "32551", "36556", "40650", "41250", "42809", "45915", "46083", "49083", "51701", "51702",
    "51798", "62270", "64450", "65222", "69200",
    # Fracture and dislocation care, splints
    "23650", "23655", "24600", "24605", "24640", "25600", "26720", "26750", "27786", "28470", "28510",
    "29086", "29105", "29125", "29130", "29280", "29505", "29515", "29540", "29580",
}
# Inpatient MS-DRGs for common admissions from the ED (kept only when the
# code type is DRG, so CPT/CDM rows with the same digits are not pulled in).
ADMISSION_DRGS = {
    "064", "065", "066",  # stroke / intracranial hemorrhage
    "190", "191", "192",  # COPD
    "193", "194", "195",  # pneumonia
    "291", "292", "293",  # heart failure
    "312",  # syncope
    "313",  # chest pain
    "392",  # gastroenteritis / digestive disorders
    "602", "603",  # cellulitis
    "690",  # kidney and urinary tract infection
    "871", "872",  # sepsis
}
# Pharmacy (CDM) rows are kept only for this short list of common ED medicines, matched on the
# hospital's exact description. Each has several rows (one per manufacturer package).
MEDICINES = {
    "ACETAMINOPHEN 500 MG TABLET",
    "LIDOCAINE 4 % TOPICAL PATCH",
    "ONDANSETRON HCL (PF) 4 MG/2 ML INJECTION SOLUTION",
    "DEXAMETHASONE SODIUM PHOSPHATE 4 MG/ML INJECTION SOLUTION",
    "FAMOTIDINE (PF) 20 MG/2 ML INTRAVENOUS SOLUTION",
    "DIPHENHYDRAMINE 50 MG/ML INJECTION SOLUTION",
    "EPINEPHRINE 0.3 MG/0.3 ML INJECTION, AUTO-INJECTOR",
    "CEPHALEXIN 500 MG CAPSULE",
    "CEFTRIAXONE 1 GRAM SOLUTION FOR INJECTION",
}
ED_REVENUE_CODE = re.compile(r"^0?45\d$|^0?981$")
ED_DESCRIPTION = re.compile(r"\bED\b|EMERG|\bER\b", re.IGNORECASE)


def is_ed_row(row: list[str]) -> bool:
    description = row[0] if row else ""
    code = row[1].strip() if len(row) > 1 else ""
    code_type = row[2].strip() if len(row) > 2 else ""
    if code_type == "DRG":
        return code in ADMISSION_DRGS
    if code_type == "CDM":
        # Pharmacy and supply items: only the listed medicines. ("ER" in other drug names means
        # extended-release, not emergency room.)
        return " ".join(description.split()) in MEDICINES
    if code in ED_CODES:
        return True
    if code_type == "RC" and ED_REVENUE_CODE.match(code):
        return True
    return bool(ED_DESCRIPTION.search(description))


def main(source: str, target: str) -> None:
    kept = total = 0
    # The hospital publishes the file in Windows-1252, not UTF-8.
    with open(source, newline="", encoding="cp1252", errors="replace") as src, open(
        target, "w", newline="", encoding="utf-8"
    ) as dst:
        reader = csv.reader(src)
        writer = csv.writer(dst, lineterminator="\n")
        for _ in range(3):  # attestation header, attestation values, column header
            writer.writerow(next(reader))
        for row in reader:
            if not row:
                continue
            total += 1
            if is_ed_row(row):
                writer.writerow(row)
                kept += 1
    print(f"kept {kept:,} of {total:,} rows -> {target}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

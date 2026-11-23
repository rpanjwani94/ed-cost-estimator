# Data sources

## Yale New Haven Hospital standard charges (price transparency file)

- Publisher: Yale New Haven Hospital, under the CMS hospital price transparency rule (45 CFR 180.50).
- Index file: https://www.ynhh.org/YNHHAssets/cms-hpt.txt
- Source page: https://www.ynhh.org/patients-visitors/billing-insurance/Pricing
- Full file: https://www.ynhh.org/-/media/Files/YNHHS/sc/06-0646652-Yale_New_Haven_Hospital_Standard_Charges011025-1.ashx
  - Served as `06-0646652 Yale_New_Haven_Hospital_Standard_Charges011025 1.csv`, 121.8 MB, CMS template version 3.0.0, `last_updated_on` 9/19/2026.
  - Covers Yale New Haven Hospital and St. Raphael's Hospital in one file.
  - 724,913 rows (CDM 486,036; CPT 221,467; DRG 17,410).
- Retrieved: 2026-11-20.

### Columns (row 3 of the file)

`description, code|1, code|1|type, modifiers, setting, drug_unit_of_measurement, drug_type_of_measurement, standard_charge|gross, standard_charge|discounted_cash, payer_name, plan_name, standard_charge|negotiated_dollar, standard_charge|negotiated_percentage, standard_charge|negotiated_algorithm, median_amount, 10th_percentile, 90th_percentile, count, standard_charge|methodology, standard_charge|min, standard_charge|max, additional_generic_notes`

### Test dataset in this repo: `data/ynhh_ed_standard_charges.csv`

- 10,373 rows, 1.6 MB, UTF-8: 240 outpatient services: 231 billing codes (ED visit levels, critical care, observation, common ED labs, imaging, infusions and procedures, plus other procedure rows whose description mentions the ED/ER) plus 9 medicines, and 20 inpatient DRGs for common admissions from the ED (460 DRG rows). Each code has one row per insurer (23 insurers).
- From the pharmacy rows (code type CDM) only nine common ED medicines are kept, matched on the hospital's exact description (listed in `scripts/extract_ed_rows.py`). The file lists each medicine once per manufacturer package, at different prices; the app uses the middle-priced package. Other medications and all supplies are left out.
- Made by `scripts/extract_ed_rows.py` from the full file:
  `python scripts/extract_ed_rows.py raw/ynhh_standard_charges_full.csv data/ynhh_ed_standard_charges.csv`
- The full file is published in Windows-1252 encoding, not UTF-8; the script reads it that way.
- The full file lives in `raw/`, which is git-ignored (GitHub rejects files over 100 MB).
- The file has no ED physician professional fees (only hospital-based `HCPR PF` rows for hospital care, 99221–99223). ED physician fees come from another source.

### ED facility prices, outpatient (23 payer rows per code)

| Code | Description | Gross charge | Discounted cash | Negotiated range across payers |
|---|---|---|---|---|
| 99281 | HC ER LVL I | $361.64 | $213.37 | $60.94–$325.48 |
| 99282 | HC ER LVL II | $687.83 | $405.82 | $115.91–$619.05 |
| 99283 | HC ER LVL III | $1,479.99 | $873.19 | $249.41–$1,331.99 |
| 99284 | HC ER LVL IV | $1,902.41 | $1,122.42 | $320.60–$1,712.17 |
| 99285 | HC ER LVL V | $2,642.92 | $1,559.32 | $445.39–$2,378.63 |
| 99291 | HC ER CRITICAL CARE 30-74 MIN | $3,804.83 | $2,244.85 | $641.20–$3,424.35 |
| 84484 | HC TROPONIN, QUANTITATIVE | $101.00 | $59.59 | $12.17–$90.90 |
| 71046 | HC XR EXAM CHEST 2 VIEWS | $227.70 | $134.34 | $38.18–$204.93 |
| 70450 | HC CT HEAD/BRAIN W/O CONTR | $792.17 | $467.38 | $132.83–$712.95 |
| 74177 | HC CT ABD/PEL W/CONTR | $2,201.25 | $1,298.74 | $369.09–$1,981.13 |

Commercial examples for 99284: Aetna $1,100.99, Anthem $1,112.37, Cigna $1,236.65, UHC $1,078.41.

### Observation stays (outpatient)

| Code | Description | Gross charge |
|---|---|---|
| G0379 | HC DIRECT REFER HOSPITAL OBSERVATION | $1,752.49 |
| 99222 | HC OBSERVATION MODERATE ACUITY | $468.01 |
| 99223 | HC OBSERVATION HIGHER ACUITY | $744.56 |

### Admissions from the ED: inpatient MS-DRG case rates (setting `INPATIENT`, 23 payer rows each, all dollar amounts)

| DRG | Description | Gross charge | Discounted cash | Negotiated range across payers |
|---|---|---|---|---|
| 313 | Chest pain | $33,793.99 | $19,938.45 | $7,277.60–$30,414.59 |
| 312 | Syncope and collapse | $44,000.14 | $25,960.08 | $9,475.52–$39,600.12 |
| 871 | Sepsis w/o MV >96 hrs, with MCC | $98,398.72 | $58,055.24 | $21,190.36–$88,558.85 |
| 872 | Sepsis w/o MV >96 hrs, without MCC | $41,997.66 | $24,778.62 | $9,044.28–$37,797.89 |
| 291 | Heart failure and shock with MCC | $62,248.83 | $36,726.81 | $13,405.41–$56,023.95 |
| 292 | Heart failure and shock with CC | $47,000.07 | $27,730.04 | $10,121.56–$42,300.07 |
| 293 | Heart failure and shock without CC/MCC | $10,760.45 | $6,348.67 | $2,317.28–$9,684.41 |
| 193 | Simple pneumonia with MCC | $56,676.26 | $33,439.00 | $12,205.34–$51,008.64 |
| 194 | Simple pneumonia with CC | $31,064.72 | $18,328.18 | $6,689.85–$27,958.24 |
| 195 | Simple pneumonia without CC/MCC | $15,775.92 | $9,307.79 | $3,397.38–$14,198.33 |
| 602 | Cellulitis with MCC | $68,593.33 | $40,470.07 | $14,771.71–$61,734.00 |
| 603 | Cellulitis without MCC | $30,932.52 | $18,250.19 | $6,661.38–$27,839.27 |
| 190 | COPD with MCC | $58,433.35 | $34,475.68 | $12,583.74–$52,590.02 |
| 191 | COPD with CC | $39,925.91 | $23,556.29 | $8,598.12–$35,933.32 |
| 192 | COPD without CC/MCC | $20,902.82 | $12,332.66 | $4,501.46–$18,812.54 |
| 064 | Stroke / intracranial hemorrhage with MCC | $110,639.68 | $65,277.41 | $23,826.47–$99,575.71 |
| 065 | Stroke / intracranial hemorrhage with CC or tPA | $61,334.20 | $36,187.18 | $13,208.44–$55,200.78 |
| 066 | Stroke / intracranial hemorrhage without CC/MCC | $33,798.02 | $19,940.83 | $7,278.47–$30,418.21 |
| 392 | Esophagitis, gastroenteritis, misc. digestive | $30,294.29 | $17,873.63 | $6,523.94–$27,264.87 |
| 690 | Kidney and urinary tract infection without MCC | $32,576.65 | $19,220.22 | $7,015.45–$29,318.99 |

A DRG case rate is what the insurer pays the hospital for the whole stay; the patient's share is set by their plan (deductible, coinsurance, out-of-pocket maximum).

### Caveats found while checking the file

- `median_amount`, `10th_percentile`, `90th_percentile` and `count` are identical for every payer on a code, and `count` is 1000 on every row checked (including $0.01 placeholder codes). Treat them as a hospital-wide summary, not proof of real paid amounts per insurer.
- The file has facility (hospital) charges only. The emergency physician's professional fee is billed separately and must come from another source (e.g. the CMS Physician Fee Schedule).
- 23 payer networks are listed (Aetna, Anthem, Cigna, CtCare, Oxford, UHC, Harvard Pilgrim, Medicare Advantage plans, and others).

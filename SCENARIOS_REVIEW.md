# Clinical scenarios

These 17 scenarios drive every estimate. They were drafted with AI help, then reviewed and corrected by the project's ED clinician on 22 November 2026.

To change one, describe the change in plain words (for example "chest pain: add a second ECG to possible") and the data file `data/workups.json` is updated to match. Prices shown are the hospital's list prices, only to show scale.

## 1. Chest pain

**Visit level:** low 99284 · typical 99285 · high 99285  
**Matched when the patient says:** chest pain, chest pressure, chest tightness, heart, palpitations, angina

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| ECG (heart tracing) | 93005 | 1 | $243.92 |  |
| Troponin (heart damage blood test) | 84484 | 2 | $101.00 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| Chest X-ray (2 views) | 71046 | 1 | $227.70 |  |
| Blood draw | 36415 | 1 | $23.00 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| D-dimer (blood clot screening test) | 85379 | 1 | $105.00 |  |
| CT angiogram of the chest (checks for lung blood clots) | 71275 | 1 | $1,547.86 |  |
| BNP (heart failure blood test) | 83880 | 1 | $349.00 |  |
| IV medication push (first) | 96374 | 1 | $580.45 |  |
| Sedimentation rate (inflammation marker) | 85652 | 1 | $28.00 | ESR |
| C-reactive protein (inflammation marker) | 86140 | 1 | $53.00 | CRP |

**Admission:** possible · observation stay possible: yes  
**If admitted, priced as:** Chest pain (DRG 313)  
**Note shown to the planner:** Two troponins a few hours apart is standard. Many low-risk patients go home; others stay in observation for monitoring or a stress test.

---

## 2. Abdominal pain

**Visit level:** low 99284 · typical 99284 · high 99285  
**Matched when the patient says:** abdominal pain, stomach pain, belly pain, stomach ache, appendicitis, gallbladder, abdomen

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Comprehensive metabolic panel (adds liver tests) | 80053 | 1 | $63.36 |  |
| Lipase (pancreas test) | 83690 | 1 | $71.00 |  |
| Urinalysis with microscope exam | 81001 | 1 | $19.02 |  |
| Blood draw | 36415 | 1 | $23.00 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT scan of the abdomen and pelvis (with contrast) | 74177 | 1 | $2,201.25 |  |
| Ultrasound of the abdomen (limited) | 76705 | 1 | $453.82 |  |
| Blood pregnancy test (yes/no) | 84703 | 1 | $77.00 |  |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |
| IV medication push (first) | 96374 | 1 | $580.45 |  |
| Ondansetron 4 mg IV (anti-nausea medicine) | RX-ONDANSETRON | 1 | $2.07 | anti-nausea medicine |
| IV medication push (each additional drug) | 96375 | 1 | $127.64 | IV push for the anti-nausea medicine |

**Admission:** possible · observation stay possible: yes  
**If admitted, priced as:** Esophagitis gastroenteritis and miscellaneous digestive disorders without mcc (DRG 392)  
**Note shown to the planner:** The CT scan is the biggest swing in cost. Whether it is needed depends on the exam and blood work.

---

## 3. Ankle or foot injury

**Visit level:** low 99282 · typical 99283 · high 99283  
**Matched when the patient says:** ankle, sprain, twisted, rolled my ankle, foot injury, foot pain after

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Ankle X-ray | 73610 | 1 | $227.70 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Foot X-ray | 73630 | 1 | $227.70 |  |
| Lower leg or ankle splint | 29515 | 1 | $601.51 |  |
| Ankle fracture care (no setting needed) | 27786 | 1 | $733.41 |  |
| MRI of a leg joint such as the ankle or knee (no contrast) | 73721 | 1 | $1,543.81 | MRI if needed |
| Physical therapy evaluation | 97161 | 1 | $712.14 | physical therapy evaluation |

**Admission:** unlikely · observation stay possible: yes  
**If admitted, priced as:** none listed  
**Note shown to the planner:** Most ankle injuries need one X-ray. A splint or fracture care is added only if something is broken. Some patients are kept in ED or medical observation when they need physical therapy or an MRI.

---

## 4. Wrist, hand or arm injury

**Visit level:** low 99282 · typical 99283 · high 99284  
**Matched when the patient says:** wrist, hand injury, arm injury, fell on my hand, forearm, elbow, finger injury, broken arm

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Wrist X-ray | 73110 | 1 | $227.70 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Hand X-ray | 73130 | 1 | $227.70 |  |
| Forearm X-ray | 73090 | 1 | $227.70 |  |
| Forearm or wrist splint | 29125 | 1 | $479.15 |  |
| Wrist fracture care (no setting needed) | 25600 | 1 | $733.41 |  |

**Admission:** unlikely · observation stay possible: no  
**If admitted, priced as:** none listed  
**Note shown to the planner:** Cost depends on how many areas are X-rayed and whether a fracture needs a splint.

---

## 5. Cut that may need stitches

**Visit level:** low 99282 · typical 99283 · high 99283  
**Matched when the patient says:** cut, laceration, stitches, gash, sliced, bleeding wound

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Stitches, simple cut up to 2.5 cm (body, scalp, hands, feet) | 12001 | 1 | $563.23 |  |
| Hand X-ray | 73130 | 1 | $227.70 | X-ray of the injured area (hand shown; use the body part that was cut) |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Tetanus booster (Tdap) vaccine | 90715 | 1 | $243.83 |  |
| Vaccine administration | 90471 | 1 | $144.00 |  |

**Admission:** unlikely · observation stay possible: no  
**If admitted, priced as:** none listed  
**Note shown to the planner:** The repair is priced by length, depth and body area; a longer or deeper cut costs more than shown. A tetanus booster is added if yours is out of date.

---

## 6. Headache

**Visit level:** low 99283 · typical 99284 · high 99285  
**Matched when the patient says:** headache, migraine, head pain

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT scan of the head (no contrast) | 70450 | 1 | $792.17 |  |
| IV medication push (first) | 96374 | 1 | $580.45 | IV medicine |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| Blood draw | 36415 | 1 | $23.00 | blood draw for the labs |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT angiogram of the head (brain blood vessels) | 70496 | 1 | $1,547.86 |  |
| CT angiogram of the neck (neck blood vessels) | 70498 | 1 | $1,547.86 |  |

**Admission:** unlikely · observation stay possible: no  
**If admitted, priced as:** none listed  
**Note shown to the planner:** The usual ED workup for a headache is a head CT, blood work, IV fluids and IV medicine. A CT angiogram of the head and neck is added when a blood vessel problem is a concern.

---

## 7. Head injury

**Visit level:** low 99283 · typical 99284 · high 99285  
**Matched when the patient says:** head injury, hit my head, concussion, fell and hit, bumped head

**Expected (most patients)**

- none

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT scan of the head (no contrast) | 70450 | 1 | $792.17 |  |
| CT scan of the neck spine (no contrast) | 72125 | 1 | $792.17 |  |
| Stitches, simple cut up to 2.5 cm (body, scalp, hands, feet) | 12001 | 1 | $563.23 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 | labs |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 | labs |
| Blood draw | 36415 | 1 | $23.00 | blood draw for the labs |
| Acetaminophen 500 mg tablet | RX-ACETAMINOPHEN | 2 | $0.09 |  |
| Tetanus booster (Tdap) vaccine | 90715 | 1 | $243.83 | tetanus booster |
| Vaccine administration | 90471 | 1 | $144.00 | giving the tetanus booster |

**Admission:** unlikely · observation stay possible: yes  
**If admitted, priced as:** none listed  
**Note shown to the planner:** Clinicians use decision rules to decide who needs a head CT. Many minor head injuries need only an exam and watching.

---

## 8. Shortness of breath, asthma or COPD flare

**Visit level:** low 99284 · typical 99285 · high 99291  
**Matched when the patient says:** shortness of breath, short of breath, trouble breathing, can't breathe, wheezing, asthma, copd, breathing

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Chest X-ray (2 views) | 71046 | 1 | $227.70 |  |
| Nebulizer breathing treatment | 94640 | 1 | $637.10 |  |
| ECG (heart tracing) | 93005 | 1 | $243.92 |  |
| COVID + flu + RSV PCR test | 87637 | 1 | $855.78 | flu/COVID/RSV swab |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| BNP (heart failure blood test) | 83880 | 1 | $349.00 |  |
| Troponin (heart damage blood test) | 84484 | 1 | $101.00 |  |
| Blood gas | 82803 | 1 | $199.00 |  |
| D-dimer (blood clot screening test) | 85379 | 1 | $105.00 |  |
| CT angiogram of the chest (checks for lung blood clots) | 71275 | 1 | $1,547.86 |  |
| Blood draw | 36415 | 1 | $23.00 |  |
| Ceftriaxone 1 g IV (antibiotic) | RX-CEFTRIAXONE | 1 | $5.00 | antibiotic |
| IV medication infusion (first hour) | 96365 | 1 | $660.48 | IV infusion for the antibiotic |

**Admission:** possible · observation stay possible: yes  
**If admitted, priced as:** Chronic obstructive pulmonary disease with mcc (DRG 190); Chronic obstructive pulmonary disease with cc (DRG 191); Chronic obstructive pulmonary disease without cc-mcc (DRG 192); Heart failure and shock with mcc (DRG 291); Heart failure and shock with cc (DRG 292); Heart failure and shock without cc-mcc (DRG 293)  
**Note shown to the planner:** The range is wide because the cause ranges from a mild asthma flare to heart failure or a blood clot in the lung.

---

## 9. Cough and fever (possible flu, COVID or pneumonia)

**Visit level:** low 99283 · typical 99284 · high 99285  
**Matched when the patient says:** cough, fever, flu, covid, pneumonia, chills, body aches

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Chest X-ray (2 views) | 71046 | 1 | $227.70 |  |
| COVID + flu + RSV PCR test | 87637 | 1 | $855.78 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| Lactate (lactic acid) | 83605 | 1 | $110.00 |  |
| Blood culture | 87040 | 2 | $96.00 |  |
| Procalcitonin (bacterial infection marker) | 84145 | 1 | $276.00 |  |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |
| IV medication infusion (first hour) | 96365 | 1 | $660.48 |  |
| Blood draw | 36415 | 1 | $23.00 |  |

**Admission:** possible · observation stay possible: yes  
**If admitted, priced as:** Simple pneumonia and pleurisy with mcc (DRG 193); Simple pneumonia and pleurisy with cc (DRG 194); Simple pneumonia and pleurisy without cc-mcc (DRG 195); Septicemia or severe sepsis without mv greater than 96 hours with mcc (DRG 871); Septicemia or severe sepsis without mv greater than 96 hours without mcc (DRG 872)  
**Note shown to the planner:** Healthy adults with a viral illness usually go home. Older or sicker patients with pneumonia may be admitted.

---

## 10. Painful urination or flank pain (possible UTI or kidney stone)

**Visit level:** low 99283 · typical 99284 · high 99284  
**Matched when the patient says:** uti, urinary, burning when i pee, painful urination, kidney stone, flank pain, blood in urine, kidney

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Urinalysis with microscope exam | 81001 | 1 | $19.02 |  |
| Urine culture | 87086 | 1 | $83.00 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| CT scan of the abdomen and pelvis (no contrast) | 74176 | 1 | $1,395.91 |  |
| Ultrasound of the kidneys | 76770 | 1 | $453.82 |  |
| Blood pregnancy test (yes/no) | 84703 | 1 | $77.00 |  |
| IV medication push (first) | 96374 | 1 | $580.45 |  |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |
| Blood draw | 36415 | 1 | $23.00 |  |

**Possible (some patients)**

- none

**Admission:** unlikely · observation stay possible: no  
**If admitted, priced as:** Kidney and urinary tract infections without mcc (DRG 690)  
**Note shown to the planner:** The ED workup includes urine tests, blood work, imaging for a kidney stone (CT and kidney ultrasound), and IV fluids and medicine.

---

## 11. Fainting or passing out

**Visit level:** low 99284 · typical 99285 · high 99285  
**Matched when the patient says:** fainted, passed out, syncope, blacked out, lost consciousness, fainting

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| ECG (heart tracing) | 93005 | 1 | $243.92 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| Fingerstick blood sugar | 82962 | 1 | $24.00 |  |
| Blood draw | 36415 | 1 | $23.00 |  |
| Troponin (heart damage blood test) | 84484 | 1 | $101.00 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT scan of the head (no contrast) | 70450 | 1 | $792.17 |  |
| Chest X-ray (2 views) | 71046 | 1 | $227.70 |  |
| Blood pregnancy test (yes/no) | 84703 | 1 | $77.00 |  |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |

**Admission:** likely · observation stay possible: yes  
**If admitted, priced as:** Syncope and collapse (DRG 312)  
**Note shown to the planner:** The ED checks the heart, including a troponin. Most patients are admitted or kept for monitoring.

---

## 12. Stroke symptoms

**Visit level:** low 99285 · typical 99285 · high 99291  
**Matched when the patient says:** stroke, face drooping, slurred speech, weakness on one side, numbness on one side, can't speak, tia

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT scan of the head (no contrast) | 70450 | 1 | $792.17 |  |
| CT angiogram of the head (brain blood vessels) | 70496 | 1 | $1,547.86 |  |
| CT angiogram of the neck (neck blood vessels) | 70498 | 1 | $1,547.86 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| Prothrombin time / INR (clotting test) | 85610 | 1 | $40.00 |  |
| Fingerstick blood sugar | 82962 | 1 | $24.00 |  |
| ECG (heart tracing) | 93005 | 1 | $243.92 |  |
| Troponin (heart damage blood test) | 84484 | 1 | $101.00 |  |
| Blood draw | 36415 | 1 | $23.00 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| MRI of the brain (no contrast) | 70551 | 1 | $1,543.81 |  |

**Admission:** likely · observation stay possible: no  
**If admitted, priced as:** Intracranial hemorrhage or cerebral infarction with mcc (DRG 064); Intracranial hemorrhage or cerebral infarction with cc or tpa in 24 hours (DRG 065); Intracranial hemorrhage or cerebral infarction without cc-mcc (DRG 066)  
**Note shown to the planner:** Stroke care is time-critical. Call 911. Do not wait to compare prices. A neurology consult is part of the workup; the neurologist bills separately, so it is not in the hospital-bill total.

---

## 13. Skin infection or abscess

**Visit level:** low 99282 · typical 99283 · high 99284  
**Matched when the patient says:** abscess, cellulitis, skin infection, boil, infected, red swollen skin

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Cephalexin 500 mg capsule (antibiotic) | RX-CEPHALEXIN | 1 | $1.14 | antibiotic |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Abscess drainage (simple) | 10060 | 1 | $563.23 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| IV medication infusion (first hour) | 96365 | 1 | $660.48 |  |
| Soft tissue ultrasound of an arm or leg | 76882 | 1 | $412.63 |  |
| Blood draw | 36415 | 1 | $23.00 |  |

**Admission:** unlikely · observation stay possible: yes  
**If admitted, priced as:** Cellulitis with mcc (DRG 602); Cellulitis without mcc (DRG 603)  
**Note shown to the planner:** Antibiotics are expected. An abscess that needs draining, blood work, or IV antibiotics adds to the cost.

---

## 14. Vomiting, diarrhea or dehydration

**Visit level:** low 99283 · typical 99284 · high 99284  
**Matched when the patient says:** vomiting, throwing up, diarrhea, dehydrated, dehydration, nausea, food poisoning, stomach bug

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Basic metabolic panel (electrolytes and kidney function) | 80048 | 1 | $50.76 |  |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |
| Blood draw | 36415 | 1 | $23.00 |  |
| Complete blood count (CBC) | 85025 | 1 | $46.62 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| IV medication push (first) | 96374 | 1 | $580.45 |  |
| IV fluids (each extra hour) | 96361 | 1 | $127.64 |  |
| Lipase (pancreas test) | 83690 | 1 | $71.00 |  |
| Urinalysis with microscope exam | 81001 | 1 | $19.02 |  |
| Blood pregnancy test (yes/no) | 84703 | 1 | $77.00 |  |
| CT scan of the abdomen and pelvis (with contrast) | 74177 | 1 | $2,201.25 |  |

**Admission:** unlikely · observation stay possible: yes  
**If admitted, priced as:** Esophagitis gastroenteritis and miscellaneous digestive disorders without mcc (DRG 392)  
**Note shown to the planner:** IV fluids and anti-nausea medicine are the usual treatment. Imaging is uncommon unless the pain is severe.

---

## 15. Back pain

**Visit level:** low 99282 · typical 99283 · high 99284  
**Matched when the patient says:** back pain, lower back, sciatica, threw out my back

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Acetaminophen 500 mg tablet | RX-ACETAMINOPHEN | 2 | $0.09 |  |
| Lidocaine 4% patch | RX-LIDOCAINE-PATCH | 1 | $4.36 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| MRI of the lower spine (no contrast) | 72148 | 1 | $1,543.81 |  |

**Admission:** unlikely · observation stay possible: no  
**If admitted, priced as:** none listed  
**Note shown to the planner:** Most back pain is treated with acetaminophen and a lidocaine patch and needs no imaging. An MRI is ordered only for warning signs like weakness, fever or loss of bladder control.

---

## 16. Sore throat

**Visit level:** low 99281 · typical 99282 · high 99283  
**Matched when the patient says:** sore throat, strep, throat pain, tonsils

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Rapid strep test | 87880 | 1 | $123.00 |  |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| COVID + flu + RSV PCR test | 87637 | 1 | $855.78 |  |
| Mono test (heterophile antibody) | 86308 | 1 | $53.00 | mono (EBV) test |

**Admission:** unlikely · observation stay possible: no  
**If admitted, priced as:** none listed  
**Note shown to the planner:** This is usually a low-level visit. An urgent care clinic or primary care office can often treat it for much less.

---

## 17. Allergic reaction

**Visit level:** low 99283 · typical 99284 · high 99285  
**Matched when the patient says:** allergic reaction, hives, swelling, allergy, rash after, bee sting

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Dexamethasone IV (steroid) | RX-DEXAMETHASONE | 1 | $2.27 |  |
| Famotidine (Pepcid) 20 mg IV | RX-FAMOTIDINE | 1 | $3.18 |  |
| Diphenhydramine (Benadryl) 50 mg IV | RX-DIPHENHYDRAMINE | 1 | $4.61 |  |
| IV medication push (first) | 96374 | 1 | $580.45 | IV push, first medicine |
| IV medication push (each additional drug) | 96375 | 2 | $127.64 | IV push, second and third medicines |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Epinephrine auto-injector 0.3 mg (EpiPen) | RX-EPINEPHRINE | 1 | $691.13 | EpiPen |
| Injection (shot in the muscle or under the skin) | 96372 | 1 | $195.51 | injection of epinephrine |
| IV fluids (first hour) | 96360 | 1 | $660.48 |  |

**Admission:** unlikely · observation stay possible: yes  
**If admitted, priced as:** none listed  
**Note shown to the planner:** The usual treatment is IV dexamethasone, famotidine (Pepcid) and diphenhydramine (Benadryl). A severe reaction (trouble breathing, throat swelling) is an emergency, needs epinephrine, and is watched for several hours.

---

## 18. Dislocated joint (elbow or shoulder)

**Visit level:** low 99284 · typical 99284 · high 99285  
**Matched when the patient says:** dislocation, dislocated, popped out, out of socket, elbow dislocation, shoulder dislocation

**Expected (most patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| Elbow X-ray | 73080 | 2 | $227.70 | X-ray before and after the joint is put back (elbow shown; use the shoulder X-ray for a shoulder) |
| Putting a dislocated elbow back in place | 24600 | 1 | $733.41 | putting the joint back (elbow shown; use the shoulder code for a shoulder) |
| Procedural sedation (first 15 minutes) | 99152 | 1 | $310.99 | sedation for the procedure |
| Procedural sedation (each extra 15 minutes) | 99153 | 1 | $291.74 | sedation, extra time |
| IV medication push (first) | 96374 | 1 | $580.45 | IV pain medicine |
| Long arm splint | 29105 | 1 | $459.90 | splint |

**Possible (some patients)**

| Service | Code | Qty | List price each | Note |
|---|---|---|---|---|
| CT scan of an arm joint (no contrast) | 73200 | 1 | $792.17 | CT if a fracture is suspected |
| IV medication push (each additional drug) | 96375 | 1 | $127.64 | second IV medicine |
| Procedural sedation (each extra 15 minutes) | 99153 | 1 | $291.74 | longer sedation |

**Admission:** unlikely · observation stay possible: yes  
**If admitted, priced as:** none listed  
**Note shown to the planner:** DRAFT, not yet reviewed by the clinician. A dislocated joint is X-rayed, put back under sedation, X-rayed again and splinted. If it cannot be put back in the ED it is done under anesthesia, which costs several times more and is not in this estimate.

---

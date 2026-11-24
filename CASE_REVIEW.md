# Review of 30 test cases

Thirty patient descriptions with a physician's expectations (`data/review_cases.json`), run through the real agents by `scripts/run_review_cases.py`. The cases came from an outside AI review of the app. The three checks are simple and mechanical: they compare billing codes and the red banner with what each case calls for.

- **Red banner right** (shown when the case is an emergency, not shown when it is minor): 24 of 24
- **Plan includes what the case calls for**: 19 of 19
- **Restraint** (nothing the case says should not be routine is in the expected list): 10 of 14
- **Cases with no failed check**: 26 of 30

| # | Case | Result | Red banner | Banner right | Includes | Restraint | Scenario used | Visit levels | Most likely | What was off |
|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Typical chest pain | estimate | yes | yes | yes | n/a | chest_pain | 4/5/5 | $1,820 |  |
| 02 | Low-risk chest pain | estimate | yes | n/a | n/a | **NO** | chest_pain | 4/5/5 | $1,814 | listed as expected: Troponin (heart damage blood test) |
| 03 | Possible pulmonary embolism | estimate | yes | yes | yes | n/a | chest_pain | 4/5/5 | $1,837 |  |
| 04 | Aortic dissection | estimate | yes | yes | yes | n/a | chest_pain | 4/5/5 | $2,589 |  |
| 05 | Palpitations | estimate | no | yes | yes | yes | chest_pain | 2/3/4 | $971 |  |
| 06 | Appendicitis | estimate | yes | n/a | yes | n/a | abdominal_pain | 4/4/5 | $1,156 |  |
| 07 | Biliary disease | estimate | no | n/a | yes | n/a | abdominal_pain | 4/4/5 | $1,405 |  |
| 08 | Gastroenteritis | estimate | no | yes | n/a | **NO** | vomiting_diarrhea | 3/4/4 | $1,422 | listed as expected: IV fluids (first hour) |
| 09 | GI bleeding | estimate | yes | yes | yes | n/a | gi_bleeding | 4/5/critical care | $2,036 |  |
| 10 | Possible ectopic pregnancy | estimate | yes | yes | yes | n/a | pregnancy_bleeding | 4/4/5 | $1,393 |  |
| 11 | Possible stroke | estimate | yes | yes | yes | n/a | stroke_symptoms | 5/5/critical care | $3,635 |  |
| 12 | Migraine | estimate | no | yes | n/a | **NO** | headache | 3/4/5 | $2,085 | listed as expected: CT scan of the head (no contrast) |
| 13 | Thunderclap headache | estimate | yes | yes | yes | n/a | headache | 3/4/5 | $2,085 |  |
| 14 | Minor head injury | estimate | no | yes | n/a | yes | head_injury | 3/4/5 | $1,078 |  |
| 15 | Anticoagulated head injury | estimate | yes | n/a | yes | n/a | head_injury | 3/4/5 | $1,475 |  |
| 16 | Mild URI | estimate | no | yes | n/a | yes | sore_throat | 1/2/3 | $432 |  |
| 17 | Pneumonia | estimate | yes | n/a | yes | n/a | cough_fever | 3/4/5 | $1,489 |  |
| 18 | Severe asthma | estimate | yes | yes | yes | n/a | shortness_of_breath | 4/5/critical care | $2,296 |  |
| 19 | Possible sepsis | estimate | yes | yes | yes | n/a | cough_fever | 4/5/5 | $2,044 |  |
| 20 | Uncomplicated cystitis | estimate | no | yes | yes | yes | urinary_flank | 3/3/4 | $874 |  |
| 21 | Ankle sprain | estimate | no | yes | n/a | **NO** | ankle_injury | 2/3/3 | $953 | listed as expected: Ankle X-ray |
| 22 | Wrist fracture | estimate | yes | n/a | yes | n/a | arm_wrist_injury | 2/3/4 | $953 |  |
| 23 | Simple laceration | estimate | no | yes | yes | yes | laceration | 2/3/3 | $1,102 |  |
| 24 | Abscess | estimate | no | yes | yes | yes | skin_infection | 2/3/4 | $839 |  |
| 25 | Back pain without red flags | estimate | no | yes | n/a | yes | back_pain | 2/3/4 | $841 |  |
| 26 | Pediatric fever | estimate | no | yes | n/a | yes | cough_fever | 3/4/5 | $1,489 |  |
| 27 | Pediatric emergency | estimate | yes | yes | n/a | n/a | shortness_of_breath | 5/critical care/critical care | $3,024 |  |
| 28 | Severe hyperglycemia | estimate | yes | yes | yes | n/a | vomiting_diarrhea | 4/5/5 | $1,851 |  |
| 29 | Psychiatric emergency | estimate | yes | yes | n/a | yes | mental_health_crisis | 4/5/5 | $1,498 |  |
| 30 | Dental pain | estimate | no | yes | n/a | yes | dental_pain | 1/2/3 | $390 |  |

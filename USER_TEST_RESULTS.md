# User test results

Feedback from people who tried the app through the shared link, in their own words. What each tester typed, and what the app answered, comes from the test-mode log (`output/test_runs.jsonl`).

## Tester 1 (22 November 2026)

**What they ran:** "Cellulitis", insurance left as "I'm not sure", at 7:56 PM. The app matched the skin infection scenario (visit level 2 to 4, admission unlikely), showed no emergency banner (the safety screener rated it "urgent"), and gave a most-likely figure of $839 at the median insurer rate.

**Their answers**

1. Role: Radiology Oncology Resident
2. Cases tried: Cellulitis
3. Visit level and expected tests as predicted? "Yes (didn’t describe frequency or hospital admission portion)"
4. What do you tell patients today? "Won’t answer"
5. Would this be useful? "No, because you don’t want them to be influenced to seek emergency care based on pricing and can place a huge ethical conundrum"
6. Other tips: "It’s too complicated. The first part was easy and the second part was too much to read—unless you’re a healthcare provider"

## Runs seen in the test log on 22 November 2026 (first evening)

| Time | What was typed | Insurance | Red banner | Scenario the app used | Most-likely figure shown |
|---|---|---|---|---|---|
| 7:56 PM | Cellulitis | not sure | no | Skin infection | $839 |
| 8:08 PM | I rolled my ankle playing soccer an hour ago. It's swollen and hurts to walk on. | Aetna | no | Ankle or foot injury | $976 |
| 8:15 PM | Emphysema | not sure | no | Shortness of breath, asthma or COPD flare | $2,296 |
| 8:16 PM | Elbow dislocation | not sure | no | Wrist, hand or arm injury | $953 |

### What these runs changed

- **"Emphysema"** was a diagnosis with no description of what was happening, and the app priced a full flare-up workup. The safety screener now asks "what is happening today?" when the text is only the name of a long-term condition, and stops there.
- **"Elbow dislocation"** was priced as an arm X-ray visit ($953; list price about $1,700). The project author reports that this patient's real bill was **$17,000, with $0 out of pocket**. A draft "dislocated joint" scenario was added (X-rays before and after, putting the joint back under sedation, splint); with it the app's list price is $4,734 most likely and $6,686 at the high end, still far below the real bill. What the real bill included is not yet known.

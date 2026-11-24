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

## Tester 2 (23 November 2026)

**What they ran:** the cut-finger example, through the hosted link (https://ed-cost-estimator.onrender.com). Their reply quotes the app's range of $805 to $1,463 and mentions Anthem. This run is in the hosted copy's log, not in the laptop's `output/test_runs.jsonl`.

**Their answers** (this tester got the version of the questions written for non-clinicians)

1. Role: "patient"
2. Cases tried: "cut finger"
3. Do the dollar figures look believable next to what patients are actually billed? "would have no idea how to answer this since I don’t know what ppl are actually billed"
4. Today, if a patient asks "what will this cost me?", who answers, and how long does it take? "IDK— i would call the ED and idk who answer i assume the front desk receptionist. IDK if they handle billing. They probably don’t. It would prob be someone in the billing dept who calls the insurance with the procedure codes."
5. Would this be useful? "As a patient, this would be useful if I am budgeting AFTER my visit for how much the visit would potentially cost me once I get the bill in however many weeks/months later. It might be helpful if I don’t have a severe emergency and I want to compare which place to go to (a local urgent care center or one of various ED centers if I have a choice). otherwise, if I have an emergency, I prob need to go regardless of the cost…"
6. Other tips: "I would not trust AI unless I knew it had a proven history of accuracy and was trained on reliable data. Otherwise, I’m like… how the hell does AI know how much it would cost. Maybe if it displayed its sources (which lots of AI chats do nowadays if doing web search tool). I want to know what Anthem (insurance) list of procedure codes and costs it looked at to get the price. I also don’t really know how insurance works— is it a set price for every procedure? Some explanatory context could help about how the estimate is gotten…

   Like this is helpful in your tool: “The hospital-bill estimate ranges from $805 to $1,463; your cost depends on your plan and deductible, and the actual bill may differ. The emergency physician bills separately, and the visit level is assigned after care, so it cannot be known exactly in advance.”

   But then I’m like ok, what use is this? The uncertainty is too big. Like I can’t rely on this at all, because it’s too uncertain what the actual price would be differing from the estimated."

### What this reply points to (not yet changed in the app)

- **Trust needs the sources in view.** The app does list every billing code and the insurer's rate for each, but in a closed "More detail" row, where they were moved after Tester 1 said the page was too much to read. The two testers pull in opposite directions.
- **The range is too wide to act on.** $805 to $1,463 for one cut finger. Narrowing it needs the patient's plan details and a check against real bills.
- **Where a patient sees the use:** budgeting after a visit, and choosing between urgent care and an ED when it is not a severe emergency. In an emergency they would go regardless of cost.

## Other feedback (23 November 2026)

- **Care management providers in the emergency department** and **lawyers** who were shown the app said they liked it. No written answers were collected from them.
- **A review by another AI assistant**, asked by the author to evaluate the website, raised two problems that were fixed the same evening:
  - The page's code held both "what you type is saved" and "your text is not saved". Only one was ever shown at a time, but the page now carries only the statement that applies.
  - Blank plan details were counted as zero, which could understate what a patient owes. A blank is now unknown: "your share" appears only when copay, deductible left and coinsurance are all filled in.
- The same review suggested showing ranges in place of exact figures. The author kept exact figures, because a user she asked preferred them; the page says throughout that these are estimates.

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

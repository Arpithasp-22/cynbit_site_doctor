# AI Opportunity Report for Cynbit Technologies

**Prepared by:** Arpitha Satish Punya, AI/ML Engineer Intern assessment
**Date:** 30 October 2026

## 1. Executive summary

Cynbit is a young Jaipur-based company that sells AI automation and custom software to businesses, and also runs its own products and a training arm (BitElevate). That mix means AI can help in three places: the **learner and candidate journey** on its own platforms, the **client delivery business**, and **internal operations**.

Reading the website, the offer is clear but the proof is thin: products get a line each with no demos, and headline numbers (99.9% uptime, 3x ROI, 50k+ users) carry no period, baseline or source. I assessed seven opportunities and recommend a two-part project that answers both gaps:

- **Make the product tangible: SkillBridge.** An explainable resume-to-role matcher that turns a candidate's skill gaps into a personalised learning path, built as a live demo of Cynbit Studio's job-matching and career-preparation promise and a front door to BitElevate courses.
- **Back the claims: ProofKit.** A claim auditor that flags website claims a reader cannot check, and an evidence-gated case-study drafter that publishes only metrics with a baseline, period, source and client confirmation.

Both work offline on rules and need no proprietary data to prototype, and every result can be audited by a human. A working prototype of both is in this repository.

## 2. What I could verify about Cynbit

This report is based only on publicly available information. I could not open every page of cynbit.in directly, so product detail comes mostly from third-party summaries and the company's GitHub organisation page.

| Item | What public sources say |
|---|---|
| Location and age | Jaipur, Rajasthan. Incorporated 2 April 2024 per MCA-derived registry listings. |
| Size | Sources disagree: 11-50 employees (Crunchbase) vs 20+ (a LinkedIn-derived profile). |
| Positioning | Homepage: AI automation, autonomous agents, custom software and cloud architecture. |
| Services | AI automation, software development, cloud solutions, digital marketing (Crunchbase). |
| Products | Cynbit Studio (career intelligence), Revio AI (review assistant), TenantEase (property ecosystem), per the homepage. Crunchbase adds that Studio supports coding practice, AI code evaluation, career preparation and job matching. The homepage gives each product only a few words. |
| Training | BitElevate: full-stack development, AI, data science, cloud, cybersecurity, digital marketing. GitHub page adds mock interviews and AI mentorship to Studio. |

**Gaps in my knowledge, stated plainly:** beyond one-line descriptions I found nothing on what TenantEase and Revio AI actually do or whether they are live, so opportunity 4 below is marked unverified. I read the homepage and Our Story page as text only; I did not assess visual design, mobile layout, page speed or SEO. Everything about Cynbit's internal data, volumes and tooling is unknown to me. The scores below are my judgement, not measurements.

## 3. What the website shows, and what is missing

Observed in a text read of cynbit.in on 30 October 2026. These are observations about evidence and detail, not criticism of the offer itself.

| Area | Observation | Why it matters |
|---|---|---|
| Statistics | 99.9% uptime, 98% retention, 3x ROI, 50k+ users, 1000+ certified architects, 25k+ newsletter subscribers, and "100% success" for one client appear with no period, baseline or source. | Unsourced numbers invite doubt; one absolute claim ("100%") is hard to defend. |
| Case studies | Client logos and testimonials appear, but the people quoted and the outcomes are not explained. | Buyers of custom software want problem, approach and measured result. |
| Products | Cynbit Studio, Revio AI and TenantEase get a few words each: no features, demo, screenshots or pricing. | Visitors cannot tell what is live or try anything. |
| Interface | Elements such as a sample "Certified Software Architect" badge, "Active now" and an "Automation 95% efficiency" widget look like mockups. | Decorative data can be read as real data. |
| Story page | No founders, team or named clients; milestone labels differ from their text; "zero-trust modules" is never explained. | Trust signals for a young company. |
| Small errors | A newsletter button reads "Join the Newslettereast"; one heading does not match its description. | Easy fixes that affect polish. |
| Process and pricing | A six-step process is shown, but no engagement model, timeline or pricing. | Leaves the first sales conversation to start from zero. |

The claim auditor in this repository checks 13 claims taken from these pages. It rates 9 as high priority (no period, baseline or source), 1 medium and 3 low, and none as fully supported on the page. That does not mean any claim is false; it means the page does not let a reader check it.

## 4. Opportunity long-list

Scoring is my subjective 1-5 judgement. Impact is the value if it works, Feasibility is how achievable it is for a small team in weeks, Data is how likely the needed data exists or can be obtained, Risk is lower-is-better.

| # | Opportunity | Where | Impact | Feasibility | Data | Risk |
|---|---|---|---|---|---|---|
| 1 | **Skills-gap matching and personalised learning paths** (SkillBridge) | Studio, BitElevate | 4 | 5 | 4 | 2 |
| 2 | Rubric-based AI code review with calibrated feedback and hint ladders | Studio | 4 | 4 | 3 | 3 |
| 3 | Learner drop-off prediction and nudges | BitElevate | 3 | 3 | 2 | 2 |
| 4 | Maintenance-request triage and tenant Q&A assistant (unverified fit) | TenantEase | 3 | 4 | 2 | 3 |
| 5 | RAG assistant over past proposals and delivery docs, plus proposal drafting | Services | 3 | 4 | 3 | 2 |
| 6 | SEO content briefs and automated campaign reporting | Digital marketing | 3 | 4 | 4 | 2 |
| 7 | Assistive resume screening for Cynbit's own hiring | Internal | 2 | 4 | 3 | 5 |
| 8 | **Claim audit and evidence-gated case studies** (ProofKit) | Website, services | 3 | 5 | 4 | 1 |

### Short rationale for each

1. **SkillBridge.** Candidates often do not know which role fits or what to learn next. Matching resumes to role profiles and mapping gaps to courses links two things Cynbit already operates (a job-matching feature and a training catalogue). It can also generate leads for BitElevate courses.
2. **AI code review.** Studio already advertises AI code evaluation, so the opportunity is quality: consistent rubrics, explanations that teach instead of just grading, and regression tests on the grader. Needs a set of graded submissions to calibrate against.
3. **Drop-off prediction.** Standard supervised learning on engagement logs. Value is real but depends on having enough historical cohorts, which a 2024-founded company may not yet have.
4. **TenantEase assistant.** Triage and FAQ automation is a common pattern in property tools. Unverified because I do not know the product.
5. **Internal RAG.** Fast to build with embeddings plus an LLM. The quality ceiling depends on how well past documents are kept.
6. **Marketing tooling.** Useful for the services arm and as a client-facing offering, but crowded and mostly an LLM-wrapper play with little defensibility.
7. **Resume screening.** Highest risk. Automated screening of people raises fairness and legal concerns, so I would only ever treat it as decision support with a human in charge.
8. **ProofKit.** Answers the website's biggest gap directly. Auditing claims is rule-based and cheap; drafting case studies from structured evidence turns a slow, ad hoc writing task into a checklist the team can send to clients. Low risk because it never publishes anything without a human and client approval.

## 5. Why these two projects

### SkillBridge (makes the product tangible)

- **Fit with strategy.** Cynbit's own public material emphasises "practical" AI, and its learning products need a way to connect assessment results to next steps.
- **Low data barrier.** A role taxonomy and course catalogue are things the company can write down in days. No model training data is needed for version 1.
- **Explainable.** Every skill detected carries an evidence snippet, and every fit score decomposes into matched and missing skills. That matters when the output affects someone's career.
- **Incremental path to ML.** Start rule-based and measurable, then add embeddings and learned ranking once real outcome data exists (see the technical approach report).
- **Double use.** The same engine can power candidate-facing guidance in Studio, course recommendations in BitElevate, and (carefully) shortlisting for client hiring projects.

### ProofKit (backs the claims)

- **Addresses what the site lacks.** A clear offer, but numbers without context and no case-study write-ups.
- **Honest by design.** A metric is published only with a baseline, a period, a source and client confirmation; the rest is held back and turned into a request list for the client.
- **Auditable.** The auditor explains why each claim was flagged and what to add. It never calls a claim false.
- **Safe use of an LLM.** The optional wording pass is rejected automatically if it adds or removes any number.
- **Reusable as a service.** The same workflow could be offered to Cynbit's own digital-marketing and software clients.

## 6. Risks and responsible-AI considerations

- **Bias.** Matching on keywords can disadvantage people who describe the same skills differently. Mitigations: show evidence, let users correct detected skills, audit results across groups once real data exists, never auto-reject.
- **Privacy.** Resumes are personal data. India's Digital Personal Data Protection Act, 2023 applies to processing of such data; Cynbit should confirm obligations with counsel before production use. The prototype stores nothing and the sample data is synthetic.
- **Over-trust in a score.** A "82% fit" can look more precise than it is. The UI should present it as guidance, alongside the reasons.
- **LLM hallucination.** The optional LLM step is restricted to rephrasing a JSON of computed facts, with a deterministic fallback.
- **Publishing client results (ProofKit).** Case studies need the client's written approval, including for named quotes. Drafts are marked as requiring approval, and unverified metrics never appear unless explicitly shown with a warning label. The auditor can over-flag (for example, a claim whose source sits on another page), so its output is a review list, not a verdict.

## 7. How success would be measured

| Metric | Why |
|---|---|
| Precision@3 against recruiter or mentor judgement on real resumes | Does the ranking agree with humans? |
| Skill-extraction precision and recall on a hand-labelled set | Catches taxonomy gaps and false positives |
| Share of users who start a recommended course | Does the advice get used? |
| Time from sign-up to first course enrolment | Funnel speed |
| Placement or interview rate for guided vs unguided learners (A/B) | The outcome that matters, measured only with consent and enough volume |
| Share of site claims with period, baseline and source after the audit | Direct measure of ProofKit's effect on the website |
| Time to produce an approved case study, and share of drafts approved by clients on first send | Shows whether the evidence checklist saves effort |

## 8. Recommended roadmap

1. **Weeks 1-2:** replace the illustrative roles and courses with Cynbit's real ones; collect 100+ anonymised, consented resumes with mentor-assigned target roles.
2. **Weeks 3-4:** measure extraction and ranking accuracy on that set, expand aliases, add skill-level (beginner/advanced) signals.
3. **Weeks 5-8:** add embedding-based soft matching for unseen skills, plug into Studio assessments as an input, ship behind a feature flag to a pilot cohort.
4. **After the pilot:** learn from outcomes (course completion, interviews) to tune weights, and evaluate opportunity 2 (code review) as the next project.
5. **In parallel (ProofKit):** run the claim audit on the live site and fix the high-priority items first; collect evidence from two or three willing clients using the generated request list; publish the first approved case studies and link them from "View work".

## Sources

- [Crunchbase profile for Cynbit Technologies](https://www.crunchbase.com/organization/cynbit-technologies)
- [Cynbit Technologies GitHub organisation profile](https://github.com/Cynbit-Technologies/.github)
- [Cynbit homepage](https://www.cynbit.in/) and [Our Story page](https://www.cynbit.in/story)
- [Falcon Ebiz registry listing](https://www.falconebiz.com/company/CYNBIT-TECHNOLOGIES-PRIVATE-LIMITED-U62011RJ2024PTC093652) and [ZaubaCorp listing](https://www.zaubacorp.com/company/U62011RJ2024PTC093652) (incorporation date, registered office)
- [Village company profile](https://village.ai/company/cynbit-in) (headcount figure)

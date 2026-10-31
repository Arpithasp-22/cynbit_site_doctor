# What is this? (the plain-language version)

## The idea in one sentence

**A doctor's checkup for a website.** It reads the site, tells the owners what is weak, in what order to fix it, and hands them the fixes. It also includes a small AI assistant that shows what a visitor-facing assistant on Cynbit's own site could do.

## Why this, for Cynbit?

Cynbit sells AI and software. Its website explains the offer well, but a buyer can't *check* it:

* Numbers like "99.9% uptime" and "3x ROI" don't say **when** they were measured, **compared to what**, or **by whom**.
* The one case study I read says "35% improvement in client ROI" with no starting figure, no period and no source.
* The three products are described in words, but there is no status (live or beta), no price signal and no screenshots.
* A visitor with a question the site does not answer has nowhere to go except a form.

People are interested in AI but careful about hype. In a LinkedIn study of Indian small businesses (reported by Business Standard), 95% said a platform's credibility matters more than cost or convenience. So the most useful thing an AI intern can build is not another chatbot; it is a way to **make the site believable and easier to use**, and to prove it with a working demo.

## What each screen does

| Screen | What you see | What is happening underneath |
|---|---|---|
| **Home: the checkup** | A scorecard, a short "start here" list, and every finding with *what's wrong, why it matters, where, how to fix it*. | A robot visitor (the "crawler") opens each page. 23 checklist-style checks run on what it found. Each problem is scored by how serious it is and how many pages it affects. |
| **Fix Pack** | Tables you can copy: claims to back up, what each offer page is missing, title and description drafts, a contact-form plan. | The tool turns each finding into a ready-to-use draft, such as a template: "[Metric] changed from [BASELINE] to [VALUE] over [PERIOD], measured by [SOURCE]". People still approve every change. |
| **Ask Cynbit** | A chat box. Ask "How much does BitElevate cost?" and get an answer plus the page it came from. Ask "What is the price of Studio?" and it says it could not find that. | It cuts the website into small passages, finds the passage most like your question, and answers **only if** the passage really contains your key words. Otherwise it declines and offers to pass the question to the team. Declined questions are grouped by topic: that list is the content the website still needs. |
| Extras | A case-study drafter and a resume matcher from my first attempt. | Same idea of "only publish what is evidenced". Not part of the main story. |

## Two examples to follow

**Example 1: a weak claim.** The homepage says "Marketing Addict: +40% growth in organic leads". The checkup flags it because the page gives no period, no starting number and no source. The Fix Pack says what to ask the client for and gives a sentence template. A flag does **not** mean the claim is false, only that a reader cannot check it.

**Example 2: a missing answer.** A visitor asks the assistant, "What is the price of Cynbit Studio?" The site never says. The assistant refuses to guess, invites the visitor to leave an email (a lead for the sales team), and logs the question. After a few days the log shows "pricing" as a top unanswered topic, which tells the web team what to write.

## Where the AI and machine learning are

* **Ask Cynbit** uses machine-learning text search (TF-IDF vectors and cosine similarity) to find the right passage, a rule that decides when to answer or decline, and clustering to group the unanswered questions.
* An LLM can optionally phrase answers, but it is **fenced in**: it only sees the retrieved passages, and its reply is thrown away if it contains any number that is not in them.
* The **checkup itself is rules, not machine learning**, on purpose. Each rule can say exactly why it fired, which matters when someone edits a real website because of it. A trained model would need examples of "good" and "bad" sites that we don't have.

## How well does it work? (honest numbers)

On 34 test questions I wrote myself, the assistant declined **every** question the site cannot answer, and gave a correct, sourced answer to about **59 to 64%** of the questions the site can answer. It prefers "I don't know" to making something up. The set is small and written by me, so treat it as a baseline.

## What it cannot do yet

* I could not scan cynbit.in directly from my environment, so the live scan was tested on a fake website with planted problems. **Run the live scan on your own computer** (sidebar: "Scan a live website").
* The built-in snapshot is paraphrased text, so it cannot show markup problems; those categories say "needs live scan" instead of a made-up score.
* Some findings come from my reading of the pages and are labelled "found by reading".
* Search is word-based, so it misses some questions asked in different words. Sentence embeddings are the planned upgrade.

## How Cynbit would use it

1. Run a scan; fix the quick wins (a day of work).
2. Collect evidence from clients using the generated request list; publish better case studies.
3. Put the assistant on the site; read the weekly "unanswered questions" list; write what is missing.
4. Rescan weekly. The score trend shows whether the work paid off. The same service could be offered to Cynbit's own clients.

## Glossary

* **Crawler**: a program that opens web pages and follows links, like a very fast visitor.
* **Baseline**: the starting value you compare a result against ("leads were 100 a month before").
* **TF-IDF / cosine similarity**: a standard way to turn text into numbers so that passages about the same words end up close together.
* **Threshold**: a cut-off. Below it the assistant says "I don't know".
* **Guardrail**: an automatic check that rejects an AI answer if it breaks a rule (here: adding numbers not found on the site).
* **Lead**: a visitor who leaves contact details.

## A 2-minute demo you can follow

1. **Home**: "This is a checkup. Overall score, then the most useful fixes first. Open 'Case study has results but no baseline' to see what, why and how to fix."
2. **Fix Pack, first tab**: "Here are the claims the site cannot back up, each with a sentence template."
3. **Ask Cynbit**: ask "How much does BitElevate cost?" (answers with a source), then "What is the price of Cynbit Studio?" (declines, captures a lead). Tick the box for example questions to show the "what the website is missing" list.
4. **Sidebar, Scan a live website**: "This runs every check on the real pages, including titles, links and forms."
5. Close: "Limits: tested on a fake site and on a snapshot; the next step is the live scan and real visitor questions."

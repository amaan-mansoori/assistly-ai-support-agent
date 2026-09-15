# Brand Comparison Deep-Dive Report

Candidates: AmazonHelp, AppleSupport, SpotifyCares

> **Note**: All statistics computed locally from `data/raw/twcs/twcs.csv`.
> No LLM/API calls were used. Exploratory themes are NOT final intents.

---
## AmazonHelp

### A. Data Volume
| Metric | Value |
|---|---|
| Brand outbound tweets | 169,840 |
| Linked customer tweets | 154,985 |
| Outbound with in_response_to | 169,287 (99.7%) |
| Customer->brand pairs | 154,985 (91.3% of outbound) |

### B. Conversation Quality
| Metric | Value |
|---|---|
| Total threads | 86,672 |
| Mean thread length | 3.75 |
| Median thread length | 2 |
| Max thread length | 116 |
| >=2 turns | 100.0% |
| >=3 turns | 47.8% |
| Customer->Brand pattern | 100.0% |
| Linkage reliability | 91.6% |

Thread length distribution:
| Length | Count |
|---|---|
| 1_turn | 29 |
| 2_turns | 45,213 |
| 3_turns | 4,412 |
| 4_turns | 18,949 |
| 5plus_turns | 18,069 |

### C. Customer Issue Diversity (Exploratory)
> [!] These are exploratory themes from TF-IDF analysis, NOT the final intent taxonomy.

Texts analyzed: 142,113

**Top bigrams (by mean TF-IDF):**
| Bigram | Score |
|---|---|
| customer service | 0.006 |
| amazon prime | 0.00439 |
| day delivery | 0.00343 |
| day shipping | 0.00281 |
| customer care | 0.00257 |
| delivery date | 0.00213 |
| prime membership | 0.00204 |
| delivered today | 0.0018 |
| amazon amazon | 0.00167 |
| amazon logistics | 0.00164 |
| don know | 0.00157 |
| prime member | 0.00152 |
| amazon pay | 0.00151 |
| haven received | 0.00146 |
| cancel order | 0.00133 |

**Exploratory themes:**
1. customer service
2. amazon prime
3. day delivery
4. delivered today
5. don know
6. haven received
7. cancel order
8. credit card
9. need help
10. package
11. email
12. days
13. que
14. ordered
15. ve

### D. Resolution Signal
Total outbound: 169,840

| Category | Count | Pct |
|---|---|---|
| substantive | 139,116 | 81.9% |
| dm_redirect | 1,326 | 0.8% |
| contact_redirect | 9,577 | 5.6% |
| generic_greeting | 17,040 | 10.0% |
| acknowledgement_only | 0 | 0.0% |
| very_short | 2,781 | 1.6% |
| empty | 0 | 0.0% |

### E. Customer Message Quality
| Metric | Value |
|---|---|
| Customer tweets (with text) | 154,985 |
| Mean char length | 116.2 |
| Median char length | 116.0 |
| Very short (<20 chars core) | 7,048 (4.5%) |
| Noise (mentions/one-word) | 454 (0.3%) |
| Looks like support request | 129,213 (83.4%) |
| Unique texts | 152,417 |
| Duplicate rate | 1.7% |

### F. Golden Set Feasibility
| Metric | Value |
|---|---|
| Request-like messages | 129,213 |
| Exploratory themes | 15 |
| Est. examples per theme | 8,614 |
| **Verdict** | **FEASIBLE** |

### G. RAG / Retrieval Feasibility
| Metric | Value |
|---|---|
| Outbound with linkage | 169,287 |
| Substantive responses | 139,116 |
| Usable (customer+substantive) pairs | 138,264 |
| Usable pair % of outbound | 81.4% |
| **Verdict** | **FEASIBLE** |

---
## AppleSupport

### A. Data Volume
| Metric | Value |
|---|---|
| Brand outbound tweets | 106,860 |
| Linked customer tweets | 106,625 |
| Outbound with in_response_to | 106,719 (99.9%) |
| Customer->brand pairs | 106,625 (99.8% of outbound) |

### B. Conversation Quality
| Metric | Value |
|---|---|
| Total threads | 82,105 |
| Mean thread length | 2.6 |
| Median thread length | 2 |
| Max thread length | 252 |
| >=2 turns | 100.0% |
| >=3 turns | 21.1% |
| Customer->Brand pattern | 100.0% |
| Linkage reliability | 99.9% |

Thread length distribution:
| Length | Count |
|---|---|
| 1_turn | 4 |
| 2_turns | 64,742 |
| 3_turns | 127 |
| 4_turns | 12,570 |
| 5plus_turns | 4,662 |

### C. Customer Issue Diversity (Exploratory)
> [!] These are exploratory themes from TF-IDF analysis, NOT the final intent taxonomy.

Texts analyzed: 102,687

**Top bigrams (by mean TF-IDF):**
| Bigram | Score |
|---|---|
| ios 11 | 0.01716 |
| new update | 0.00473 |
| battery life | 0.00416 |
| iphone 6s | 0.00401 |
| question mark | 0.004 |
| fix shit | 0.00382 |
| ios update | 0.0037 |
| iphone plus | 0.00359 |
| new ios | 0.00346 |
| updated phone | 0.00326 |
| update phone | 0.00304 |
| new iphone | 0.00303 |
| doesn work | 0.00298 |
| apple music | 0.00297 |
| 11 update | 0.00289 |

**Exploratory themes:**
1. ios 11
2. new update
3. battery life
4. iphone 6s
5. question mark
6. fix shit
7. updated phone
8. doesn work
9. apple music
10. type letter
11. high sierra
12. app
13. problem
14. issue
15. ios11

### D. Resolution Signal
Total outbound: 106,860

| Category | Count | Pct |
|---|---|---|
| substantive | 44,551 | 41.7% |
| dm_redirect | 56,126 | 52.5% |
| contact_redirect | 1,675 | 1.6% |
| generic_greeting | 4,241 | 4.0% |
| acknowledgement_only | 0 | 0.0% |
| very_short | 267 | 0.2% |
| empty | 0 | 0.0% |

### E. Customer Message Quality
| Metric | Value |
|---|---|
| Customer tweets (with text) | 106,625 |
| Mean char length | 109.3 |
| Median char length | 108.0 |
| Very short (<20 chars core) | 4,459 (4.2%) |
| Noise (mentions/one-word) | 423 (0.4%) |
| Looks like support request | 90,866 (85.2%) |
| Unique texts | 104,347 |
| Duplicate rate | 2.1% |

### F. Golden Set Feasibility
| Metric | Value |
|---|---|
| Request-like messages | 90,866 |
| Exploratory themes | 15 |
| Est. examples per theme | 6,057 |
| **Verdict** | **FEASIBLE** |

### G. RAG / Retrieval Feasibility
| Metric | Value |
|---|---|
| Outbound with linkage | 106,719 |
| Substantive responses | 44,551 |
| Usable (customer+substantive) pairs | 44,368 |
| Usable pair % of outbound | 41.5% |
| **Verdict** | **FEASIBLE** |

---
## SpotifyCares

### A. Data Volume
| Metric | Value |
|---|---|
| Brand outbound tweets | 43,265 |
| Linked customer tweets | 41,697 |
| Outbound with in_response_to | 43,243 (99.9%) |
| Customer->brand pairs | 41,697 (96.4% of outbound) |

### B. Conversation Quality
| Metric | Value |
|---|---|
| Total threads | 29,890 |
| Mean thread length | 2.84 |
| Median thread length | 2 |
| Max thread length | 72 |
| >=2 turns | 100.0% |
| >=3 turns | 27.6% |
| Customer->Brand pattern | 100.0% |
| Linkage reliability | 96.4% |

Thread length distribution:
| Length | Count |
|---|---|
| 1_turn | 3 |
| 2_turns | 21,648 |
| 3_turns | 739 |
| 4_turns | 4,512 |
| 5plus_turns | 2,988 |

### C. Customer Issue Diversity (Exploratory)
> [!] These are exploratory themes from TF-IDF analysis, NOT the final intent taxonomy.

Texts analyzed: 39,872

**Top bigrams (by mean TF-IDF):**
| Bigram | Score |
|---|---|
| premium account | 0.00392 |
| spotify premium | 0.0039 |
| need help | 0.00337 |
| spotify account | 0.00287 |
| ios 11 | 0.00265 |
| family plan | 0.00253 |
| student discount | 0.00241 |
| web player | 0.00216 |
| premium family | 0.00195 |
| spotify app | 0.00193 |
| family account | 0.00192 |
| discover weekly | 0.00184 |
| email address | 0.0018 |
| credit card | 0.00179 |
| spotify version | 0.00177 |

**Exploratory themes:**
1. premium account
2. need help
3. ios 11
4. family plan
5. student discount
6. web player
7. spotify app
8. discover weekly
9. email address
10. credit card
11. new album
12. apple music
13. doesn work
14. customer service
15. won let

### D. Resolution Signal
Total outbound: 43,265

| Category | Count | Pct |
|---|---|---|
| substantive | 12,916 | 29.9% |
| dm_redirect | 13,351 | 30.9% |
| contact_redirect | 86 | 0.2% |
| generic_greeting | 16,879 | 39.0% |
| acknowledgement_only | 0 | 0.0% |
| very_short | 33 | 0.1% |
| empty | 0 | 0.0% |

### E. Customer Message Quality
| Metric | Value |
|---|---|
| Customer tweets (with text) | 41,697 |
| Mean char length | 103.8 |
| Median char length | 100.0 |
| Very short (<20 chars core) | 2,205 (5.3%) |
| Noise (mentions/one-word) | 184 (0.4%) |
| Looks like support request | 34,178 (82.0%) |
| Unique texts | 40,975 |
| Duplicate rate | 1.7% |

### F. Golden Set Feasibility
| Metric | Value |
|---|---|
| Request-like messages | 34,178 |
| Exploratory themes | 15 |
| Est. examples per theme | 2,278 |
| **Verdict** | **FEASIBLE** |

### G. RAG / Retrieval Feasibility
| Metric | Value |
|---|---|
| Outbound with linkage | 43,243 |
| Substantive responses | 12,916 |
| Usable (customer+substantive) pairs | 12,883 |
| Usable pair % of outbound | 29.8% |
| **Verdict** | **FEASIBLE** |

---
## Summary Comparison Table

| Metric | AmazonHelp | AppleSupport | SpotifyCares |
|---|---|---|---|
| Outbound volume | 169,840 | 106,860 | 43,265 |
| Usable customer->brand pairs | 154,985 | 106,625 | 41,697 |
| Total threads | 86,672 | 82,105 | 29,890 |
| >=2 turn conv. rate | 100.0% | 100.0% | 100.0% |
| >=3 turn conv. rate | 47.8% | 21.1% | 27.6% |
| Substantive response rate | 81.9% | 41.7% | 29.9% |
| DM redirect rate | 0.8% | 52.5% | 30.9% |
| Issue themes found | 15 | 15 | 15 |
| Duplicate/noise rate | 1.7% | 2.1% | 1.7% |
| Looks like request % | 83.4% | 85.2% | 82.0% |
| Golden set verdict | FEASIBLE | FEASIBLE | FEASIBLE |
| RAG verdict | FEASIBLE | FEASIBLE | FEASIBLE |

---
## Data-Driven Recommendation

*(Auto-generated from the metrics above — final brand selection
should be reviewed by a human.)*

- **AmazonHelp**: composite score = 30.47
- **AppleSupport**: composite score = 27.12
- **SpotifyCares**: composite score = 26.02

**Recommendation: AmazonHelp** appears strongest based on the combined metrics.

This recommendation should be validated by reviewing:
1. The sample messages and themes for domain familiarity
2. Whether the exploratory themes map to distinct, labelable intents
3. Whether the substantive responses contain actual resolution info

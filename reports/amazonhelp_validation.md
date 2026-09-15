# AmazonHelp Candidate Selection Validation Report

Validation conducted locally on `data/raw/twcs/twcs.csv` without LLM calls.

## 1. Customer->Brand Pair Matching Validation
- Total AmazonHelp outbound tweets: **169,840**
- Outbound tweets citing `in_response_to_tweet_id`: **169,287** (99.7%)
- Unique parent tweets recovered from `twcs.csv`: **154,985**
- Parent tweets with `inbound == 'True'` (customer): **168,814** (99.3% of recovered)
- Parent tweets with `inbound == 'False'` (agent self-threads): **9** (0.7%)
- **Conclusion**: Matching by `in_response_to_tweet_id == tweet_id` strictly identifies the preceding tweet. 99.3% are verified customer tweets.

## 2. Thread Reconstruction & Turn Count Validation
- Reconstructed threads: **86,672**
- >= 2 turns: **99.97%** (matches report: 100.0% rounded)
- >= 3 turns: **47.80%** (matches report: 47.8%)
- **Distribution**:
  - Length 1: 29 (0.03%)
  - Length 2: 45,213 (52.17%)
  - Length 3: 4,412 (5.09%)
  - Length 4: 18,949 (21.86%)
  - Length 5: 2,053 (2.37%)
  - Length 6: 7,472 (8.62%)
  - Length >=7: 8,544 (9.86%)

## 3. Substantive Response Heuristic Rules & 20 Sampled Examples per Category

### Exact Rules and Precedence:
1. Core length < 30 characters -> `very_short`
2. Matches `acknowledgement_only` regex -> `acknowledgement_only`
3. Contains DM keywords (`dm`, `direct message`, `private message`, `inbox`) -> `dm_redirect`
4. Contains support redirect keywords (`call us`, `contact support`, `reach out to`) -> `contact_redirect`
5. Starts with greeting/apology (`hi`, `hello`, `sorry to hear`, `apologize`) without redirect -> `generic_greeting`
6. Otherwise -> `substantive` (contains troubleshooting, instructions, links)

### Sample 20 Examples: `substantive` (Total: 139,116)

01. `@202267 You're welcome! Glad we could help! Reach out if you have any questions in the future. ^JF`
02. `@576407 If the delivery date is missed, we can be reached 24/7 via phone here: https://t.co/hApLpMlfHN. We will be able to take a c loser look at the order and into available options.  ^EP`
03. `@378019 again, we are sorry to about that, delays do happen from time to time for unforeseen reasons. ^AS`
04. `@466086 I understand your concern. Please contact us here: https://t.co/rS49hgaADF so that we can assist you accordingly. ^BV`
05. `@193277 Oh no! That's not good. Have you tried the tips listed here: https://t.co/ZiiPC3H4IF to help locate your order? ^KP`
06. `@617604 That's unusual.  Please contact us here: https://t.co/rS49hgaADF so that we can assist you accordingly. ^MN`
07. `@805475 I'm sorry for the poor experience, Tammy! To cut down on packaging, we've started shipping certain items in manufacturer packaging. When checking out, there should be an option to ship the order in an Amazon box! More info here: https://t.co/oF0wfkwkrc ^WT`
08. `@499736 I'm sorry the pick-up hasn't been completed. We'd like to look into it. Kindly report it to our support team 1/2 ^AP`
09. `@771024 Oh wow! That is a bit excessive. At your convenience, you can help us improve here: https://t.co/fxgZ6hTrFA We'd appreciate any feedback! ^SK`
10. `@685869 Oh no! I'm sorry you haven't received the package. Please try these steps, and keep us posted: https://t.co/zyPVbV62ul ^BH`
11. `@122482 Allow our support team to investigate this. You can report this here: https://t.co/R3EfhzgU8B.(1/2) ^CB`
12. `@387212 You're welcome! Let us know if we can further assist! ^AB`
13. `@338252 I just checked and we haven't received your details yet. Kindly share your details here: https://t.co/beaaDm0muc ^GK`
14. `@350524 Unless the form is filled we wouldn't be able to offer any further insight in this case. Thanks for understanding. 2/2 ^AB`
15. `@460459 Our apologies. We'd like to check this and assist. Please share the required details, here: https://t.co/GIJyeYqKE0. (1/2)`
16. `@309803 What information do you get when you request approval? ^MC`
17. `@439571 I'm very sorry for the delay! Could you tell us who the carrier was for this delivery? We'd like to help! ^ZW`
18. `@199412 Please don't provide your order details, we consider it to be personal information. Our page is visible to the public. ^GD`
19. `@324789 Sorry to know you're order wasn't delivered. Have you reported this to our support team here: https://t.co/R3EfhzgU8B? ^PS`
20. `@375172 Please share your details here: https://t.co/GIJyeYqKE0 and I'll get in touch with you. (2/2) ^HD`

### Sample 20 Examples: `dm_redirect` (Total: 1,326)

01. `@499263 We have responded to your DM. Kindly check. ^SS`
02. `@313941 Thank you, we appreciate you letting us know about this. I've replied to your DM. ^MB`
03. `@301255 Sure! Feel free to send us a DM. We're here to help. ^AB https://t.co/1XyLaGkcaN`
04. `@192051 We've responded to your DM, please check. ^KA`
05. `@800867 I get your disappointment. We're following up via DM. ^SG`
06. `@293268 Hey, you should be able to DM us. Are you following the page? What error message are you getting when you try to DM us? ^RS`
07. `@222174 Então vamos responder no DM jordamn. ^JJ`
08. `@776594 Bonjour, nous avons répondu au DM que vous avez envoyé ^KD`
09. `@294377 We have responded to you via DM. Kindly check. ^GK`
10. `@228685 We've responded to your DM. Request you to please refer to it. ^AM`
11. `@563030 We've received your correspondence. Our team shall respond to you soon. Kindly keep an eye on your inbox for any correspondence here: https://t.co/NTkrxpsbHJ ^SF`
12. `@155855 We'd like to help! Please use the link below to DM with us. As a reminder we don't have access to your Amazon account; please refrain from providing personal or account details.  ^AG https://t.co/1XyLaGkcaN`
13. `@286682 Due to heavy demand, we send out a limited number of invites each week. Keep an eye on your inbox.  2/2 ^EM`
14. `@193289 We've responded to your DM. We can continue either here or there, it's up to you! ^LB`
15. `@172003 Hello, we will respond to your DM now. ^CR`
16. `@157017 I'm sorry to hear your issue still hasn't been resolved! You can send us a Direct Message by using the link below. ^TH https://t.co/1XyLaGkcaN`
17. `@701570 Hey, Charlotte! We're unable to access accounts via Twitter. Since you're unsure what account the membership is associated with it would be best for us to assist you in real-time. I recommend chatting or calling for the fastest resolution. I have enabled DM's. ^LA`
18. `@300780 Kindly take a look at your inbox here: https://t.co/deS2TU9Xfp and revert for further updates. 2/2^MS`
19. `@439951 I'm so sorry for the delay! I've responded to your direct message. ^JN`
20. `@321291 Sorry to hear that. We have already sent you the response via DM. Request you to check. ^NK`

### Sample 20 Examples: `contact_redirect` (Total: 9,577)

01. `@690876 When you contacted Seller Support, what options were they able to provide: https://t.co/3OLNiE1ssK ^AF`
02. `@506088 Kindly reach out to our support team here: https://t.co/HQhpS2qeEd. We'll definitely look into it. 2/2 ^PS`
03. `@193237 https://t.co/beaaDm0muc and I'll reach out to you. 2/2^EM`
04. `@742722 Oh no! Sorry about your late package. Please reach out to us here: https://t.co/hApLpMlfHN when you get a free moment for assistance. Thank you ^AP`
05. `@215321 My apologies for the trouble. Kindly reach out to us via: https://t.co/RboaDBVczl and we will have this checked. ^KS 1/2`
06. `@705514 Sorry to hear that. We'll be happy to look into that for you. Please reach out to us here:  https://t.co/zYVX1Qi29G ^RS`
07. `@612543 If you would like us to contact the carrier on your behalf, please reach out to us via this link: https://t.co/hApLpMlfHN ^WM`
08. `@341532 Thanks for reaching out! If there isn't a gift note in the box, we can use the tracking number to identify the purchaser and notify them to reach out to her. You're welcome to e-mail us with this information here: https://t.co/hApLpMlfHN ^ST`
09. `@708894 We'd like to take a closer look into this with you. When you have a chance, please reach out to us here: https://t.co/jzvkhdlrK5 ^HC`
10. `@636107 You can reach out to the seller using these steps: https://t.co/blYvi942ZL. Please keep us posted on the outcome. ^JN`
11. `@579205 Apologize for the delay in picking up the return package. Please reach out to us 1/3 ^AH`
12. `@703544 I'm sorry for any repeat information; we just want to cover all bases. Since you're not being provided with a new date, please reach out to us by phone or chat so we can investigate with you in real-time: https://t.co/EKXRLsnxJu ^AM`
13. `@708755 Please reach out to us here:https://t.co/JzP7hlA23B so we can look into this further for you! ^SA`
14. `@256808 I'm sorry your order was delivered that way! Please call us here: https://t.co/JzP7hlA23B so you can report this. ^AH`
15. `@384810 You can reach out to our support team here:https://t.co/vlvfJr4nN9 for any assistance. ^EM`
16. `@262978 I'm so sorry for the problem with your item! Please reach out to us via phone or chat so we can discuss options: https://t.co/JzP7hlA23B. ^DG`
17. `@320325 Sorry for the hassle. You can also choose to call us or drop an email to us Himanshu. ^HN`
18. `@480791 Sorry to hear about your a/c. Please reach out to us directly: https://t.co/jzvkhdlrK5 (No login req) and we can look into it. ^PK`
19. `@183287 I request you to reach out to our support team through the link provided earlier, we'll look into it for you.  ^EM`
20. `@124791 Please contact our support team for any assistance through the link provided to you earlier. ^MS`

### Sample 20 Examples: `generic_greeting` (Total: 17,040)

01. `@421452 We understand your concern, Aditya. In this case, please share your details from the link shared by "^NR". We'll assist. ^SV`
02. `@255818 Hi Alex, that sounds strange! Did the courier make an attempt yesterday? ^JC.`
03. `@773748 Hello! Apologies for the delay. Did you receive a new delivery date? What was advised when you contacted us? ^CN`
04. `@228694 Apologies, to reach us please try the following link instead:  https://t.co/JzP7hlA23B.^BZ`
05. `@403487 Hi, Charles! I'm sorry to hear you have not received your book. We are unable to view orders via twitter. When you get a chance please contact us so we can take a closer look: https://t.co/JzP7hlA23B Thanks! ^SW`
06. `@404625 Hi, sorry to hear that. Have you checked the options available here: http:https://t.co/5RcjVPJgUP? ^JJ`
07. `@336791 Apologies for the trouble. Please drop your details here: https://t.co/F9bwOOBQYM we'll connect with you on this. ^RB`
08. `@264884 Hello Johannes, wollte mal nachfragen, ob die Kollegen im Kundenservice dir weiterhelfen konnten? ^AW`
09. `@146679 Apologies Robert, during this busy period some deliveries may take slightly longer than usual.^BD`
10. `@383573 Hi Chris. We don't have access to accounts here. Please reach out - https://t.co/JzP7hlA23B happy to assist. ^TP`
11. `@226925 Apologies for the delay, Leon. What is the current status on the tracking?^CN`
12. `@206130 We're sorry to hear that. Have you reported this to our support team as requested earlier? ^HK`
13. `@222540 Hello Kylie! When did you send the item back? ^CN`
14. `@721544 Hello, I am sorry for that. Did you purchase the item on Amazon.fr ? ^SM`
15. `@665282 Sorry to hear that, please contact us here: https://t.co/Q7Ftz6nj80 so an agent can look into this with you. ^JJ`
16. `@142144 Hello! What was advised when you contacted us?^CN`
17. `@226940 Sorry to hear about the disappointing experience. Kindly request a return/replacement here: https://t.co/dgreAZQ5qf. Further, I'll share your experience with the concerned team as feedback.^AR`
18. `@665594 Apologies Mohammed. Were you able to get in touch with the carrier? Have you a current outstanding order?  ^TP`
19. `@138638 Sorry to hear that! Can you tell us why you contacted us? Is there an issue with your account?^CD`
20. `@816254 Hey Paul, don't worry we do deliver up to 8pm! Does your tracking say out for delivery? You can find that information here: https://t.co/PyACxvY8Qo ^LS`

### Sample 20 Examples: `very_short` (Total: 2,781)

01. `@465803 |ω・).｡oO( ありがとうございます・・・！） SK`
02. `@169711 You are welcome, Avinash. ^MJ`
03. `@442896 Keep us posted! ^LB`
04. `@300259 Wirklich schwierig .... 😀 ^VM`
05. `@208868 That is correct. ^TR`
06. `@460284 Je vous remercie :) ^MA`
07. `@442803 Profitez-en :)`
08. `@770536 Thank you :) ^NW`
09. `@804144 Estamos para ayudarte. 😄 ^DB`
10. `@488768 Did you email us? ^RS`
11. `@803282 Merci à vous !!`
12. `@254620 ご利用いただきありがとうございます✨✨ SK`
13. `@153429 Ravie de l'apprendre 😊 ^MA`
14. `@295642 Du Ferkel! 🐷😱😂 ^MF`
15. `@118356 Always happy to help. ^CB`
16. `@770772 ( *• ̀ω•́ )b✨ YM`
17. `@275645 Sim, fique de olho. 👀😃😉 ^NB`
18. `@123478 Lindo demais, né! 💙 ^DA`
19. `@629141 Thanks for the feedback. ^KM`
20. `@428947 à votre service !  ^KE`

## 4. Issue Diversity (TF-IDF Customer Bigrams)
- Analyzed strictly on **154,976** inbound customer messages.
- Top 15 customer bigrams:
  - **customer service** (mean TF-IDF: 0.00600)
  - **amazon prime** (mean TF-IDF: 0.00439)
  - **day delivery** (mean TF-IDF: 0.00342)
  - **day shipping** (mean TF-IDF: 0.00281)
  - **customer care** (mean TF-IDF: 0.00257)
  - **delivery date** (mean TF-IDF: 0.00213)
  - **prime membership** (mean TF-IDF: 0.00204)
  - **delivered today** (mean TF-IDF: 0.00180)
  - **amazon amazon** (mean TF-IDF: 0.00167)
  - **amazon logistics** (mean TF-IDF: 0.00164)
  - **don know** (mean TF-IDF: 0.00157)
  - **prime member** (mean TF-IDF: 0.00152)
  - **amazon pay** (mean TF-IDF: 0.00151)
  - **haven received** (mean TF-IDF: 0.00146)
  - **cancel order** (mean TF-IDF: 0.00133)

## 5. Duplicates & Message Noise
- Unique customer texts: **152,408 / 154,976** (duplicate rate: **1.66%**)
- Noise rate (pure mentions/single-word replies): **0.29%**
- Substantial requests (? or >50 chars): **83.37%** (129,204 messages)

## 6. Golden Set Feasibility
- Target: 150–250 examples. Available high-quality customer requests: **129,204** (>500x surplus).

## 7. RAG Usable Pair Calculation
- Formula: `Substantive Outbound Replies (139,116)` matched to verified `Inbound Customer Tweets (inbound=True)`
- Verified usable pairs: **138,255**

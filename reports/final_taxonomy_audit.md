# Proposed Final Intent Taxonomy — pending human annotation

> Local, reproducible audit only. Clusters describe language patterns, not ground-truth intents.

## Corrected dataset metrics

- Raw AmazonHelp customer→brand pairs: **154,976**
- Unusable messages removed: **14,215**; usable pre-dedup: **140,761**.
- Duplicate normalized texts removed: **498**; cleaned unique messages: **140,263**.
- Cleaned unique English corpus / denominator: **117,934**.

### Corrections to earlier artifacts

- Recomputed substantive AmazonHelp→verified inbound-customer pairs: **138,255**. This resolves the 138,255 vs 138,264 discrepancy in favor of **138,255**; 138,255 is an undocumented stale value.
- Language counts are now explicitly reported both pre- and post-deduplication; only post-dedup English is used as an intent denominator.
- The prior K=8 value is not reused: this audit reruns KMeans deterministically and stores every cluster count in the raw artifact.
- The earlier 50.44% multi-turn claim is not supported by the prior implementation. This audit measures follow-up availability from actual parent IDs instead of treating that claim as a finding.

## Isolated message versus conversation context

- Earlier-regex fallback population audited: **88,731**.
- Fallback messages with recovered preceding context: **44,952** (50.66%).
- Apparently unclear messages assigned a supported customer intent only after context: **10,821** (12.2% of fallback; 24.07% of those with context).
- Residual `other_unclear` after context-aware classification: **81,523** (69.13% of cleaned English).

Customer intent is the underlying help goal. Conversation state (initial/follow-up) and message type (question, information provision, acknowledgement, complaint) are separate fields and are not intents.

## Fallback language exploration

TF-IDF used 3,000 features. Top word frequencies: [['amazon', 13617], ['order', 11016], ['delivery', 9999], ['just', 6726], ['service', 6504], ['customer', 6397], ['delivered', 6244], ['day', 5851], ['time', 5687], ['today', 5336]]
Top bigram frequencies: [['customer service', 2853], ['day delivery', 1358], ['day shipping', 1118], ['customer care', 1043], ['delivered today', 662], ['don know', 539], ['amazon india', 434], ['order delivered', 434], ['haven received', 433], ['amazon logistics', 392]]

Top document co-occurrences: [['customer + service', 3070], ['day + delivery', 1912], ['amazon + order', 1503], ['amazon + delivery', 1437], ['delivery + order', 1332], ['delivered + order', 1331], ['amazon + service', 1200], ['day + shipping', 1163], ['day + prime', 1148], ['amazon + customer', 1123]]

KMeans was rerun at K=8, 10, 12, 15, and 20. It is exploratory only; exact results are in `experiments/final_taxonomy_audit_raw.json`.

## Major K=10 fallback clusters

### cluster_5: 44,712 messages (50.39%)

- Top keywords: `order, help, time, email, don, need, account, thanks, details, yes`
- Top bigrams: `don know, haven received, gift card, order number, filled form, let know, need help, shared details, don want, email address, customer support, pre ordered`

1. Customer `1719103`: @119625 @58582 Please upload jaya janaki nayaka full movie bro
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Racier, Intense &amp; Bolder! #GirlfriendExperience 
https://t.co/80JLmlzV6h. @58582 https://t.co/kmg5gmYjWS
   - AmazonHelp response: @119624 We will continue to add new content. Stay tuned for updates! ^EM
2. Customer `828339`: @AmazonHelp Reach me @ 7373488027
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @115821 cheating Amazon, I ordered Moto g5 s plus mobile,but you sent me micromax mobile .I complained in customer care ,but there is no use | customer: @115821 Commenting this useless url doesnt help others... For the name shake dont do anything | AmazonHelp: @314401 resolve this at the earliest by sharing your details through the link mentioned earlier. (2/2) ^VM
   - AmazonHelp response: @314401 details, as we consider it to be personal information. Our Twitter page is public.​ 3/3 ^EM
3. Customer `1506884`: @469735 @115821 @13579 Mines a kinda worrisome: 
"It was handed directly to a resident."
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: I'd pay extra for @115821 NOT to use their own @13579 service. 
It's awful. | customer: @187887 @115821 @13579 Totes not as bad in my area after they stopped just leaving packages at the bottom of the stairs for everyone. | customer: @469735 @115821 @13579 Hrm, when that happened what was the delivery message? 
Maybe I should go check stairs around apt complex.
   - AmazonHelp response: @187887 I'm sorry for the trouble! If you haven't already found your package, please send us your info here: https://t.co/49pFNZSZGp ^JM
4. Customer `1341710`: @AmazonHelp Text said package lost, contact you, but no contact info anywhere. It's not a return. How do we contact you as you requested?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @432942 I'm sorry your package was lost. We'd be happy to go over your options, please contact us here: https://t.co/hApLpMlfHN ^CO
5. Customer `920546`: So sieht es aus , wenn bei @116316 große Päckchen an einem „Hausbewohner“ übergeben werden. 6, setzen https://t.co/pwyjaJ5anz
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @338510 Tut mir sehr leid zu sehen :( Melde dich bitte hier, damit wir das prüfen können: https://t.co/OrmRHrb4p9 Liebe Grüße ^MF
6. Customer `2763567`: La #carotte @120533 on peut seulement #modifier sa #commande depuis un #pc comme ça on verrouille tout 😶 quelle #qualité de #service ! 👎🏼 https://t.co/FTHoNLqdv4
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @773067 Bonjour, pouvez-vous m'expliquer davantage? Rencontrez-vous un problème? ^ARC
7. Customer `437332`: @120540 ho ricevuto un pacco che riporta solo il mio nome sopra (senza cognome) e null'altro... È possibile o non era un corriere?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @218861 il nome riportato sul pacco è quello presente nell'indirizzo del tuo account, puoi verificare da qui: https://t.co/NrwoFbnt44. ^MZ
8. Customer `779436`: @AmazonHelp Its been given as a gift I can't really ask for it back. I should have read the reviews two people also said it was 8gb not 16gb.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `marketplace_seller`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Pretty disappointed that the usb stick we bought as a birthday present has less storage than advertised @115830 | AmazonHelp: @238475 I'm sorry your order was not as expected. Was this item shipped or fulfilled by Amazon or shipped by a third party seller? ^EM | customer: @AmazonHelp Sold by https://t.co/IwA8yFhgZe and fulfilled by Amazon | AmazonHelp: @238475 Hi, sorry to hear that, you can send it back for a refund if you are not happy ^AS
   - AmazonHelp response: @238475 We'd be happy to look into further into this with you and see what help options are available here: https://t.co/JzP7hlRCV9 ^WJ
9. Customer `2269323`: @AmazonHelp Can your team can give me a call plzz
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: AmazonHelp: @447293 Prime membership can be renewed as soon as the current membership expires. If your membership is about to expire then please watch out for email or SMS communication from Amazon.in with details to renew your Prime membership. ^AR | customer: @AmazonHelp  https://t.co/VfrT25nE05 | AmazonHelp: @447293 Could you please confirm if you've shared the details in the link provided earlier? ^RB
   - AmazonHelp response: @447293 I understand you want to talk to us. Kindly reply to the email correspondence you've received from us by requesting a call back and we'll contact you. ^HS
10. Customer `1137859`: @AmazonHelp Sure will try it..get back to you..thank you
   - State/type: `followup_in_thread` / `acknowledgement`; inferred goal: `prime_membership`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @119625 @12154 Videos downloading very slow in Amazon prime videos app..#ArjunReddy  #ArjunReddyinamazon | AmazonHelp: @388014 That is unusual, Jagan. Did you try restarting the phone and checking with the network connections?  ^KS | customer: @AmazonHelp Dear @AmazonHelp i have tried in different locations with different networks..everywhere it's dam'n slow | AmazonHelp: @388014 There doesn't seem to be any ongoing issues with the app, Jagan. Please uninstall and reinstall it in your device. ^JC
   - AmazonHelp response: @388014 Appreciate your patience and understanding. Do keep us posted. ^MM
11. Customer `1311849`: @AmazonHelp You need a space after the Twitter handle name..
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: AmazonHelp: @54884 that case, please fill this form: https://t.co/beaaDm0muc and we'll have a closer look at it and get back to you soon.^RS
   - AmazonHelp response: @426543 You can continue without the space. ^RW
12. Customer `1748130`: @AmazonHelp when will you actually help?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @526970 We'd like to help in any way we can! Can you tell us when your package was scanned as delivered? https://t.co/Y5jpI9gRhE ^NM
13. Customer `150477`: @117086 bloqueiem esses cara em todas redes sociais possíveis. Recebi um e-mail antes e AAAAH SÓ UMAS OFERTINHA. Gastei 100 pila em livro.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: eu ODEIO vocês @117086
   - AmazonHelp response: @150320 Nossa 😅 Mas nós amamos você ❤️ Só queremos que você seja feliz! ^LG
14. Customer `2645189`: @AmazonHelp I bought a paper shredder from you &amp; it stopped working a little week after. I would like to know what you can do to help.
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @746312 If it's been less than 30 days since delivery, please call or chat us to explore your options: https://t.co/hApLpMlfHN 1/2 ^EA
15. Customer `1131238`: @AmazonHelp Yes while they investigate but I know what has happened because it has happened so many times before!
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @AmazonHelp Have delivered to wrong House again. Claim they’ve delivered to me! only firm that can’t get it right! Such a pity Amazon changed to them. | AmazonHelp: @386597 We'd like to take a closer look into this incident with you. Please click here: https://t.co/JzP7hlA23B so we can assist. ^NM | customer: @AmazonHelp Being investigated. No answers though more than 24hrs! Amazon don’t care about delivery issues. Amazon Logistics appalling don’t care either | AmazonHelp: @386597 Sorry about that! Were you advised to wait 24hours?^CD
   - AmazonHelp response: @386597 Did they email you after the call advising this? Is there a link at the bottom to leave feedback? ^PK

### cluster_4: 9,338 messages (10.52%)

- Top keywords: `delivered, just, today, package, ve, order, says, yesterday, delivered today, supposed`
- Top bigrams: `delivered today, package delivered, order delivered, supposed delivered, arrive today, says delivered, delivered yesterday, just want, parcel delivered, said delivered, today pm, deliver package`

1. Customer `117848`: Text from @115821  . 8.43am we will attempt to deliver your parcel today. Okay well that's not helpful. Thanks.
5.35pm we will deliver today but it'll be later than expected. Well it's 9.45pm and no parcel? Cheers
   - State/type: `initial_or_context_unavailable` / `acknowledgement`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @142140 I'm sorry your order hasn't arrived! I know how frustrating this can be. What is the latest tracking showing for your order: https://t.co/aaDyEz1VgE? ^LR
2. Customer `2950793`: Something has gone downhill with @117093 quality control. Last 4 orders there has been an issue. Order didn’t even show up today.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @814859 I'm sorry for the poor experiences! This isn't the expectation we've set. Have you had a chance to contact us regarding your order? If no, please do so here: https://t.co/EKXRLsnxJu ^AC
3. Customer `1591539`: @AmazonHelp I've already been in touch with three CSRs over the course of the week. I never had an issue when USPS and UPS delivered instead of Amazon.
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Hey @AmazonHelp @115821 ordered 2 pkgs this week &amp; I'm 0-2 on timely arrival. Insult to injury is today's missed pkg showing as delivered. | AmazonHelp: @489261 I'm sorry to hear you didn't receive your order! Here's a link to our Help page for this situation: https://t.co/pxzdNT3obZ ^BV
   - AmazonHelp response: @489261 Was the carrier AMZL? Did the orders miss the estimated delivery date we gave at checkout and via email? We'd like to help. ^RM
4. Customer `2617267`: @AmazonHelp Not yet. Normally there's a picture taken or some indication of where the package was left but this just says "Your package was delivered. It was handed directly to a resident." No one has been here all day.
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `delivery_status_delay`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: So @115821 *might* have given my package to a neighbor "for safe keeping". I think this idea of independently contracted "deliverers" who just say that "it was delivered to a resident" is a pretty horrible idea. I DON'T KNOW MY NEIGHBORS | AmazonHelp: @739718 Oh no! I'm so sorry to hear about your experience! Just to clarify, were you able to locate the package? ^VF
   - AmazonHelp response: @739718 I certainly understand. We would like to look into this further for you! When you have a moment, please give us your details here: https://t.co/P3GZyChaXZ ^VF
5. Customer `2449345`: @AmazonHelp Nope. Said it would be delivered today right up until 8PM. Then I was told it was delivered to @118706.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Order from @115821. Prime eligible items. Should have been delivered tonight. Nope. They decided to ship it USPS, the slowest shipping method possible. | AmazonHelp: @702020 Oh no, Bryan! Have we missed the delivery date in your confirmation email? ^LM | customer: @AmazonHelp Yep. Because you shipped it via the @118706. Bad idea. | AmazonHelp: @702020 Did you receive an email notification of a delay? ^LM
   - AmazonHelp response: @702020 Hmm, that sounds strange. Please reach out to us here so that we can take a closer look at the tracking information and explore options: https://t.co/hApLpMlfHN ^EA
6. Customer `331983`: @AmazonHelp we have a kids fire that is less than a yr old that is just stuck on this screen? Any ideas https://t.co/cgJKQdtsTF
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @195053 Oh no! Let's try restarting it by holding the power button for 40 sec: https://t.co/oTmletsunX. Let us know how this helps! ^MB
7. Customer `1389978`: @115830 not impressed by your driver leaving my door within 6 seconds of knocking 
Despite my note explaining I've just had spine surgery!
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `packaging_and_carrier_feedback`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @443315 Very sorry to hear this. Was the parcel delivered to you ? ^CR
8. Customer `421001`: @AmazonHelp no.IVR just parrots where my order is and runs pre-recorded options (no option to talk to exec) and recommends me to go back to the website
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `delivery_status_delay`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @AmazonHelp horrifying customer service this highly arrogant portal gives.On selecting call me,I am made to listen a an IVR @115851 | AmazonHelp: @215334 We're sorry about the stretch with your order. Were you not connected to one of our  representative after the IVR on call? ^HK
   - AmazonHelp response: @215334 Apologies for the trouble. I'd like to help. Please share your details here: https://t.co/JzRdscmdH9  ^AK
9. Customer `1304668`: @AmazonHelp Not sure I wont be home till tomorrow Its not the first time it’s happened It’s usually at my door getting that text just makes me nervous
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @115821 is always freaking me out choosing the wrong delivery updates. Tell me how it says “hand delivered to Alexandra” when no one is home | AmazonHelp: @424872 Oh no! That's odd! Did you receive your package?  ^AG
   - AmazonHelp response: @424872 I'm sorry for any frustration this has caused. If you're unable to locate your package when you get home please let us know. ^LR
10. Customer `224207`: @AmazonHelp If I just cancel the order and then reorder it again will I get it tomorrow? It's been in transit to the carrier.
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `packaging_and_carrier_feedback`.
   - Preceding context: customer: @115821 ordered same day delivery &amp; package is still in transit to carrier on day 2.  2nd time Same Day turned out to be 3 day delivery. https://t.co/gpUWvILQHF | AmazonHelp: @169574 I'm sorry to keep you waiting. Reach out to us here to have a look into this with you: https://t.co/iwhSpWer9i ^CL
   - AmazonHelp response: @169574 I can't guarantee this. You can place a new order to get the estimated delivery date. ^RR
11. Customer `2562149`: @115821 explain why I have two packages being delivered today but you just dropped off one?? Whyyyyyy are you doing this to me? https://t.co/lMgtccFaaZ
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @159646 I'm so sorry for your troubles! Have you checked to see if the other package was being delivered by a different carrier? You may check here: https://t.co/Y5jpI9gRhE Please keep us updated if it doesn't arrive by the delivery date! ^VF
12. Customer `1342562`: @AmazonHelp I'm in your chat now. Trouble is this is happening a lot. Being told something is delivered and it isn't
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Ok this is a lie @115821 @115830 - been in all day, no sign of it. Order no. 205-6496104-8852338 https://t.co/UsKbcgbSls | AmazonHelp: @433126 I'm sorry you haven't received this game yet! Have you tried these troubleshooting steps:https://t.co/kb30YDbmyp? ^WM
   - AmazonHelp response: @433126 Please keep us posted. We want to make sure this is taken care of for you ^VS
13. Customer `1565895`: @AmazonHelp can you track a parcel more precisely than me? I just want to know if it’s going to come today so I can let my neighbour know
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @483376 Hi, Tom. The most up-to-date tracking info is displayed on the courier's site. Who's the courier here: https://t.co/aaDyEz1VgE ^LB
14. Customer `180161`: @115850 My logitech x50 bluetooth speaker tracking id 203111266741,neither delivered at time nor showing tracking details.
   - State/type: `initial_or_context_unavailable` / `information_provision`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @158392 Hi, sorry about that. We'd like to help. Kindly report this to our support team here: https://t.co/rS49hgaADF ^AK (1/2)
15. Customer `1905574`: I used to only have good experiences with shipping and ordering from @AmazonHelp but have had 3 packages not delivered in the last 2 months
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @567829 I'm sorry to hear this! Have we missed the delivery date on a current order? ^KP

### cluster_8: 8,378 messages (9.44%)

- Top keywords: `amazon, order, account, india, amazon logistics, help, logistics, amazon india, service, time`
- Top bigrams: `amazon india, amazon logistics, amazon account, amazon echo, amazon order, order amazon, service amazon, amazon shipping, gift card, use amazon, buy amazon, contact amazon`

1. Customer `343866`: @AmazonHelp And even it looks like the Amazon isn't interested much with the customer.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @AmazonHelp No updates from @115850 yet | AmazonHelp: @197813 An email has already been sent to you with a reply. Please check it, using this link here: https://t.co/NTkrxpsbHJ ^KA | customer: @AmazonHelp I do not see any useful information from the Amazon, they have give clarification of the reorder product | AmazonHelp: @197813 We're unable to verify the details over Twitter, Vignesh. Please respond to the email you received from us. ^JC
   - AmazonHelp response: @197813 Please reply to the email from our team and we'll contact you soon. ^PS
2. Customer `2922645`: Placed a Prime Now order for a few random things I needed... Literally they used this huge bag for this one sheet of stickers. Amazon is so wasteful. https://t.co/XWiaSi0nqG
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @808817 We strive to improve. Please provide more detailed feedback here: https://t.co/9QXcxpa4i6 ^BA
3. Customer `644718`: @115851 @115850 Amazon.in Order # 406-9047234-6277910
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @115851 @115850 I buy 1 year warranty period phone n now ur team ask 4 go to local shop n repair the phone even product is in warranty
   - AmazonHelp response: @267722 Please don't provide your order details, we consider it personal info. Our Twitter page is visible to public. ^NR
4. Customer `1704757`: My hopes and dreams are crushed bc Amazon messed up my order
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: I have 6 pounds of Amish popcorn kernels being delivered today this is me living my best life
   - AmazonHelp response: @516732 Uh oh! We'd love to help with this! Without including account information, could you tell us more about what's happened?^ML
5. Customer `1695866`: @AmazonHelp do I have to guess where my parcel is? #amazon #AmazonPrime #CustomerService #AmazonUK https://t.co/eGggjs8FEi
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `delivery_status_delay`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @514493 Oh no! We'd love to help if we can, Megan! Please contact us via phone or chat here: https://t.co/JzP7hlA23B ^AJ
6. Customer `537528`: @116618 amazon video not loading on the PS4
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @244599 Sorry you are having trouble, Andrew! Restarting your device, Internet modem, and router can resolve many intermittent connectivity issues. Let us know if this helps! ^SC
7. Customer `313645`: Frode 
Fake fake fake
Very poor
Amazon service 
9773388355
7666616852
@AmazonHelp @115850 @118702 @122599
   - State/type: `initial_or_context_unavailable` / `complaint_or_feedback`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @123622 Also, don't provide your account details, as we consider it to be personal information. Our Twitter page is public. (2/2) ^AU
8. Customer `1972844`: @AmazonHelp I was in the middle of typing so we weren't idle. It was a query about a guarantee for a tv I was expecting but about which Amazon UK are denying all knowledge.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @AmazonHelp Maybe 2 mins not quite long enough to allow customers in live chat? Particularly for those who are disabled and find typing a longer process. In the middle of a chat and I've been disconnected! | AmazonHelp: @584321 I'm sorry to hear of this Ruth, chats should only be disconnected if they are idle and show no sign of someone typing. Without providing any personal information can you let us know what your query was? ^KI
   - AmazonHelp response: @584321 Hello, please try to contact once again using the following link: https://t.co/JzP7hlA23B ^CR
9. Customer `2276011`: @AmazonHelp Hello, I have ordered a phone from Amazon 😊
Kindly can you Pls Update how can I get my ebill on mail id 

Thanks
   - State/type: `initial_or_context_unavailable` / `acknowledgement`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @661977 Let me help you here. You can download an invoice copy from your Amazon.in account. The steps here: https://t.co/r3mxli0q9I should help. ^AR
10. Customer `1156703`: Terrible service this time #Amazon . Didn't get cashback after doing payment by #amazonpay . Didn't expect such error #Amazon #amazonprime
   - State/type: `initial_or_context_unavailable` / `complaint_or_feedback`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `gift_card_promotions`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @392102 Sorry to know that you dint receive the cashback. Please contact us here: https://t.co/TK4yevTaND, we'll check it. ^NR
11. Customer `1612530`: Amazon said they would give me my package before 8 pm and it's 11 minutes til. Y'all better drive fast
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @494821 I'm sorry for the wait! What does the most up to date tracking information say here: https://t.co/Y5jpI9gRhE? ^DW
12. Customer `1501853`: Come on Amazon where’s my case at? I need to protect my new baby 😛
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @148233 What is the shipping status, as described in"Track my Package"? You can access the Order History here:  https://t.co/aaDyEz1VgE ^CH
13. Customer `1483548`: #Amazonindia Amazon does not serve.I had booked twice.Automatically returnedTells the bad region There is no help too Amazon's https://t.co/ACJHsTekB4
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @464510 I'd like to take a closer look into this, please share your details on the link here: https://t.co/GIJyeYqKE0. 2/2 ^PS
14. Customer `2987259`: Why have you lied to me @115821.... First you take several days to ship this out, then you charge me twice over a single order and now this? Why have you done this to me I've been a loyal Amazon customer since 2013.... https://t.co/1SYAuBKEIl
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @823674 Can I ask, what was the original delivery date given to you on the confirmation email you received when you placed this order please?^GA
15. Customer `1403985`: @AmazonHelp Well, it's happened again! Yet another one of my orders messed up by Amazon; and this time they've really screwed me over!
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @408415 I'm sorry for this experience. Can you tell us more about what's gone on without posting order or account info? ^DO

### cluster_9: 6,588 messages (7.42%)

- Top keywords: `delivery, like, didn, order, time, ordered, package, deliver, driver, today`
- Top bigrams: `delivery service, delivery guy, delivery driver, amazon delivery, delivery drivers, looks like, delivery today, guaranteed delivery, delivery boy, delivery person, attempted delivery, delivery attempted`

1. Customer `988870`: @117795 That's in Liverpool, same in Manchester and Birmingham, the below pic is Leeds 40 pounds free delivery 3.99 over 25 pounds
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @117795 Leeds given the worse service again?Gone up to £40 minimum now, not £20 as other cities,guess you don't like Leeds very much
   - AmazonHelp response: @354291 Hello, this service is the Prime now service. We would require a minimum charge of 40GBP to avail of free delivery. ^CR
2. Customer `967236`: @115850 Kindly do the delivery we are at home only @115850
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @115850 We attempted to deliver your order with Iris Dew Berry Aroma Short Glass Jar Candle . https://t.co/wDyryuRVEV
   - AmazonHelp response: @349571 I understand your concern, please contact us here: https://t.co/rS49hgaADF so that we can assist you accordingly. ^SC
3. Customer `562865`: @AmazonHelp About 30 mins ago when speaking with the CSR from the shipping company AMZCA. Said if it was on a truck they’d have an idea when I can expect but said it looks like it hasn’t made it to a truck yet.
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `prime_membership`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: AmazonHelp: @251767 I'm sorry for this wait. Deliveries continue through to 8PM. Please keep us informed of your order's arrival. ^DO | customer: @AmazonHelp Told package not even on a truck yet. Guaranteed delivery is to be today with Prime Membership | AmazonHelp: @251767 I completely understand how frustrating this must be. At what time were you told it's not on a truck? Has the tracking shown 'Out for Delivery' today? https://t.co/PyACxvY8Qo  ^RO
   - AmazonHelp response: @251767 My team can escalate this to our Transportation team on your behalf. When you've got a free moment, please send us some more details about this order here: https://t.co/7PFt9RIhWY ^DW
4. Customer `2367352`: Good one @115830 
That’s a wonderfully secure delivery...
No email, no text! You just abandoned my parcel in an unsecured doorway 😡
#ShoddyService #HonestNeighbours https://t.co/udnPNGjm2r
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @683338 We're sorry to hear of your experience receiving this parcel, Katrina.  Delivery preferences can be set up for parcels that arrive when you're away. For more information please click here: https://t.co/Sz6ITMMnXa. We're here to help in any way we can! ^AZ
5. Customer `2609881`: @AmazonHelp this link is directed to the order details and can’t see where i can fill details for not receiving the delivery
   - State/type: `followup_in_thread` / `information_provision`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: AmazonHelp: @650141 I'm sorry to hear you haven't been able to find your order. I'd recommend checking our help page on locating items that are tagged as delivered: https://t.co/t9cD8JIHc7 ^KI | customer: @AmazonHelp Thanks for prompt revert.. but i have checked everywhere and asked the neighbours too.. i did got Missed Post Note by @643 but nothing was around | AmazonHelp: @650141 Hey Sandeep, can you contact us so that we can look into this further for you: https://t.co/oGDklGgbCZ? ^PJ
   - AmazonHelp response: @650141 Sorry about that Sandeep. Please try the following link instead and we can check what has happened for you: https://t.co/JzP7hlA23B ^BZ
6. Customer `2463881`: @AmazonHelp If the same delivery carrier is used. (2/2)
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `packaging_and_carrier_feedback`.
   - Preceding context: customer: @115830 truly have been useless this time I really wonder why I pay for prime sometimes | AmazonHelp: @555622 Sorry to hear that Jordan- without revealing any personal info, can you tell us what happened? ^MA | customer: @AmazonHelp That you guys would just send out a new one by another member of the help team on the phone. Just the way I was spoken to and I had to repeat the whole details to every be new person I spoke to was just not good enough. Especially when I pay for a service that I didn’t get. | AmazonHelp: @555622 I'm sorry for the inconvenience Jordan- was the resolution proposed to you at the end? What did we advise? ^MA
   - AmazonHelp response: @555622 Hi Jordan. Sorry to hear that you've experienced issues with our carrier. Can you advise who the carrier was and what happened? Did you pay for the order using a gift card? If so, we can only refund to the same payment method.^JC
7. Customer `378532`: @AmazonHelp Didn't get any response so far.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `item_condition_or_fulfilment`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Very bad service @115850. For last one week calling customer care for the return of my defective laptop and charger delivered. No response | AmazonHelp: @205826 details from the link here: https://t.co/VNUITkunAc and we will assist you accordingly.(2/2)^HR
   - AmazonHelp response: @205826 I’m sorry for the issue regarding the return. Could you please let us know if you have shared the details via secure link? ^SB
8. Customer `2500795`: @AmazonHelp Paid for next day delivery. Delivery was “attempted” today but my security cameras reveal no such attempts were made. Can I be refunded for this delivery charge?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @713407 Oh no! I'm sorry your parcel wasn't delivered today! Please phone us here: https://t.co/JzP7hlA23B to report this and discuss the available options for this order. ^LB
9. Customer `574936`: @AmazonHelp Delivery due 8, on chat at 8.48 oh yes def arrive by 10pm checks online tracking 8.42 marked as rejected by resident. My daughter waited in all day as it was signed for
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @AmazonHelp you need to get yourselves sorted out getting told a pile of lies and messed around until 10 pm at night is not the way to treat customers. Then no way to complain as the adviser doesn’t put the option in the email 🤬 | AmazonHelp: @255257 Hi, without revealing any account information, can you advised what's happened? ^JC.
   - AmazonHelp response: @255257 Sorry to hear that. We don't have access to your account over Twitter, but if you get in touch here: https://t.co/JzP7hlA23B we'll look in to this for you.^TI
10. Customer `2410496`: @AmazonHelp No. Text message links to delivery page, projection there is unchanged.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `delivery_status_delay`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Ok @AmazonHelp/@UPSHelp s'plain:(delivery promise - 8:00p)9:06a Out for Delivery (my city)10:37a Delivery Delay Was the truck robbed? | AmazonHelp: @693044 I'm sorry for the delay. Was a new delivery date provided: https://t.co/Y5jpI9gRhE? ^JF
   - AmazonHelp response: @693044 Have you tried checking it directly on UPS website? There might be more information provided there. ^MA
11. Customer `775741`: @115850 Pls help!My order was COD but at the time of delivery I paid through ezetap. I've the receipt also.Do I have to pay again???
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @305360 If you have already paid for the order then you don't have to pay for it again. ^SH
12. Customer `2390369`: @AmazonHelp Item still not here. I understand the original point was I missed the delivery. I am just sick of going to live chat to be lied by each advisor to try and keep me happy, I prefer an honest response  it makes things easier in the long run.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: Does Amazon customer service think it’s okay to lie to customers just to keep them happy? Really not impressed and i used to love Amazon. @AmazonHelp | AmazonHelp: @688588 I am sorry to hear this Louise, can I ask for you to elaborate on this please? Thanks ^GA
   - AmazonHelp response: @688588 Without personal info what were you last advised? ^MC
13. Customer `2949474`: @AmazonHelp Ok, didn't get it. Yeah, I ordered like 200€ on your french website and the package was... well, you saw the pics...
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: customer: @AmazonHelp I ordered this on the French website. Packages sent from personal sellers are in better conditions... -_- | AmazonHelp: @814544 Hey Matthieu, did you received a response on your french post ? | customer: @AmazonHelp Nope. Nothing. | AmazonHelp: @814544 I don't understand why, but we do sent you an answer on your french post. So, you ordered something on your website and the package was damaged ?
   - AmazonHelp response: @814544 I'm really sorry for that I hope the item is intact; Who is the carrier in charge of this delivery please? ^ASZ
14. Customer `1497231`: Definition of a nanosecond: the time elapsed between the @115821 delivery driver knocking on the door and writing a 'we missed you' card! 😬
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `packaging_and_carrier_feedback`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @467631 Sorry about that Sarah- Have you a safe place set up or nominated neighbor option? ^NV
15. Customer `1597040`: @AmazonHelp I have 2 Kindles I'd like to trade in towards an Oasis, is there still a bonus offer for trading in old Kindles? Thx
   - State/type: `initial_or_context_unavailable` / `acknowledgement`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @490606 Hi - pls see this link for more info : https://t.co/0jDSmpuLnv  ^TD

### cluster_3: 4,805 messages (5.42%)

- Top keywords: `day, prime, shipping, delivery, day delivery, day shipping, days, pay, order, ordered`
- Top bigrams: `day delivery, day shipping, prime day, pay prime, paying prime, paid day, prime shipping, free day, day prime, prime order, release day, days later`

1. Customer `726612`: @115850 @AmazonHelp Atleast provide 2 day delivery in Jabalpur :( so I can buy Prime else why shud I? Many wud buy in Jbp/Bhopal @115821
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @294049 We're trying our best to improve our services. I'll surely pass on your comments to our concerned department internally. ^SH
2. Customer `1652943`: Hey @115821: Why is it that after a week, you still can't tell me when something from your warehouse (w/Prime shipping) will be sent?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @504626 Hey, did you receive a delivery date via the confirmation email sent? Is the item currently in stock? ^TP
3. Customer `401580`: @AmazonHelp Ordered Saturday, expected today (next day delivery), may not receive until Thursday!
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `delivery_marked_delivered_missing`; isolated overlap: `delivery_delay`.
   - Preceding context: customer: Unhappy with @115830 Prime. Order failed to be delivered today. What's the point paying for prime if the order doesn't arrive! | AmazonHelp: @133240 Oh no! I'm so sorry for the poor delivery experience! Did we miss the date in the confirmation e-mail? Let us know! ^TG
   - AmazonHelp response: @133240 To confirm, Thursday was the order date from the original e-mail was marked for delivery on Thursday? ^MJ
4. Customer `492231`: @115830 Funny how you apparently tried to deliver my parcel without success today, when I’ve been home all day and no one has appeared. Pay for Prime, get crap service in return 💩😡
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @232317 Oh goodness! I'm sorry you haven't received your parcel. We'd like to take a closer look with you. Please reach us by phone or chat here: https://t.co/JzP7hlA23B Thanks KJ! ^AB
5. Customer `10647`: @115821 paid for next day delivery.. had it confirmed and alas, no package #nothappy
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @117950 I'm so sorry for the wait. If you have a moment, please contact us by chat or phone: https://t.co/JzP7hlA23B. ^LH
6. Customer `919805`: @115830 why has prime become so unreliable? On order confirmation is next day delivery, dispatch notification says arrives few days after?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @338337 Hi, sorry for the wait! Have you been provided with a reason behind the revised delivery date? ^TS
7. Customer `990991`: @AmazonHelp my order is past 4 days of shipping date.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @354739 I've responded directly to your DM. Thank you! ^AB
8. Customer `142888`: We pay for prime services for a service which gives you delivery after 2 days? Not happy, when you guys promise a one-day delivery.
@115850 @AmazonHelp
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @148255 I get you haven't received the package on estimated delivery date.  Did you happen to report this to our support team? ^MN
9. Customer `2260854`: Shoddy service now from @115830 
already cancelled @232617. But Prime Now orders are also undelivered. No Next Day deliveries from normal Prime at the weekend anymore. Delivery charges up. They should stick to books.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @396545 Hey Marina! I'm really sorry for the frustration. We'd love to help! What's the tracking say on your Prime Now order?
10. Customer `2627661`: So my @115830 Prime one day delivery ordered on Wednesday night, is apparently due to be delivered by 9pm today, but has not yet been despatched? Ideally I needed it in the next 10 mins, which is why I ordered from Prime in 1st place. 😡
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @742153 We'd like to review your order and confirm the status. When you have the time, please contact us here: https://t.co/JzP7hlA23B ^RA
11. Customer `1100951`: Not sure how one day delivery works from @115830 when it’s not even dispatched yet #doigetarefund #itsabitlate https://t.co/nOYpanOYA0
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @379752 What is the delivery date showing in your orders here:https://t.co/aaDyEz1VgE? Let us know! (2/2) ^SA
12. Customer `2532009`: @115821 are quite literally the most useles company on earth. prime service and next day delivery is a joke. been waiting a damn week
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `delivery_delay`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @720618 My apologies Cris. What does the tracking information currently state? ^DC
13. Customer `816334`: @115821 We were open all day. Maybe it's not a holiday closure but that you tried to deliver at midnight? https://t.co/JDFoNaCTaQ
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @314396 Goodness! Can you tell us who the carrier was for this shipment? You can find this here: https://t.co/Y5jpI9gRhE ^KN
14. Customer `1153223`: @115821 how do you keep losing packages? It's 2017! Sick of your CS scripted answers. Why do I pay for Prime? Taking my business elsewhere.
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `no_legacy_candidate_match`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @391345 Sorry for your experience with us, Sang! Who was the carrier for your order? Let's check here: https://t.co/Y5jpI9gRhE ^JZ
15. Customer `421421`: @AmazonHelp I'm planning to buy the echo dot in India which comes with one year prime. What if i have an existing prime subscription?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence; retain other_unclear`; isolated overlap: `digital_kindle_audible`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @183357 The prime membership with echo will be added to your account after the existing prime expires. ^NS

## Taxonomy decisions

- **RETAIN** delivery, returns/refunds, cancellation, Prime, account security, payment, product catalog, and marketplace-seller journeys because they have distinct customer goals/remedies.
- **MERGE** damaged/wrong/defective/incomplete received-item reports into one fulfilment-condition intent; their initial remedy is replacement/return.
- **MERGE** return, replacement, and expected-refund status into one customer journey for this provisional schema; annotate sub-issues later if they prove operationally separable.
- **SPLIT** delivered-but-missing from delivery delay/status. The classifier requires both delivered evidence and absence evidence and evaluates this predicate first, so it cannot be swallowed by generic delay language.
- **RENAME** `general_inquiry_unclear` to `other_unclear`; it is a residual evidence state, not a customer intent.
- **REMOVE** `conversational_followup` as an intent. It remains a conversation-state/message-type signal.

## Proposed customer-intent distribution

| Intent | Count | % of cleaned English |
|---|---:|---:|
| `delivery_marked_delivered_missing` | 1,085 | 0.92% |
| `delivery_status_delay` | 11,307 | 9.59% |
| `return_refund` | 8,252 | 7.0% |
| `item_condition_or_fulfilment` | 2,634 | 2.23% |
| `order_cancellation_or_change` | 429 | 0.36% |
| `prime_membership` | 4,637 | 3.93% |
| `account_access_security` | 2,020 | 1.71% |
| `payment_charge_issue` | 1,975 | 1.67% |
| `product_availability_pricing` | 1,937 | 1.64% |
| `marketplace_seller` | 2,135 | 1.81% |
| `other_unclear` | 81,523 | 69.13% |

Coverage is every label other than `other_unclear`; all rows sum exactly to the cleaned English corpus.

## Intent definitions, examples, and operations

### `delivery_marked_delivered_missing` — Marked delivered, parcel missing
- Definition: Tracking says delivered, but the customer cannot find the parcel.
- Include: A delivered/handed-off tracking assertion plus non-receipt, missing-location, or wrong-address evidence.
- Exclude: Still in transit or merely late; wrong product in hand.
- PII/account information: Yes — order and delivery-location lookup.
- Likely handling: Give safe-location/neighbor checks, then escalate to delivery investigation or replacement.
- Annotation difficulty: Medium; both delivery and absence evidence are required.
- Historical AmazonHelp response pattern: {'substantive': 859, 'contact_redirect': 122, 'generic_greeting': 98, 'very_short': 2, 'dm_redirect': 4}
- Real example `5128`: @AmazonHelp AMZL US Tracking ID TBA566517950000 it says delivered to mail room, I checked the mail and the front offce, the driver listed 1 package, in that one package was my XLR cables...I'm missing the controller. — AmazonHelp: @116914 I understand your frustration! Our team would like a chance to address this concern. At your convenience, include your details here: https://t.co/hKZOmv3DMU ^SJ
- Real example `16826`: @AmazonHelp Ordered last Friday, still not here. — AmazonHelp: @119702 What was the estimated delivery date provided in the order confirmation e-mail? ^MJ
- Real example `16829`: @AmazonHelp My guaranteed delivery date was Monday. — AmazonHelp: @119702 My apologies. What is the latest update on the tracking?: https://t.co/Y5jpI9gRhE ^PK

### `delivery_status_delay` — Delivery status, delay, or failed delivery
- Definition: An order is late, stuck, not yet dispatched, or needs delivery-status help.
- Include: Late/missed dates, in-transit tracking, failed attempts, or where-is-my-order requests without delivered-and-missing evidence.
- Exclude: Explicit delivered-but-missing cases; a return/refund after delivery.
- PII/account information: Yes — order/tracking lookup.
- Likely handling: Provide tracking guidance; escalate when materially overdue or repeated failure is shown.
- Annotation difficulty: Medium; distinguish status from a confirmed missing parcel.
- Historical AmazonHelp response pattern: {'very_short': 52, 'substantive': 8752, 'contact_redirect': 903, 'generic_greeting': 1542, 'dm_redirect': 58}
- Real example `627`: @AmazonHelp @115826 Yeah this is crazy we’re less than a week away and still no Shipping Information on something that we Pre-ordered back in August — AmazonHelp: @115827 Thanks for your patience. ^KM
- Real example `628`: @115828 How about you guys figure out my Xbox One X project Scorpio edition first. No expected delivery or shipping date and it’s only a week away — AmazonHelp: @115826 I'm sorry for the wait. You'll receive an email as soon as we have an estimated delivery date. ^FJ
- Real example `634`: @115821 @AmazonHelp why is my order at my local courier for the last 6 days and still hasn’t been delivered to me?? Over 1 week late 😡 — AmazonHelp: @115831 I'm sorry for the wait. Please reach out to us so we can take a closer look at this delivery: https://t.co/JzP7hlA23B ^SH

### `return_refund` — Returns, replacement, and refund status
- Definition: A customer needs to return/replace an item or asks about an expected refund.
- Include: Return labels/pickups, replacement requests, refund timing or amount after a transaction.
- Exclude: Unauthorized/double card charges; cancellation before dispatch.
- PII/account information: Yes — order, payment, and return lookup.
- Likely handling: Offer self-service return/replacement path and standard refund timing; escalate missing/exception cases.
- Annotation difficulty: Medium; refund can co-occur with delivery or cancellation.
- Historical AmazonHelp response pattern: {'substantive': 6462, 'contact_redirect': 747, 'generic_greeting': 931, 'dm_redirect': 65, 'very_short': 47}
- Real example `664`: @AmazonHelp delivery I paid for today,didn’t arrive.why not?i paid enough for it.where is it??I’m unhappy.refund the delivery charge — AmazonHelp: @115842 Oh no! Please contact us via phone/chat here: https://t.co/JzP7hlA23B
We're unable to view order details via Twitter. ^KL
- Real example `1699`: @AmazonHelp I called customer service and was told my membership wouldn't be renewed. I was just charged today. How do I get a refund? https://t.co/SeoQUsA0VA — AmazonHelp: @116082 Canceling your Prime membership can be done here:https://t.co/MlOxxuNX7N. You'll be shown your estimated refund there. ^SK
- Real example `2570`: @AmazonHelp yes i did,but amazonuk is not doing the refund process.if they do it .i will get the money — AmazonHelp: @116321 I would like someone from our team to take a look into this for you, Sanu. Please reach out here: https://t.co/QtC7bueYoR ^LA

### `item_condition_or_fulfilment` — Wrong, damaged, defective, or incomplete item
- Definition: A received item is wrong, damaged, defective, expired, or missing components.
- Include: Wrong item/size, damaged packaging/item, faults, missing parts, empty box.
- Exclude: Parcel wholly missing after a delivered scan; return/refund status without a condition report.
- PII/account information: Yes — order lookup; evidence may be needed.
- Likely handling: Usually self-service replacement/return; escalate hazardous or non-returnable cases.
- Annotation difficulty: Low to medium.
- Historical AmazonHelp response pattern: {'substantive': 2044, 'generic_greeting': 326, 'contact_redirect': 233, 'very_short': 13, 'dm_redirect': 18}
- Real example `651`: @AmazonHelp I don't want a form to fill out that logs a response no one reads. I want to prevent AMZL from touching my stuff. Possible, or no? — AmazonHelp: @115838 Is there a current order you're having difficulties with? Please let us know, we'd like to help! ^KL
- Real example `654`: @AmazonHelp Already started the return. UPS gets it from my doorstep tomorrow. Order 111-5014070-4118645 — AmazonHelp: @115838 Provide your details here: https://t.co/6f6cWZv7vm and my team will escalate the order to Amazon Logistics for feedback. ^EZ
- Real example `652`: @AmazonHelp Is it possible to prevent AMZL from delivering my packages moving forward? Stuff is either lost/stolen/broken EVERY time. — AmazonHelp: @115838 Oh no! We want to hear more about your experience with AMZL. Please provide your feedback here: https://t.co/hApLpMlfHN ^SH

### `order_cancellation_or_change` — Order cancellation or change
- Definition: The customer wants to cancel/modify an order or disputes an automated cancellation.
- Include: Cancel order, address change, accidental order, order already cancelled.
- Exclude: Canceling Prime; returning a delivered item.
- PII/account information: Yes — order lookup.
- Likely handling: Direct to order management when pre-dispatch; escalate shipped or system-error cases.
- Annotation difficulty: Low.
- Historical AmazonHelp response pattern: {'substantive': 328, 'generic_greeting': 46, 'contact_redirect': 47, 'dm_redirect': 5, 'very_short': 3}
- Real example `23198`: @115850 Order number 407-2412845-1630730, how to change shipping address? — AmazonHelp: @121051 details as we consider them to be personal information. Our Twitter page is visible to public. 3/3 ^SB
- Real example `42573`: Trying to cancel an order on @115821 but the website and app page come up blank when I hit "cancel order" @AmazonHelp — AmazonHelp: @125405 Oh no! We can help you with this, Annie! Just give us a quick call or chat here so we can assist: https://t.co/hApLpMlfHN ^JD
- Real example `64208`: @AmazonHelp This is ridiculous, I’ve literally just shown what the tracking is showing and your asking again, can you not look through the thread of tweets? Something needs to be done ASAP otherwise I’ll just cancel my order — AmazonHelp: @130736 Our team would like to look into this further with you directly to see what we can get done to help repair the situation. Can you please provide your information here so that we can reach out? https://t.co/t56ZRZdwU0 ^GS

### `prime_membership` — Prime membership and benefits
- Definition: Prime fees, renewal/cancellation, eligibility, or Prime service benefits.
- Include: Prime membership, trial, fee, renewal, student Prime, Prime Video/Music.
- Exclude: A generic late order that only incidentally mentions Prime.
- PII/account information: Usually yes — membership lookup.
- Likely handling: Manage-membership guidance; escalate account-specific billing disputes.
- Annotation difficulty: Medium; Prime may be evidence in a delivery complaint rather than the goal.
- Historical AmazonHelp response pattern: {'substantive': 3617, 'generic_greeting': 685, 'contact_redirect': 272, 'very_short': 37, 'dm_redirect': 26}
- Real example `693`: @AmazonHelp since when you stop giving 20% off videogame pre-orders (amazon prime members) im confused? why? — AmazonHelp: @115852 We still offer discounts on eligible physical game pre-orders. For further details on Prime benefits: https://t.co/80y2YnlQGJ ^MB
- Real example `1698`: @AmazonHelp Thats the thing I told customer service. I created a new email address for the Prime trial and forgot it. What can I do so I'm not charged? — AmazonHelp: @116082 Hey Corey! Even on the new account you made you can turn of the auto renew through the same link ^SK posted for you. ^AJ
- Real example `1706`: @AmazonHelp I have tried. It’s not allowing me to access my account to cancel my membership, I haven’t even used prime in almost 3 months. — AmazonHelp: @116083 I'm sorry to hear you're not able to access your account. Please use this link instead to contact us: https://t.co/zYVX1Qi29G. ^LH

### `account_access_security` — Account access and security
- Definition: Login, password, verification, account hold, or suspicious-access problem.
- Include: Cannot sign in, locked account, password/OTP/verification trouble, hacked account.
- Exclude: Payment-only dispute with no account-access issue.
- PII/account information: Yes — security verification required.
- Likely handling: Secure recovery channel; do not request credentials publicly.
- Annotation difficulty: Low.
- Historical AmazonHelp response pattern: {'substantive': 1506, 'generic_greeting': 281, 'contact_redirect': 202, 'dm_redirect': 19, 'very_short': 12}
- Real example `1701`: @AmazonHelp You have to log in. I don't remember the email address I used. Can you look up the account by my bank information? — AmazonHelp: @116082 It would be best if you get in touch with us by phone or chat.use this link to do so:  https://t.co/hApLpMlfHN ^CH
- Real example `3729`: @AmazonHelp i reset my password 3 times and it still says incorrect you gotta be shitting me — AmazonHelp: @116611 I'm sorry for the trouble! Have you tried the steps outlined here? https://t.co/POJ37mWiEk ^LA
- Real example `3732`: @AmazonHelp I can’t log in because it’s locked. — AmazonHelp: @116612 The link ^TN provided will allow you to contact us without signing in! Select "skip log in" and you'll be in touch in no time! ^VB

### `payment_charge_issue` — Payment, charge, or Amazon Pay issue
- Definition: Unauthorized, duplicate, failed, or otherwise disputed payment.
- Include: Double charge, unknown charge, payment failure, card/bank/Amazon Pay dispute.
- Exclude: Expected refund after return; Prime membership management.
- PII/account information: Yes — secure billing lookup.
- Likely handling: Secure billing escalation with general authorization guidance.
- Annotation difficulty: Medium.
- Historical AmazonHelp response pattern: {'substantive': 1534, 'generic_greeting': 248, 'contact_redirect': 159, 'very_short': 10, 'dm_redirect': 24}
- Real example `18408`: amazon japan still hasn’t verified my bank account and i’m getting STRESSED — AmazonHelp: @120091 We can't confirm your account details via Twitter, so please contact JP Customer service at: https://t.co/J6YEizo6qC TN
- Real example `18894`: @115850 Funny!Yesterday prime account activation was rs499 , today 999 with 500 cash back into amazon pay . Creepy offer for intense user https://t.co/b0DdLAmFoe — AmazonHelp: @120224 Umm.. creepy, not sure. The offer was rolled out keeping in mind the benefit of our existing customers. Enjoy! ^AB
- Real example `19194`: @AmazonHelp thnx, matter resolved. — AmazonHelp: @120263 Glad the issue was resolved. Thank you for keeping us posted. ^SB

### `product_availability_pricing` — Product availability, pricing, and promotions
- Definition: Stock, restock, price/deal, authenticity, pre-order, or promotion question.
- Include: In/out of stock, restock, pre-order, price/deal, coupon/promo code, authenticity.
- Exclude: Seller service dispute; delivered defective item.
- PII/account information: Normally no.
- Likely handling: Product-page policy or stock-alert guidance; escalate listing inaccuracies.
- Annotation difficulty: Low.
- Historical AmazonHelp response pattern: {'substantive': 1457, 'contact_redirect': 100, 'generic_greeting': 358, 'very_short': 13, 'dm_redirect': 9}
- Real example `1721`: @AmazonHelp Never got the beta and now I’m being told I won’t get ANY of the other stuff. Including Last Jedi content and or bonus classes. Anything! :( — AmazonHelp: @116088 We'd like to see what we can do to help. What date did you place the order on, and which version did you order? ^MB
- Real example `1726`: @AmazonHelp Star Wars Battlefront 2 Elite Trooper Deluxe Edition Playstation 4 https://t.co/6K7WdDcY2P preorder info is in description. Thanks for help — AmazonHelp: @116088 Thanks for the link. We are not a participating retailer to receive the bonus content. Details: https://t.co/hJIrBtSMrl ^BE
- Real example `1722`: @116090 Saying I preordered to early, terrible customer service. Won’t renew prime if this isn’t fixed. — AmazonHelp: @116088 I'm sorry for the frustration, Anthony! Can you tell me more about which pre-order bonuses are missing? ^EA

### `marketplace_seller` — Marketplace seller issue
- Definition: A third-party seller is unresponsive, refuses a remedy, or triggers an A-to-Z concern.
- Include: Seller/merchant contact, seller refusal, marketplace or A-to-Z guarantee.
- Exclude: Amazon-fulfilled delivery issue with no seller relationship.
- PII/account information: Usually yes — order/seller details.
- Likely handling: Contact Seller guidance; escalate eligibility for A-to-Z claim.
- Annotation difficulty: Medium.
- Historical AmazonHelp response pattern: {'substantive': 1616, 'generic_greeting': 254, 'very_short': 13, 'contact_redirect': 233, 'dm_redirect': 19}
- Real example `2543`: @AmazonHelp Just now, don't use Amazon much so didn't know the process if you don't receive an item — AmazonHelp: @116314 Please allow 48 hours for the seller to respond, Allen. Let us know how it works out and if we can help with anything else! ^CN
- Real example `2544`: @AmazonHelp Wasn't tracked as sent via Royal Mail. I've emailed the seller. — AmazonHelp: @116314 How long has it been since you've e-mailed the seller? ^TR
- Real example `16115`: @AmazonHelp Ur customer care didnt provide me a correct answer — AmazonHelp: @119535 I'm sorry about the experience. Kindly share your details here: https://t.co/beaaDm0muc and we'll check. ^GK

## Golden-set unit recommendation

**B. Customer inquiry + relevant conversation context.** The measured context-resolved fallback cases show that a reply can be semantically incomplete in isolation while its preceding customer turn supplies the customer goal. Preserve the target customer message, the immediately relevant preceding turns, and message type/state as annotation fields. This is a recommendation only; this audit does not create a golden set.

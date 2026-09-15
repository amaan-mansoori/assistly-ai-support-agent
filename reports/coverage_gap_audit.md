# Coverage Gap Audit — Proposed Final Intent Taxonomy pending human annotation

> Local analysis only. Unsupervised clusters are exploratory and are not treated as ground-truth intents.

## Exact current coverage

- Cleaned English corpus: **117,934**
- Current defined-label coverage: **37,626 (31.9%)**.
- Current `other_unclear`: **80,308 (68.1%)**.
- Residual messages with recovered preceding context: **35,341 (44.01%)**.
- Context-resolved into an existing or defensible augmented goal: **3,064**; still unclear even with available context: **32,277**.

## What the residual represents

Message type and customer intent are separate. The table below describes messages, not new intent labels.

| Message type / state | Count | % of residual |
|---|---:|---:|
| `message_type:problem_statement_or_update` | 40,733 | 50.72% |
| `message_type:question_or_request` | 29,499 | 36.73% |
| `message_type:acknowledgement` | 4,562 | 5.68% |
| `message_type:complaint_or_feedback` | 2,209 | 2.75% |
| `message_type:information_provision` | 2,160 | 2.69% |
| `message_type:conversational_social` | 1,145 | 1.43% |
| `conversation_state:initial_or_context_unavailable` | 44,967 | 55.99% |
| `conversation_state:followup_in_thread` | 35,341 | 44.01% |

## Tested coverage hypotheses

| Hypothesis | Isolated hits | Context-supported hits | Decision |
|---|---:|---:|---|
| Digital content, device, and app support | 3,054 | 4,319 | new intent if examples concern troubleshooting/access rather than membership management |
| Gift card, promotion, cashback, and voucher | 994 | 1,464 | new intent if a benefit/redemption/dispute is the primary goal; pricing-only questions remain product availability/pricing |
| Product information, compatibility, and warranty | 224 | 346 | merge into a broadened product inquiry intent if examples are pre-purchase information requests |
| Customer-service/contact-channel request | 4,462 | 6,858 | retain as routing/state metadata unless the underlying issue is unavailable; it is not automatically a customer intent |
| Generic order/account question | 2,711 | 4,132 | merge into delivery status/account access only when the goal is explicit; otherwise retain other_unclear |
| Shipping address/instruction issue | 231 | 374 | merge into order cancellation/change; not a separate intent unless evidence supports a different remedy |

## Residual clustering

TF-IDF features: **3,000**. KMeans ran at K=8, 10, 12, 15, 20; exact counts are in the raw artifact.
Top residual bigrams: [['customer service', 2585], ['day delivery', 1303], ['day shipping', 1071], ['customer care', 921], ['delivered today', 554], ['don know', 480], ['order delivered', 430], ['haven received', 420], ['amazon india', 407], ['delivery service', 366], ['placed order', 359], ['gift card', 355]]
Top document co-occurrences: [['customer + service', 2811], ['day + delivery', 1884], ['amazon + order', 1407], ['amazon + delivery', 1382], ['delivered + order', 1330], ['delivery + order', 1291], ['day + prime', 1157], ['amazon + service', 1122], ['day + shipping', 1114], ['delivery + prime', 1105], ['delivery + today', 1029], ['amazon + customer', 992]]

### cluster_2: 40,928 (50.96%)

- Top keywords: `just, delivery, help, prime, ordered, email, thank, account, product, got`
- Top bigrams: `day delivery, day shipping, haven received, gift card, pre ordered, let know, black friday, safe place, echo dot, need help, delivery drivers, delivery driver`
- Co-occurrence: `day + delivery, delivery + prime, day + prime, day + shipping, days + prime, delivery + just, delivered + delivery, help + need, delivery + ordered, haven + received, day + days, day + ordered`

1. Customer `2192528`: @AmazonHelp i understand delivery drivers can get lost and go to the wrong location but there is a contact number they can use that cant be too hard too do
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: having an absolute nightmare with @115821 | AmazonHelp: @641737 I'm sorry for the frustration. We'd like to address this. At your convenience, please reach us via phone or chat here: https://t.co/oGDklGgbCZ ^SJ
   - AmazonHelp response: @641737 I certainly understand! Have you had the chance to reach out to us through the link previously provided to you? ^HC
2. Customer `2350962`: @AmazonHelp hi there, I preordered LA Noire on PS4 over a month ago and paid to have it on release day.
My order details are now saying it won’t arrive till Wednesday... is there any chance of getting it on release day as I have paid for?
   - State/type: `initial_or_context_unavailable` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `order_status_or_account_question`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @679486 Sorry, we're unable to access accounts on Twitter. We're happy to look into the order and available options here: https://t.co/hApLpMlfHN ^LI
3. Customer `2771741`: @116316 Einen Student drei Monate vorher erinnern? Probiert es nochmal zwei Tage vorher https://t.co/qUW9M8EOlK
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Okay, @116316 ist wohl ein bisschen im Kalender verrutscht. 😅 https://t.co/SKWQDadXvK | customer: @774774 Verrutscht? Nur eine Hilfestellung für dich, dass du Ostern nicht vergisst!
^AM 😎😁😂
   - AmazonHelp response: @774774 Of course, will do 🐰 ^AS
4. Customer `2367333`: @AmazonHelp 18 U.S. Code § 1701 - Obstruction of mails generally. Whoever knowingly and willfully obstructs or retards the passage of the mail, or any carrier or conveyance carrying the mail, shall be fined under this title or imprisoned not more than six months, or both.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @442107 Terribly for the misunderstanding Laurence. If you following that link and select an issue, use 'I do not have an Amazon account but need assistance'. From there you can contact us without account information and we can work together to get this fixed. ^JD
5. Customer `814386`: @AmazonHelp Book was released on 10/17 and the status has been “not yet shipped” since then.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Dear @115821 , Why has the book that I pre-ordered back in May and was released three days ago still not yet shipped? No love, me | AmazonHelp: @313954 Oh no! We'd like to help. What delivery date were you given? Without revealing account info., can you give us more details? ^SE
   - AmazonHelp response: @313954 Some orders ship and arrive in the same day! We do still expect your book to arrive between 10/23 and 10/24 as expected. ^BE
6. Customer `1678565`: @AmazonHelp This isn't even two days after it comes out but THREE (i have prime) and I ordered this in August!! What's the point?!?
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp I'm getting tired of y'all promising to have books delivered the day they cone out for that to literally NEVER happen. https://t.co/4psC0HC1mm
   - AmazonHelp response: @510542 I'm really sorry Molly ^AT
7. Customer `2983654`: @AmazonHelp I have spoken to the health team very often. It has resulted in no help at all as diesel junior call centre people. I need some help from an expert.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `digital_content_device_support`; coherent enough: `True`; hypotheses: `none`.
   - Preceding context: customer: @121284  I am an Echo  owner. I am extremely frustrated and would like to be contacted by some senior software person. Otherwise I am compelled to return the product. My Amazon account ID is __email__ it will also have my mobile number. | AmazonHelp: @132155 We're extremely sorry for the unpleasant experience. You may reach out to our support team using the link provided here: https://t.co/2t6DQoUmNZ. We'll be glad to help.
Please don't provide your details, we consider it to be personal information.^AR
   - AmazonHelp response: @132155 We understand you are not able to reach us via the link provided earlier. Kindly put 'N/A' on the twitter handle and submit your details and we'll get in touch with you. As this being a public platform we wouldn't be able to view your account/order details here. ^VM
8. Customer `1235571`: @AmazonHelp @115851 I STARTED THIS TRAIL ON 22ND &amp; INFORMED YOU VIA TWITTER ON 26. NOTHING WORKED SO FAR?
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115850  if you can't handle customer service.  Stop this business in interiors.  #worstcustomerservice https://t.co/7WVgw6Xagq | AmazonHelp: @409804 I'm sorry about the situation. Kindly share your details here: https://t.co/GIJyeYqKE0 and I'll look into this. ^SG
   - AmazonHelp response: @409804 Please write back to the email you received from social media team. We'll check the details and get back to you. ^SQ
9. Customer `222856`: @AmazonHelp We would like to see SBI and ICICI debit/credit cards also signed up for cash back offers along with Citi Bank.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `gift_card_promotion`; coherent enough: `True`; hypotheses: `gift_card_promotion`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @169226 Thanks for taking your time out. I'll make sure to forward your comments to our teams (1/2) ^VM
10. Customer `1300543`: @AmazonHelp I will provide all details
   - State/type: `followup_in_thread` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp I don't receive same phone . Local phone delivered by company . I will logge FIR against Amazon and team https://t.co/zHD6VOPQ56 | AmazonHelp: @423690 Please don't provide your order details, we consider it personal information. Our Twitter page is visible to public. ^MJ
   - AmazonHelp response: @423690 We've sent a correspondence to your registered email address. Kindly check. You may reply to the email for further help. ^AK
11. Customer `2949491`: @amazonhelp ciao, giusto perché lo sappiate: corriere Hermes ha avvisato x un ritiro reso il 23/11, poi il 24/11 e poi 27/11. Non è mai passato nessuno. Sono passati oggi (29/11), senza avvisare. #Epicfail
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @814547 Mi spiace per l'accaduto! Se non l'hai già fatto segnalalo al Servizio Clienti tramite questo link: https://t.co/7LOgclPYpD. A presto! ^CS
12. Customer `946558`: @AmazonHelp It's slow as hell &amp; the stream becomes choppy every ten minutes. The problem isn't hardware based or connection based coz Netflix runs fine
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Is it just me or is the @119625 PS4 app complete garbage? | AmazonHelp: @207236 That's quite a remark. Could you let us know if you're facing any issues with the app? ^SQ
   - AmazonHelp response: @207236 I'm sorry for the trouble you are facing with our app, call us here: https://t.co/vlvfJr4nN9 &amp; we'll check this for you. ^MJ
13. Customer `426313`: @AmazonHelp I downloaded an second audio book during my 3month trial but got charged, please may you advise how to help
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @216400 Hi Tommy- Which website is your trial with? https://t.co/nUUp5MLhYl https://t.co/ykTUEmdsQA or? ^NV
14. Customer `1936603`: @AmazonHelp FYI I filled out the contact form but no one called me
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Hey @AmazonHelp I saw I guy hurling packages over fences yesterday - Bill Kennedy near I-20, ATL - QA/QC much? https://t.co/sSkAuH2J49 https://t.co/r6iZvhlzK6 | AmazonHelp: @576157 Oh no! I'd like a member of team to look into this with you! Please submit your info here: https://t.co/Oqn6EqMjBN ^ME
   - AmazonHelp response: @576157 Hi Alexandra! You should've received an e-mail from a member of my team. Be sure to check spam/junk folders! ^FD
15. Customer `2952308`: @AmazonHelp Ciao! Uno non ha il messaggio che avevo scritto, l’altro ha metà dei caratteri non leggibili (come se mancasse la cartuccia nella stampante) e l’altro non c’è proprio
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Cara @120540 , su tre pacchetti regalo sbagliare tre bigliettini d’auguri è una media un po’ alta. Non voglio immaginare cosa farete sotto Natale.

Io peró il servizio l’ho pagato (e non poco). | AmazonHelp: @815199 Mi spiace! Puoi darci maggiori dettagli? Che tipo di errore contengono i bigliettini d'auguri? ^CS
   - AmazonHelp response: @815199 Grazie per il chiarimento! Hai già contattato il Servizio Clienti? ^CS

### cluster_5: 7,184 (8.95%)

- Top keywords: `amazon, delivery, india, amazon logistics, logistics, account, amazon india, product, help, just`
- Top bigrams: `amazon india, amazon logistics, amazon account, amazon delivery, amazon echo, service amazon, gift card, amazon music, buy amazon, experience amazon, amazon shipping, amazon gift`
- Co-occurrence: `amazon + delivery, amazon + india, amazon + service, amazon + just, account + amazon, amazon + help, amazon + product, amazon + ordered, amazon + delivered, amazon + customer, amazon + got, amazon + logistics`

1. Customer `416691`: @AmazonHelp

Just returned a "mattress protector", pickup tracking ID 511353091893, to the Amazon agent but didn't get the SMS confirmation
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @182581 Also, please don't provide your order details, as we consider it to be personal info. Our Twitter page is public. (2/2) ^ST
2. Customer `606068`: @AmazonHelp Amazon.in. I know the list of accepted payments. I used a Visa and credit (Master) cards to pay. It doesn't seem to accept! What should I do?
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Hey @AmazonHelp, I've tried every card I have to pay on your website. It fails every time! Can you help? | AmazonHelp: @264045 Hey Nim, which site are you using: https://t.co/nUUp5MtGzL, .co.uk or any other one? Here is the list of the payment methods we would accept: https://t.co/TwBk7xqv3V ^MA
   - AmazonHelp response: @264045 I'm sorry that your payments are not going through. Could you let me know the error message that you see while making a payment? ^AU
3. Customer `1507895`: #@132995 #Amazon I've just bought a onepus 3t from Amazon and it's having ghost touch problem , really need help , after spending hard earned money feeling helpless
Pease get it replaced ASAP.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @469983 them here: https://t.co/rAnq9y86TA. They should help. 2/2 ^NK
4. Customer `1611056`: @115821  i need urgent from  amazon help regarding my  ordered shipment  with tracking id 209118315819 callback requested  on 9990676182.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @494502 Please don't provide your order details, we consider it personal information. Our Twitter page is visible to public. (2/2) ^AS
5. Customer `1240066`: @AmazonHelp If I'm ordering an item that's supplied from Amazon Warehouse (from USA to Canada) will there be an import charge/fee?
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @410869 Great question! Have you taken a look here: https://t.co/8YhdldNyp3 for details on import fees? Let us know if this helps! ^FR
6. Customer `2516937`: @AmazonHelp Pela própria Amazon.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Nunca mais compro pela @117086 primeira vez que compro e já me decepciono. Me enviaram um exemplar de uma graphic novel com duas páginas rasgadas. Primeira, última e péssima experiência. Desfazendo meu cadastro já! https://t.co/AV4yZfgOGi | AmazonHelp: @144096 Olá Dri! Sentimos muito o acontecido! Poderia nos confirmar, o seu pedido é vendido pela Amazon ou um vendedor externo do nosso site? ^HC
   - AmazonHelp response: @144096 Neste caso por favor acesse o seguinte link para devolver o livro: https://t.co/nzwXNsIYIz  ^JJ
7. Customer `606113`: @AmazonHelp Amazon site is saying it will arrive on Friday. UPS on the other hand has it as a rescheduled delivery for Monday.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: I guess prime isn’t worth a damn when 2 day shipping turns into 4. I just need my damn vacuum lol @115821 | AmazonHelp: @264050 Were you advised at checkout that it will take longer to arrive or did you receive an e-mail update? ^KI
   - AmazonHelp response: @264050 Hey Liz, if you check the tracking here: https://t.co/Y5jpI9ys9c could you tell me what the latest update has been?^TI
8. Customer `1077774`: Amazon, honey, I do not pay for prime so that AMZL can mark things as delivered, not deliver, and then mysteriously drop them off 2wks later.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @374256 I'm terribly sorry for this conflicting information. We'd like to look into this further. Please pass your details to us here: https://t.co/y0Qi2lJHBy ^RR
9. Customer `283989`: @AmazonHelp Seems like you don't. You folks gave me a wrong Amazon Agent number. And I'm reporting it.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115850 @AmazonHelp wrong info of AmzAgent provided. Was told "he will come" I said why was I given wrong no., he simply hung up! | AmazonHelp: @183640 Nishit, I understand your concern, please contact us here: https://t.co/rS49hgaADF so that we can assist you accordingly. ^BV
   - AmazonHelp response: @183640 May I know if you have reported this to our support team using the link provided earlier? ^SK
10. Customer `1905585`: @AmazonHelp @115851  @115850  
No its not 
You guys should have heard the cs guys talk to me
Amazon's fault and they tell me cant help in anyway
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115851 @115850 @AmazonHelp still getting automated tweets jeff 

Nobody reach out to me or call from amazon support | AmazonHelp: @219626 That's quite a comment, Rohit. We are already following up with your issue here: https://t.co/80DEOCdFh5. Please check. ^NK
   - AmazonHelp response: @219626 I get your disappointment, Rohit. Could you confirm If you have shared your details through the link provided earlier? ^NK
11. Customer `2110463`: @AmazonHelp Why is amazon.ca saying there is no account linked to my email address? What is the best way to look into this?
   - State/type: `initial_or_context_unavailable` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @622570 I'm sorry for the account issues! To speak to our account specialists, please contact us here: https://t.co/QFCr5CIjfk ^WT
12. Customer `984697`: @AmazonHelp Huh!!! Mater s escalated 2 concern team.. Same thing I m listeing frm lst 11 dys... Wonderig i Amazon s creatng nw departm. 2 slve my problm
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp Even filling that form provided by u...  No revert... Pathetic service | AmazonHelp: @353419 I'm sorry about the stretch. If you have provided details in the link, our team will work on the issue &amp; write back soon.^SF | customer: @AmazonHelp From 11 days I am writing on this issue ... No soln provided..... | AmazonHelp: @353419 You might have received an E-mail correspondence from us. Kindly check here: https://t.co/fYrzNInVt2 and reply (1/2) ^MO
   - AmazonHelp response: @353419 My apologies for the delay, Gourav. We are working and will get back to you as soon as there is an update. ^KS
13. Customer `197529`: @AmazonHelp for amazon uk same day prime is ready for ng7 but it says "...no results for this search with Same-Day to your address."
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @162473 Some items and addresses may not be eligible for Same-Day delivery. More info about this here: https://t.co/jDRhVZDj8k ^GL
14. Customer `1286978`: @AmazonHelp I am in Brazil and the cost of the call would be high.. Would be possible for you to see if my complaint is being considered by Amazon?
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp I already sent my complaint through that link on Sunday Oct. 15 and have been waiting for an answer since!.. https://t.co/EgKOy6bcne | AmazonHelp: @421025 Understand, have you contacted the SAC via phone? ^DA | customer: @AmazonHelp I thought a written complaint is a more than valid one. "You should receive a response from one of our representatives within 12-24 hours." | AmazonHelp: @421025 Jenny, to receive an immediate response, we suggest you contact via telephone. That way our agents can research your case. ^LG
   - AmazonHelp response: @421025 We can't access your acct here but we'd like to look into this. Please send us your contact info here https://t.co/SccPG9obnp ^KH
15. Customer `1728585`: Hey @AmazonHelp I have a query re a boxset I recently bought - am I good to drop you a DM?  #Amazon #Help
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @522623 Sure you can :) Or you can just ask us here too :) ^AS

### cluster_8: 6,860 (8.54%)

- Top keywords: `order, delivered, delivery, amazon, placed, help, cancelled, order delivered, received, order number`
- Top bigrams: `order delivered, placed order, order id, order number, order placed, cancel order, cancelled order, day delivery, place order, prime order, order order, amazon order`
- Co-occurrence: `delivered + order, amazon + order, delivery + order, help + order, order + placed, days + order, day + order, order + prime, order + received, just + order, cancelled + order, got + order`

1. Customer `1763149`: @115830 Ordered a book &amp; it was dispatched on 14th Oct, estimated date was 18-24th Oct, but no delivery.Do not want to order for it again.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @530468 We're here for you! What does the tracking currently display? Check: https://t.co/aaDyEz1VgE and let us know, please! ^JE
2. Customer `568344`: Received an @115821 order like this from @118706. I didn’t order an open box item. 😑👎🏻 https://t.co/sVwK4wwZis
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @253349 Oh my goodness, I'm so sorry your package arrived in that condition, Nicole! Was your order damaged at all? ^AM
3. Customer `1702220`: @115850 Finally, I received my order.

Thank u amazon
   - State/type: `followup_in_thread` / `acknowledgement`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `order_status_or_account_question`.
   - Preceding context: customer: @115850 
Pathetic service, expected date for delivery was 7th and today u all extended the date.
Not expected from u amazon.
   - AmazonHelp response: @516092 Glad to hear your package got delivered. I'll certainly forward your experience internally for improvements. ^NK
4. Customer `1501828`: @AmazonHelp If I had placed the order on a Friday maybe a month ago or so, it would have been for the Saturday, not the following Monday. Make sense?
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp So, why have you suddenly stopped delivering on weekends to my area without mentioning it? Rather reduces usefulness of Prime. | AmazonHelp: @468593 Without providing any account information can you tell me more about the issue? ^CH | customer: @AmazonHelp Sure. Not long ago a Prime order placed on Friday would be delivered Saturday. Now, it's Monday. | AmazonHelp: @468593 I'm sorry for the troubles! Just to clarify, were you sent an e-mail about a change in delivery? Check spam/junk folder. ^AL
   - AmazonHelp response: @468593 Some items may take longer to process and dispatch. More information here: https://t.co/AQT9h7621z ^AB
5. Customer `73558`: @115850 How do I get the invoice if I don’t remember my id &amp; order number?
   - State/type: `initial_or_context_unavailable` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `order_status_or_account_question`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @132449 We understand your concern regarding the invoice. Kindly contact us from here: https://t.co/O7KjQO4yOB and we'll look into this and assist you further. ^VH
6. Customer `787524`: @AmazonHelp This is freaking idiotic. You can't get a single order right? After the entire day, now your rep says it will be done tomorrow. WTF
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp I replied. | AmazonHelp: @296764 Thanks for the update. Once we receive your revert we'll work on it and get back to you. ^MM | customer: @AmazonHelp entire day passed by and no delivery yet. This was to be done yesterday morning. PATHETIC | AmazonHelp: @296764 We apologize for the stretch. Keep a tab on your registered e-mail. We'll reach out soon. ^CB
   - AmazonHelp response: @296764 Apologies for the delay. Please wait for the update from us. ^HN
7. Customer `248601`: @115830 thank you for failing to deliver my second order in a row, both meant to be Prime  / Next day.  I officially hate Amazon.
   - State/type: `initial_or_context_unavailable` / `acknowledgement`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @175064 I'm sorry your order missed the estimated delivery date: https://t.co/BQmcNXViiI. Please contact us: https://t.co/oGDklGgbCZ. ^AF
8. Customer `1381536`: @AmazonHelp My order details Order no. 0210232119 for 2 quantity.
   - State/type: `followup_in_thread` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `order_status_or_account_question`.
   - Preceding context: customer: @115821 even confirmation for order by Amazon and hometown that my order will be delivered. Both have no clues of my delivered #cheater | customer: @115821 Ready for dispatch; Order no. 0210232119 for 2 quantity. Thank you for choosing Home Town!For any queries call 18002100004 received on 26/10 | AmazonHelp: @441471 Sorry for the inconvenience. Please contact our support team here: https://t.co/vlvfJr4nN9 we will get it resolved. ^GU
   - AmazonHelp response: @441471 Just to confirm, have you reported this to our support team as requested earlier? If not kindly let them know about it. ^AB
9. Customer `1575623`: hi @AmazonHelp i sent you a dm because i received my order but the product was missing
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `order_status_or_account_question`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @485516 Thanks for reaching out! We've responded to your dm. ^JN
10. Customer `2103681`: @115850 pathetic pickup experience for my order # 404-3967148-4720314
Have requested pickup since 1 week and no one shows up, only rescheduling. Calling customer care only rescheduled it further.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access, order_status_or_account_question`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @621113 Apologies for hassle, I'd like to assist you with this, please fill this form; https://t.co/beaaDm0muc &amp; I’ll contact you soon.^AH
11. Customer `1716156`: Pathetic services by @115821 @AmazonHelp. Cancelling order after 7-8 days. @115851 Please look into it.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @519715 mentioning the reason for cancellation. Further, I'll forward your experience as feedback internally for a review. 2/2 ^AR
12. Customer `122719`: @AmazonHelp These are my details of order-order #407-0701499-7452341,date of placement of order 10 Nov, contacted Amazon assistance on 3 occasions,once you check you will get https://t.co/MJei7NGKF9 story is in my tweet
   - State/type: `followup_in_thread` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115850 I am looking for answers for non delivery of my product and also pathetic customer relationship attitude of Amazon inspire of shopping so much.I had booked item on 10 Nov it was to be delivered on 17th but till date no delivery,have spnk to Amazon assistance,most sweet spkg guys | AmazonHelp: @143382 I'm sorry that you haven't received the product yet. Kindly share your details here: https://t.co/GIJyeYqKE0 and we'll look into the issue for you. ^GD | customer: @AmazonHelp Done | AmazonHelp: @143382 We can't gain access to your account details via Twitter. Could you confirm sharing your details in the link provided above? ^KA
   - AmazonHelp response: @143382 Please don't provide your order details, we consider it personal information. Our Twitter page is visible to public. ^VN
13. Customer `1387233`: @AmazonHelp It's regarding my last order of one plus 5 phone
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `gift_card_promotion`; coherent enough: `True`; hypotheses: `none`.
   - Preceding context: customer: @115850 : you people tourchered me lot and latter offer Rs 250 as gift card for all those mental tourchered. | customer: @115850 Is this what value of your services. Really too much embrassing from me . You just take your piecemeal gift card I don't it. | AmazonHelp: @442781 Sorry for any ordeal, Shweta. Could you let us know what went wrong? We'd like to look into it. ^HD
   - AmazonHelp response: @442781 Sorry for the hassle. Please report this to our support team here: https://t.co/vlvfJr4nN9 and we'll check this. ^HN
14. Customer `741527`: @115830 why am i not getting an email confirmation of my order? plus i sent myself a gift card and that has also not been received. please advise
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `gift_card_promotion`; coherent enough: `True`; hypotheses: `gift_card_promotion, order_status_or_account_question`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @297346 Oh no! Have you checked your Spam or Junk folders?  ^CO
15. Customer `1234055`: @AmazonHelp Techylots - yes one of your “top” sellers! Fed ex says they haven’t even shipped my order and is not in system
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `order_status_or_account_question`.
   - Preceding context: customer: @AmazonHelp trying to get iPads ordered from Techylots. WHERE ARE THEY? Need to speak with someone today not 2 days from now.😩👺 | AmazonHelp: @409445 Was this a seller fulfilled order placed on our site? ^LB
   - AmazonHelp response: @409445 We can't view accounts via Twitter. Have you tried contacting the seller regarding your order, Rosa? https://t.co/dqTSHMOC60 ^LA

### cluster_3: 5,125 (6.38%)

- Top keywords: `customer, service, customer service, day, delivery, care, customer care, day delivery, prime, shipping`
- Top bigrams: `customer service, customer care, day delivery, day shipping, worst customer, delivery service, amazon customer, prime day, customer support, worst service, pathetic service, called customer`
- Co-occurrence: `customer + service, care + customer, delivery + service, amazon + customer, amazon + service, day + delivery, customer + delivery, service + worst, customer + worst, day + prime, customer + order, customer + just`

1. Customer `2867238`: 4 minutes on the phone with @115821 customer service,and you still can't understand my email. Smh, ready to hang up and start over.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @796310 I'm sorry you're having difficulties with our phone support. Without divulging personal or account information, would you mind telling us about the issues you're facing? We'd like to help where we can. ^KL
2. Customer `397429`: @115850 This made my day. Thank you :)) https://t.co/fyFfwNiHCH
   - State/type: `initial_or_context_unavailable` / `acknowledgement`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @210101 We just try to make our customers happy with our service. I'm glad you had an amazing experience. Happy Shopping :) ^OS
3. Customer `77618`: @115850 @AmazonHelp just share the things here so that world can knows you well and your robotic customer services...

@115851 @115821
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115850 making fool of us and playing with their Database.

First of All, taking 5 days delivery for "Prime-Customer" and on 5th days updated their records with order status Delivered while not attempting for delivery.

Later than ask you to wait for next 3 days.

#Logical ????
   - AmazonHelp response: @133290 I get your disappointment. However, Twitter being a Social Media platform we can't view your order/account information. I'd request you to share your details through the link provided above for better assistance. Appreciate your cooperation. ^KH
4. Customer `1760560`: @AmazonHelp Your customer support bloke was an absolute hero cheers lads
   - State/type: `followup_in_thread` / `acknowledgement`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @AmazonHelp where's my book? Has the delivery bloke crashed his van on the way? https://t.co/QKlqrxbp57 | AmazonHelp: @529873 Delivery can still occur up until 21:00. Please keep us updated on its delivery! ^MH | customer: @AmazonHelp @AmazonHelp it didn't turn up :( | AmazonHelp: @529873 Let's find out what is going on with your book in real time here: https://t.co/JzP7hlA23B ^JZ
   - AmazonHelp response: @529873 Awesome! Glad to hear we could get that taken care of! Make sure to let him know how great he did on that e-mail survey. ^JZ
5. Customer `318785`: @115850 fucking site and fraud service and offer...
   - State/type: `initial_or_context_unavailable` / `complaint_or_feedback`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @192049 This an't what we thrive to deliver. Kindly let us know where did we go wrong. ^CB
6. Customer `439807`: @AmazonHelp @219399 Your own CEO's words, @AmazonHelp, and you do exactly the opposite. Wah!

Customer first and be patient, @43750, really, mate? https://t.co/nUSnG5tztW
   - State/type: `followup_in_thread` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115851 Your @115850 delivery people don't even wait for 2 minutes at door for a handicapped person to open the gate. Pathetic. | AmazonHelp: @219399 Apologies for your experience with the delivery agent. Please report this here: https://t.co/vlvfJr4nN9 and we'll investigate. ^HK | customer: @AmazonHelp Your delivery agents are Taking shortcuts and wrong messages. The consignment was never delivered. @115850 https://t.co/rX5gPH7ZLX | AmazonHelp: @219399 Sorry about that. Kindly get in touch with us here: https://t.co/ohsCHsr6qQ and we’ll be glad to help you. ^AG
   - AmazonHelp response: @294531 Apologies for the trouble. Kindly fill in your details with the link provided earlier and we'll sort it out for you. ^PB
7. Customer `1655083`: @115850 @115821 Had a really bad experience with Amazon India its been the third day contacting with pathetic customer care service
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @378594 Please share your details using the secure link provided in the previous correspondence and we will contact you soon. ^RI
8. Customer `516649`: @149087 @115850  stupid service i did not get my phone yesterday &amp; they say they cldnt cntct me ... rubbish excuse wts d use if paying 100₹ fr getting it in 1 day.. if u cldnt deliver/ i had to cancel my trip to goa just bcz of ur pathetic service
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Do you also feel that Face Unlock is so fast you just want to show the whole world!? | customer: @149087 Waiting..... ❤❤❤❤❤❤ https://t.co/bBfYZIiltP
   - AmazonHelp response: @239066 I'm extremely sorry about this experience, Abhishek. Do not worry. Please report this to our support team here: https://t.co/TdDksLo6Mf and we'll look into this. ^MK
9. Customer `2847339`: This isn't 1 day delivery @115830 mate https://t.co/mY1w7kJ47b
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @791897 Sorry for the trouble! One-Day Delivery refers to the transit time, in business days, once the item has dispatched. Some orders may be out of stock or require extra processing time. You can learn more about One-Day Delivery here: https://t.co/JgOCWnRnvg. ^VB
10. Customer `2831608`: @115830  why are prime products not being delivered until Thursday.  Prime is supposed to be next day delivery 😡
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @383302 Hi there! A possible reason for the delay is due to the time of year. We're very busy at the moment and this is resulting in some deliveries taking a little longer. Take a look at more info here: https://t.co/o3kN7RHTtS ^SM
11. Customer `111817`: @115821 Your customer service is terrible. There was a mistake made on my order and I tried to change it. 3 reps and 2 supervisors couldn’t help. One supervisor supposedly named “P.R” was horrible. When I asked to be transferred to some1 else, he says he’s the top guy at Amazon.
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access, order_status_or_account_question`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @140835 Thanks for reaching out! We can help with this! Just to clarify, were you trying to change the details of an order after it had shipped? ^TK
12. Customer `2929504`: @AmazonHelp My number is blocked on the app i m unable to receive calls from your side i want to purchase tv and i m unable to contact customer service.. #Frustrated
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access`.
   - Preceding context: customer: @Amazonhelp hi i m not able to call your cust care through app or toll free number please help | AmazonHelp: @810412 Sorry for the trouble with the application. We do not have any number as such. Could you please let us know what is the error message? ^HR
   - AmazonHelp response: @810412 I'm sorry you are having trouble contacting us. Please drop in our details here:  https://t.co/GIJyeYqKE0 and we will help you. ^AH
13. Customer `865827`: @115850 I am not happy with your service.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: Our customers push us to do better every day. Thank you so much, Mrs. Lynette Pereira for sharing your happy moment with us! Gestures like these inspire us to continue serving our wonderful customers in the best way possible. It is still Day 1! #RealAmazonStories https://t.co/dT6JTvZ2H2
   - AmazonHelp response: @533026 Looks like you've had an unpleasant experience. Were any of your recent issues unaddressed? Do let us know and we'll be sure to help you. ^KH
14. Customer `1657362`: @AmazonHelp what’s the email address for customer service?
   - State/type: `followup_in_thread` / `information_provision`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access`.
   - Preceding context: AmazonHelp: @501792 Thank you for letting us know! Do you see a trend with one carrier? ^AR
   - AmazonHelp response: @501792 This link will provide you with the option to e-mail after you follow the prompts here: https://t.co/hApLpMlfHN. ^SY
15. Customer `493436`: @AmazonHelp ordered a week ago and no sign of my delivery. Customer service told me yesterday that they’ve contacted the courier and I’ll get priority delivery but feel like I’m being fobbed off as nothing arrived again today...
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `contact_support_access`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @232632 Deliveries can run until 21:00 so please let us know when you receive the order! ^DD

### cluster_4: 5,010 (6.24%)

- Top keywords: `time, don, know, delivery, don know, prime, want, deliver, just, think`
- Top bigrams: `don know, don want, don think, second time, day delivery, waste time, don understand, nd time, delivery time, day shipping, deliver time, delivered time`
- Co-occurrence: `delivery + time, don + know, don + time, delivery + don, amazon + time, don + want, prime + time, don + just, deliver + time, just + time, day + time, don + prime`

1. Customer `457716`: @AmazonHelp I'm incredibly dissapointed for the first time with amazon for the first time in a while. i demand to speak with an actual person about this as twitter does not have enough characters for me to explain properly
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @223698 I'm sorry you had a poor experience with us. We'd like to help! Without revealing order or account specific details, can you give us more information about the issue today? ^JP
2. Customer `1522560`: .@115821 Why won't your interface switch to one-time from subscription? I try loading and selecting many times in Chrome and Firefox. https://t.co/lMMHGqoiry
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @473133 Sometimes clearing the Cache and Cookies can help w/issues like this, Scott.  Have you tried that yet?(Unable to duplicate)^FR
3. Customer `840877`: @AmazonHelp,dis is d 4th instance I am facing problem and I have approached to CC each time, but with not much success except once.
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115851, am losing interest in Amazon due 2 poor courier services. Amazon is losing a lot of business in India bcoz f this. Need ur help! | AmazonHelp: @320058 In case, your concern is with a delayed order, please reach our support team here: https://t.co/vlvfJr4nN9 for more help.(2/2)^RS
   - AmazonHelp response: @320058 I'm sorry for the inconvenience with this order, write to us here: https://t.co/GIJyeYqKE0 &amp; we'll help fix this for you. ^MJ
4. Customer `351874`: @115821 promised me same day delivery n I still don’t have my game. Smh.
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @199689 Hi, sorry to hear that, what's the current status of the tracking: https://t.co/Y5jpI9gRhE? ^JJ
5. Customer `1722158`: @115850 tomorrow we commemorate 1 year of demonitization... And 90% of my COD still don't swipe cards #DemonetizationDisaster
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @521084 striving to improve our services and we hope to be able to provide a better "COD" payment experience soon. (4/4)^VM
6. Customer `473255`: @115821 Second time now your driver has left our item on the step to get stolen!   He knocks then buggers off before we can open the door.  Not good
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @227692 I'm so sorry your parcel was stolen! Do you have your unattended delivery preferences set up? You can do so here: https://t.co/63M8wgvXtJ We'd also like to make sure your order is taken care of! Please reach out to us via phone here: https://t.co/JzP7hlA23B ^AR
7. Customer `785132`: @AmazonHelp I have called multiple time yet I haven't got any resolution
   - State/type: `followup_in_thread` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: customer: @115821 @115850 @144777 @120320 @15471 
Amazon worst online site to purchase as they play with people emotion .Fake # irresponsible# | AmazonHelp: @307356 Could you please let us know if any of your issues are unaddressed? ^VR
   - AmazonHelp response: @307356 We cannot promise an early delivery. Request you to wait till delivery estimates. ^RW
8. Customer `163563`: I wonder when @115821 is going to finally wise up and have their own means of delivery, bc @118706 can never deliver on time
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @153831 I'm very sorry for any delay. What is the latest tracking showing here: https://t.co/Y5jpI9gRhE We'd be happy to assist in any way possible. ^SK
9. Customer `1692628`: Don't know why I bother paying for #AmazonPrime anymore. Order on Friday, "Guaranteed for Saturday", now looking like Tuesday! @115830 https://t.co/sHRrW9KboO
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @267788 I'm very sorry for this wait. Did you receive a notification on a change in delivery date? ^DO
10. Customer `2414504`: If you live in an area small enough to NOT have @115821 delivery, consider yourself lucky. Every time I see them as the delivery method instead of @118706, @115817, or @81, I just cringe. #fb
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @487280 Do you have a recent delivery issue with Amazon Logistics, Maureen? We'd like to help if at all possible. ^MT
11. Customer `1150914`: @AmazonHelp @115821 you got people in the Philippines who don't speak English handling support and refuse to transfer me to someone in USA
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @390833 We'd be happy to assist. Could you tell us more about the issue you're having? Please no account details. ^MT
12. Customer `1756511`: @115830 have a word with your driver, that attempt time is a load of bollocks. 2nd failed attempt on one of the items! #letdown #lies https://t.co/k4QU7VC27J
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @528899 I'm sorry for the delivery trouble! Please contact us by phone or chat so that we can help investigate: https://t.co/JzP7hlA23B ^SD
13. Customer `2802323`: Don't change your payment info on @115821 unless you want your account deactivated. Oh and then have to call customer support 8+ times and get no help whatsoever!
   - State/type: `initial_or_context_unavailable` / `problem_statement_or_update`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @781722 I'm sorry for the account issues, Molly! We're here to help! Without revealing account information, what information were you given by customer support? ^SE
14. Customer `794431`: @115821 @115850 will u be delivering the products ?
#Pathetic #AmazonIndia product not delivered since 7 days..Don't dare ask to fill form
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @219794 My apologies for the trouble with the delivery, Kapil. Kindly revert to the email sent for more information. ^KS
15. Customer `784356`: @AmazonHelp @115821 @115850 Another JOKE right???? And U don't even feel ashamed of ur service right?? https://t.co/7fhWOmu5qJ
   - State/type: `initial_or_context_unavailable` / `question_or_request`; inferred goal: `insufficient evidence`; coherent enough: `False`; hypotheses: `none`.
   - Preceding context: unavailable in recovered ancestry.
   - AmazonHelp response: @184637 I'd like to take a closer look into this, please share your details here: https://t.co/GIJyeYqKE0. ^AG

## Coverage decision

- Current taxonomy coverage: **31.9%**.
- Conservative revised coverage: **37.33%** (44,028 messages).
- Residual after defensible additions/merges: **73,906 (62.67%)**.
- The additions are limited to digital/device support and gift-card/promotion issues. Product information is merged into the product inquiry intent; address/instruction cases merge into order change. Contact-channel requests remain metadata/routing rather than an intent.

## Recommendation

**No — an 8–12 intent taxonomy cannot reasonably cover the majority of all individual cleaned tweets in this corpus without conflating follow-ups, social/conversational messages, and vague complaints with customer goals.** It can cover a meaningful subset of task-oriented inquiries. Frame the assignment around context-aware inquiry-level classification, retain `other_unclear`, and use human annotation to determine whether the two new categories and broadened product label have adequate boundary reliability.

The taxonomy is **not yet ready to be locked**, but it is ready for a context-aware human-annotation validation phase. This audit does not create that set.

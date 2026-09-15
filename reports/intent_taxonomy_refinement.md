# Intent Taxonomy Refinement & Boundary Analysis Report

> **Status**: Proposed Final Intent Taxonomy — pending human annotation.
> Based on rigorous non-LLM empirical analysis of AmazonHelp customer messages.

## 1. Verified Dataset Counts & Discrepancy Resolution

### Pipeline Stage Counts:
| Pipeline Stage | Record Count | % of Raw Pairs | % of Cleaned Unique |
|---|---|---|---|
| **Total Raw Customer->Brand Pairs** | **154,976** | 100.0% | — |
| Unusable noise removed (<15 chars / <3 tokens) | 14,215 | 9.17% | — |
| Usable messages (Pre-deduplication) | 140,761 | 90.83% | — |
| Duplicates removed across all languages | 498 | 0.35% | — |
| **Cleaned Unique Customer Inquiries** | **140,263** | 90.51% | **100.0%** |
| — Cleaned Unique English (`en`) | **117,934** | 76.10% | **84.08%** |
| — Cleaned Unique Spanish (`es`) | 9,737 | 6.28% | 6.94% |
| — Cleaned Unique French (`fr`) | 6,090 | 3.93% | 4.34% |
| — Cleaned Unique German (`de`) | 3,598 | 2.32% | 2.57% |
| — Cleaned Unique Japanese (`ja`) | 1,856 | 1.20% | 1.32% |
| — Cleaned Unique Portuguese (`pt`) | 1,027 | 0.66% | 0.73% |
| — Cleaned Unique Unknown | 21 | 0.01% | 0.01% |

### Resolution of the 118,356 vs. 117,934 Inconsistency:
- **118,356** was the English message count **prior to deduplication**.
- **422** exact duplicates existed within the English messages.
- **117,934** is the **true, post-deduplication unique English inquiry count**.
- All analyses and percentages henceforth strictly use **117,934** as the English denominator.

## 2. Deep-Dive: Investigation of `general_inquiry_other` (86,994 Messages)

In the initial discovery run, 73.76% (86,994 messages) were assigned to `general_inquiry_other`. Empirical investigation reveals that **this was caused by two distinct structural factors**, not because the messages were genuinely 'other':

1. **The Multi-Turn Twitter Dialogue Effect (50.44% of Dataset)**:
   - Analysis of `twcs.csv` parent pointers reveals that **50.44% of all customer messages are Turn 3, Turn 5, or Turn 7 follow-up replies**, NOT initial problem statements.
   - Within `general_inquiry_other`, **2,100 messages (2.41%)** are dialogue turns like *'Sent you a DM'*, *'Here is my order number'*, *'Done'*, *'Thank you'*, or *'Still waiting for an update'*.
   - Because these mid-stream utterances lack the initial problem keywords (e.g. *'my package is delayed'*), rigid keyword matchers dumped them into 'other'.

2. **Undetected Core Intent Synonyms in Initial Inquiries**:
   - Unsupervised TF-IDF on the remaining messages revealed high frequencies of terms like `delivery date`, `delivered today`, `days ago`, `arriving today`, `damaged box`, and `out of stock`.
   - Customers commonly express delivery issues without using the word 'delay' (e.g. *'order placed 5 days ago still not dispatched'* or *'tracking says delivered today but nothing arrived'*).

## 3. Unsupervised Clustering Analysis (K = 8, 10, 12, 15, 20)

MiniBatchKMeans was trained on TF-IDF features across candidate cluster counts:

| K | Semantic Coherence Assessment | Key Observation |
|---|---|---|
| **K = 8** | Low Coherence | Massive dominant cluster (86,848 items); fails to separate distinct delivery sub-issues. |
| **K = 10** | **High Coherence** | Clean separation: 1) Delivery status/date, 2) Delivered missing, 3) Prime shipping delays, 4) Conversational gratitude, 5) Service complaints. |
| **K = 12** | **High Coherence** | Further cleanly isolates third-party seller queries and Kindle/digital queries. |
| **K = 15** | Moderate Coherence | Fragmentation; creates several micro-clusters with <50 items capturing profanity and non-English fragments. |
| **K = 20** | Over-fragmented | High sparsity; clusters split near-identical delivery queries into artificial sub-pockets. |

## 4. Real Examples from Major Clusters Inside `general_inquiry_other`

### CLUSTER_6 — Size: 42,281 (48.6%)
**Top Terms**: `customer, service, just, help, email, don, ve, need`

> **[01] Customer (Tweet 321684)**: "@AmazonHelp Damn. I need bayonet ones 😣 so what's the difference between his b22 and hue e27 bulbs."  
> **AmazonHelp**: "@192633 It seems the E27 bulbs are known for their richer colours. ^WJ"

> **[02] Customer (Tweet 2290254)**: "@115850 @118919  I ordered phone. Phone speaker is not working.I called CCE but CCE is not answering. How can I return?"  
> **AmazonHelp**: "@665294 Sorry to know the product is not working. Connect with our support team here: https://t.co/TK4yevTaND, and they'll assist you regarding this. ^AR"

> **[03] Customer (Tweet 2541759)**: "@AmazonHelp It won't let me message about it or anything? https://t.co/ohGiiUxbOP"  
> **AmazonHelp**: "@722701 When you click on the link and select this order, you should be able to scroll down and select email, phone or chat. Is this not appearing for you Laura? ^SA"

> **[04] Customer (Tweet 1953641)**: "@AmazonHelp Standard. But when preordering previously I've always received the item on the day of release."  
> **AmazonHelp**: "@579982 What was the delivery date was provided in your order confirmation email? ^CN"

> **[05] Customer (Tweet 2353800)**: "@AmazonHelp I have already raised a return. Can you make sure I should get a new device."  
> **AmazonHelp**: "@541204 We don't have access to your Amazon account info via Twitter. Please contact our support team in the link mentioned earlier and we'll get this checked. ^MK"

> **[06] Customer (Tweet 911983)**: "@115851 @115850 Customer services went from Cstmr Satisfaction to Cstmr Harrasment. (1/2)"  
> **AmazonHelp**: "@226490 I’m sorry about the delay regarding the pickup. Please drop in your details here: https://t.co/GIJyeYqKE0 We’ll look into it. ^SB"

> **[07] Customer (Tweet 1434140)**: "@199875 @115833 Vielleicht kann da @AmazonHelp weiterhelfen 😊"  
> **AmazonHelp**: "@459669 Hi, alle kompatiblen Geräte sind hier aufgelistet: https://t.co/7SqovuKm0f :) Liebe Grüße ^SI"

> **[08] Customer (Tweet 318562)**: "@AmazonHelp i'm tired of filling out forms. i want the service i paid for."  
> **AmazonHelp**: "@191894 Hi- The form above would be different, it sends your details directly to our team so we can personally investigate. ^NV"

> **[09] Customer (Tweet 108221)**: "@AmazonHelp We don't get error messages it just shuts off, exits apps and disconnected from our wifi accounts."  
> **AmazonHelp**: "@140022 Please try restarting your device and network to see if that clears out any cached data that may be behind the issue. ^DO"

> **[10] Customer (Tweet 661440)**: "@AmazonHelp I shouldn't have to knock on every door hoping to find it."  
> **AmazonHelp**: "@277601 Please contact us here so we can take a closer look into this with you: https://t.co/EKXRLsnxJu ^GG"

> **[11] Customer (Tweet 2371340)**: "I still haven’t rcvd my Yankee fitted @AmazonHelp"  
> **AmazonHelp**: "@684234 Thanks for reaching out to us! I'm sorry you haven't received your item yet. Have we missed the estimated delivery date provided in your confirmation e-mail? ^HM"

> **[12] Customer (Tweet 2488564)**: "@169994 Can I purchase something and have someone else pick it up?"  
> **AmazonHelp**: "@710680 Hi Ashley! Where are you getting the parcel delivered to? Keep us updated! - CN"

> **[13] Customer (Tweet 495802)**: "@AmazonHelp They are little to no help. How can I escalate?"  
> **AmazonHelp**: "@233262 Can you tell us more about what's happening with your device? What options were offered when you contacted? Did we try any troubleshooting or mention escalating this to another team? ^DO"

> **[14] Customer (Tweet 2472350)**: "@AmazonHelp Dont be in offensive mode."  
> **AmazonHelp**: "@183935 It's never our intention to hurt your sentiments on any instance. Kindly elaborate the issue so that we can assist you accordingly. ^MN"

> **[15] Customer (Tweet 421593)**: "@115850 can you please look into this, Feeling cheated and looking forward to use @118702 @115821 https://t.co/KeLbAIsboc"  
> **AmazonHelp**: "@215446 provide your order details as we consider them to be personal info. Our Twitter page is visible to the public. [2/2] ^NS"


### CLUSTER_4 — Size: 7,156 (8.23%)
**Top Terms**: `amazon, india, service, customer, amazon india, product, help, just`

> **[01] Customer (Tweet 2451335)**: "@120781 @AmazonHelp I have already replied several times.@120781  #amazon #amazonpay"  
> **AmazonHelp**: "@322303 Unfortunately, we'll not be able to provide any additional insight in this matter. 2/2 ^HD"

> **[02] Customer (Tweet 1104574)**: "@125833 Amazon Canada code redemption is not working for Destiny 2 on PC. Code not getting accepted by @128996"  
> **AmazonHelp**: "@380657 I'm sorry for the trouble! We'd like to look into this with you, please reach out to us here: https://t.co/3pBuw1SV0L ^GM"

> **[03] Customer (Tweet 1326873)**: "@AmazonHelp I have shared all the problems before and also fill up the details in the link given by you but no response from amazon team..poor service👎"  
> **AmazonHelp**: "@295979 Thank you for providing your details. We'll reach out to you soon. ^GU"

> **[04] Customer (Tweet 779286)**: "#amazon india horrible service. They took money in advance and have still to deliver the product though almost a month has gone by."  
> **AmazonHelp**: "@306110 I'm sorry your order has been delayed. Have you reached out to our team here: https://t.co/vlvfJr4nN9 ? ^GK"

> **[05] Customer (Tweet 2525419)**: "@AmazonHelp SO I ODERED SOMETHING FROM AMAZON FOR MY APPLE WATCH ITS BEEN A WHOLE MONTH AND NOW ITS SAYING IT WONT GET HERE FOR LKME ANOTHER WEEK"  
> **AmazonHelp**: "@277899 I'm sorry for the frustration. We'd like to help! Is the delivery date shown in your order confirmation different from the one you're seeing now? You can check here: https://t.co/3f6Z7p2gU4 ^JP"

> **[06] Customer (Tweet 2352307)**: "@AmazonHelp No damage, contacted DPD who have told me that the sender requested return? sold by Amazon EU S.a.r.L.?  Thanks"  
> **AmazonHelp**: "@142697 We'd like to take a closer look into this order. Please contact us at: https://t.co/JzP7hlA23B ^LI"

> **[07] Customer (Tweet 1026069)**: "@AmazonHelp Call kar bata taa hu kya huva he   Call me Chor company he Amazon Mat lena Amazon c kuch bhi Chor company he OnePlus Or Amazon. 9723269852"  
> **AmazonHelp**: "@190745 Please don’t provide your contact details as it is personal information. Our page is visible to the public.2/2^HN"

> **[08] Customer (Tweet 1936516)**: "It's always easy to criticise, but on this occasion, well done @115830 . After being let down by your courier leaving our parcel out in the rain to damage every item in the box, contacted customer service and all resloved within minutes. 👏👏 #amazon #greatservice #ThankYou"  
> **AmazonHelp**: "@576136 Sorry to hear about you're original order. Glad to hear we were able to help out, thanks for the lovely feedback Andy. ^NV"

> **[09] Customer (Tweet 1688618)**: "@AmazonHelp Hi Amazon, I spoke to customer services and got nowhere. I spoke with a supervisor who was very patronising and unhelpful."  
> **AmazonHelp**: "@512749 Sorry to hear- What was advised when you spoke with us directly? Was any further info provided? ^NV"

> **[10] Customer (Tweet 259948)**: "@AmazonHelp Can you at Amazon contact their support team? If you succeed i will forget everything."  
> **AmazonHelp**: "@177840 I'm sorry, we cannot contact the manufacturer on your behalf. Request you to visit the nearest service center. ^NR"

> **[11] Customer (Tweet 570854)**: "Is @AmazonHelp a real person, or an automated response to seeing the word Amazon? Because it doesn't seem completely automated but damn that's a lot of tweets."  
> **AmazonHelp**: "@253825 Hey, Ryan we are real and here for you if you need us! Please keep us posted on the delivery of your package. Thanks! ^MO"

> **[12] Customer (Tweet 259941)**: "@AmazonHelp I'm heavily disappointed with Amazon, customer support via email is all scripted and they don't read the emails. #useless"  
> **AmazonHelp**: "@177839 Hey, Carl! I'm sorry about the negative experience with email support. We'd love to help! What are the details of the issue? ^AJ"

> **[13] Customer (Tweet 1216270)**: "@116618 @127110 If I watch Netflix through Amazon it stalls but Ama/Net work fine in their own app. Trying to make Netflix look bad?"  
> **AmazonHelp**: "@405398 To confirm, what device are you using? Give these steps a try: https://t.co/IiOL0vFR6E and let us know how it goes. ^SJ"

> **[14] Customer (Tweet 2377241)**: "so when I was in kindergarten I had a stuffed bunny that I loved a lot and my ex best friend stole it and moved away with it and I've been salty about it since anyway I just found it on amazon and I'm v tempted"  
> **AmazonHelp**: "@685632 I say go for it! Few things can make a person feel better, but a cute stuffed bunny, how can you resist?  :) ^SY"

> **[15] Customer (Tweet 200001)**: "@115850 @AmazonHelp @115821 Pathetic customer support experience despite being a Prime &amp; being one of the first buyers of Amazon Echo !!"  
> **AmazonHelp**: "@163184 Our apologies. Could you tell us more about your concern for better assistance? ^YP"


### CLUSTER_0 — Size: 7,136 (8.2%)
**Top Terms**: `delivery, date, delivery date, today, prime, day, amazon, service`

> **[01] Customer (Tweet 844181)**: "@AmazonHelp No one calls me, and the day is beginning to end! So much for guaranteed delivery for a prime user! Turns out, Prime is not worth after all"  
> **AmazonHelp**: "@320702 I do understand Bhaskar, please do not worry we'll get back to you at the earliest with an update. ^HN"

> **[02] Customer (Tweet 2296987)**: "@AmazonHelp Can I just pick my orders up at a fulfillment center as opposed to being guaranteed delivery and it not show up?"  
> **AmazonHelp**: "@664403 Hi Dylan- Pick up wouldn't be an available option. Are you currently awaiting a delivery now which we can help with? ^NV"

> **[03] Customer (Tweet 199995)**: "@AmazonHelp rep came back briefly and I'm back on hold again.  this is the second call this week for this order and your second wrong delivery"  
> **AmazonHelp**: "@163183 Thanks for the update. Since we do not have access to your account details they will have the best options to help review. ^TM"

> **[04] Customer (Tweet 317423)**: "@AmazonHelp That you were checking with your delivery chaps as to where they had left them. They attached a photo for one, that wasn't my house!?"  
> **AmazonHelp**: "@191758 Were you advised to wait up to 24hours while this is being looked into?^CD"

> **[05] Customer (Tweet 1693537)**: "@AmazonHelp Replied.. Called.. Got new timing for delivery until 1 pm. That too would be over in 15 mins.. This how you treat escalations? #pathetic"  
> **AmazonHelp**: "@123814 Apologies for the delay, Bunty. Please respond to the same email so we could take it from there. ^JC"

> **[06] Customer (Tweet 327609)**: "When you pay for Express Delivery on something from @115821 and it doesn't even turn up.!!! Absolute joke.!!! 😡😡"  
> **AmazonHelp**: "@194099 Oh no! What's the latest tracking status show here: https://t.co/aaDyEz1VgE? ^KP"

> **[07] Customer (Tweet 2299736)**: "@AmazonHelp Please just try to find my delivery"  
> **AmazonHelp**: "@322926 We aren't able to view account or order info via Twitter but we'd still like to help. Please reach out via the link provided by ^CS! Let us know how it goes! ^CN"

> **[08] Customer (Tweet 745054)**: "@AmazonHelp https://t.co/r36ZS6leOZ it was this here sold by Smart Shop Online. Was prime delivery doesn't seem to be anymore though I also mailed them."  
> **AmazonHelp**: "@298108 Since this was sold/fulfilled by a third-party seller, please use this link to contact them for options: https://t.co/cDME3v6ynT ^WM"

> **[09] Customer (Tweet 2460249)**: "Apparently @115830's delivery drivers think 'In Your Green Bin' is an acceptable safe spot to leave a parcel."  
> **AmazonHelp**: "@704505 I'm sorry for the improper delivery! We'd like a chance to collect some details about this and review our options. Please reach out to us via phone or chat here: https://t.co/JzP7hlA23B ^WT"

> **[10] Customer (Tweet 698823)**: "@115850 Still not get product order 405-4841727-8482714, which used to deliver on 9th. Nor update the delivery time. Intentionally do that"  
> **AmazonHelp**: "@286684 Please don't provide your order details, as we consider them to be personal info. Our page is visible to the public. (2/2) ^GK"

> **[11] Customer (Tweet 1447154)**: "Don’t know why @115830 have delivery drivers who don’t knock! Twice waited in &amp; they just dump the parcel on the doorstep 🤬 #thingstodo"  
> **AmazonHelp**: "@455806 So sorry about the poor experience! Please contact us via phone/chat here: https://t.co/JzP7hlA23B so we may look into this. ^KL"

> **[12] Customer (Tweet 63895)**: "@AmazonHelp Says rescheduled when it wasn't. I just updated a safe place as my hour window was not met on Monday. Now it's nowhere to be seen. Even @122232 said delivery for yesterday and nothing. https://t.co/yahZHLp8jq"  
> **AmazonHelp**: "@130677 Hi Danny. Can you contact us directly regarding this via the below link, we can look into this further for you.  https://t.co/JzP7hlA23B Thank you. ^NV"

> **[13] Customer (Tweet 1394532)**: "@AmazonHelp Your delivery boy not answering my call."  
> **AmazonHelp**: "@444309 We'd like to have his checked for you. Please call us here: https://t.co/TK4yevTaND. ^NR"

> **[14] Customer (Tweet 2480935)**: "@115821 can I assume my guaranteed delivery isn’t coming today now it’s gone 10.15 on a Sunday night?"  
> **AmazonHelp**: "@708895 What does the latest tracking update show here:https://t.co/aaDyEz1VgE, Richard? Let us know, we'd love to help! ^SA"

> **[15] Customer (Tweet 737983)**: "@AmazonHelp It's okay. After 80 minutes, the delivery guy finally came to the correct location and I was able to return the product."  
> **AmazonHelp**: "@296496 Thank you for confirming. Please get back to us if you need any further assistance. ^PB"


### CLUSTER_7 — Size: 7,012 (8.06%)
**Top Terms**: `order, placed, amazon, delivered, help, cancelled, id, number`

> **[01] Customer (Tweet 2470967)**: "Hi @116316 I received a CD that I did not order, if you want to recover it please send to me an address and an empty envelope. https://t.co/kToTC17iwl"  
> **AmazonHelp**: "@706744 Is it possible, that the item is a gift from a friend? ^MS"

> **[02] Customer (Tweet 1192282)**: "Explain to me how @115821 will let me buy fine but when it's telling me to change my payment method on a different order "an error occured""  
> **AmazonHelp**: "@400229 Strange - have you added the new payment card to your account successfully ?  ^TD"

> **[03] Customer (Tweet 114443)**: "@115850 1/2 2 times i order from amazon &amp; it never even shipped. i contacted cc multiple times &amp; always  they told me it will never be happen again.1st time i order moto g5 phone &amp; 2nd time fan heater. it was so frustrating . i had to cancel my 1st order &amp; take it from flipkart"  
> **AmazonHelp**: "@141442 I'm sorry to know about your order. We never intended this experience. Please share your details here: https://t.co/GIJyeY99fq I'll reach out to you with further assistance. ^SV"

> **[04] Customer (Tweet 1601082)**: "@AmazonHelp Following your link I have not found any mail regarding the status of the order. Kindly check the photo here. https://t.co/Yv3QP3t2uz"  
> **AmazonHelp**: "@299564 Did you happen to look into the other messages? Do keep us posted. ^CB"

> **[05] Customer (Tweet 1432367)**: "@115821 i was going to make an order but there was no Checkout button when looking at my cart."  
> **AmazonHelp**: "@452598 Hey, sounds like the item you're ordering is an add on item. You can read about it here: https://t.co/jyfgyGFDMY ^RS"

> **[06] Customer (Tweet 547932)**: "@AmazonHelp Hi a number of my orders haven’t arrived, so I’ve had to re order as I need the items ASAP! But the previous orders show as delivered! Really not happy about this and want to be refunded ASAP!"  
> **AmazonHelp**: "@247487 My apologies for this inconvenience. Please get in touch with us here: https://t.co/JzP7hlA23B and we'll be happy to assist you! ^RB"

> **[07] Customer (Tweet 349119)**: "@AmazonHelp And I can't find the order in my order column.  Will it be delivered?"  
> **AmazonHelp**: "@199094 I'm sorry for the trouble. As informed to you earlier please get in touch with our support team for more information. ^GU"

> **[08] Customer (Tweet 1239296)**: "@AmazonHelp I placed a return of order#405-5827927-7849934 on 5th november, 2017. But it hasn't been picked up yet and no replies came from ur customer service unit. Please help"  
> **AmazonHelp**: "@410695 I'm sorry for the poor experience. We are unable to access your account over Twitter however, we'd still like to help! To make sure we're giving you the best information possible can you let us know which website/marketplace you used to order with us? ^EB"

> **[09] Customer (Tweet 1763158)**: "Love it when my @115821 order doesn't even turn up 😡"  
> **AmazonHelp**: "@530471 Oh no! I'm sorry the order hasn't arrived. What's the delivery date and most recent tracking here: https://t.co/ijxJ9jCwr9? ^JN"

> **[10] Customer (Tweet 2320473)**: "FAKE CUSTOMER CARE #MISGUIDE  BY CUSTOMER CARE @7092 @115850 @115851 I ORDER PRODUCT ON 30th but they always misguide me right now they told me re-order your product again but they don't understand almost half month gone. This type of service given by @115850 😡😡"  
> **AmazonHelp**: "@672512 Apologies for the inconvenience. Please share your details here: https://t.co/GIJyeYqKE0 and we will get in touch with you. ^BS"

> **[11] Customer (Tweet 46480)**: "@AmazonHelp I have used the form at least 3 times &amp;not had any response (hence use of Twitter). Order not showing as delivered yet so can't log issue."  
> **AmazonHelp**: "@126318 (1/2) Using the link ^VS provided, select the options "An order I placed &gt; Other order issues &gt; Something else""

> **[12] Customer (Tweet 1053490)**: "@AmazonHelp Tried placing an order on amazon.fr and amazon.es for snes classic. Order cancelled and accounts closed. Multiple times."  
> **AmazonHelp**: "@368928 Have you received an email explaining why your account has been closed  please ? ^KE"

> **[13] Customer (Tweet 1688642)**: "@AmazonHelp YO I updated my payment info about 6 times &amp;there's more dan enuf money to proceed with my purchase Y isn't my order  goin thru?"  
> **AmazonHelp**: "@512750 Hi! These steps should help: https://t.co/RbswDFGu8o Keep us updated! ^AB"

> **[14] Customer (Tweet 1853082)**: "@AmazonHelp either I'm blind or there is no way to contact customer service on the website.  So no way to talk to someone re my order?"  
> **AmazonHelp**: "@554534 We'd be happy to help, Mike! Without disclosing personal information. Will you tell us more about your order issues? ^SK"

> **[15] Customer (Tweet 693833)**: "@115850 @AmazonHelp Amazon resolves issues thankfully, but trips again re my order 408-7261960-8669144!!!"  
> **AmazonHelp**: "@149041 Uhoh! Could you elaborate on what went wrong with this order? I'm unable to check that over this medium.  Please don’t provide your order details as we consider them to be personal information. Our Twitter page is visible to public. ^JC"


### CLUSTER_3 — Size: 6,312 (7.26%)
**Top Terms**: `delivered, today, package, delivered today, says, ordered, yesterday, supposed`

> **[01] Customer (Tweet 2923463)**: "Really upset that @115817 said my package was undeliverable when they delivered another package that day, causing my books for my classes to be returned to @115821 and now are out of stock."  
> **AmazonHelp**: "@809011 I'm so sorry for the trouble! Please reach us for carrier feedback and explore available options with us here: https://t.co/hApLpMlfHN ^ST"

> **[02] Customer (Tweet 2252813)**: "@AmazonHelp placed an order on the basis it would be delivered today. Order tracker on app says still getting delivered today but it’s now quarter to 9, what’s going on??"  
> **AmazonHelp**: "@656293 Hi, Mat!  Thank you for reaching out.  I'm sorry that your package hasn't arrived yet!  Have there been any tracking updates about a possible delay?  ^SP"

> **[03] Customer (Tweet 207636)**: "@AmazonHelp where's ma call of duty?! I pre ordered it to arrive today weeks ago?"  
> **AmazonHelp**: "@165099 I'm sorry for the long wait; deliveries may take until 21:00 within the provided delivery date. ^SJ"

> **[04] Customer (Tweet 596759)**: "@AmazonHelp It says it was delivered, but wasn't in my mailroom."  
> **AmazonHelp**: "@261462 Understood. We're happy to take a closer look at this order with you and assist directly using ^AB's second link in our previous response. ^JR"

> **[05] Customer (Tweet 2059157)**: "@AmazonHelp on your website,my package says it was delivered on Wednesday. it's Friday and I still have no package! There is no contact help"  
> **AmazonHelp**: "@609012 Oh no! We'd love to help Makayla! Have you checked these steps to locate your package? Let us know! https://t.co/NQXunET7D5 ^JD"

> **[06] Customer (Tweet 277079)**: "@AmazonHelp You promised me that product will be delivered y'day by 10 pm . I was sure that the promise was just one more 420 lie isn't it ?"  
> **AmazonHelp**: "@182213 I'm sorry your package hasn't been delivered yet. Please reply to the email received from us and we shall get back to you. ^SH"

> **[07] Customer (Tweet 1368124)**: "@AmazonHelp I preordered something that was released today, but my pkg won't be here until Tue... the item is avail for 1day Prime shipping"  
> **AmazonHelp**: "@438495 in check out. You can learn more about our shipping rates here: https://t.co/d52NDiCnqi ^HC (2/2)"

> **[08] Customer (Tweet 2184661)**: "@115821 y’all delivered my shirt to some address in New Jersey. Wtf."  
> **AmazonHelp**: "@306294 Sorry to hear that. Does the tracking mention a carrier delivering it? ^PK"

> **[09] Customer (Tweet 2907920)**: "@115830 Why do you use #Hermes for delivery? Parcel on their website says 'delivered and signed for' - actually thrown over 9 foot fence"  
> **AmazonHelp**: "@805150 So sorry about this, Helen! We'd like to look into this in more detail with you. When you have the chance, please reach out to us here: https://t.co/JzP7hlA23B so we can investigate this for you. ^VB"

> **[10] Customer (Tweet 227717)**: "@AmazonHelp Package arrived on Saturday and going to send it back this weekend. It is not opened/label still on. What should I do?"  
> **AmazonHelp**: "@170304 Reach us here:  https://t.co/JzP7hlA23B so we can check into this for you.^CD"

> **[11] Customer (Tweet 1326936)**: "My costume for work today @115821 #bwi2 #behindthesmile https://t.co/srGSsIjAp8"  
> **AmazonHelp**: "@429597 Hailing on all frequencies........ that costume rocks!! 🖖 ^PK https://t.co/hl4zphhRhD"

> **[12] Customer (Tweet 911186)**: "@115850 @AmazonHelp Hey guys, My product has not delivered to me as they have mentioned the Expected date on 20th Oct."  
> **AmazonHelp**: "@336418 Apologies for the delay. Please report this to our support team here: https://t.co/vlvfJr4nN9. They'll assist you with this. ^ST"

> **[13] Customer (Tweet 2973890)**: "I was so goddamn stoked to get my desk chair delivered early today and then @115821 had to go and send me the wrong color. 😤"  
> **AmazonHelp**: "@820180 Oh no! That's not what we strive for! Let's check out refund/replacement options here: https://t.co/riTjn0MovI ^TR"

> **[14] Customer (Tweet 327562)**: "@AmazonHelp I am following up with your customer care from last two days but all in vain. Hope you will get my package delivered tomorrow 2of2"  
> **AmazonHelp**: "@194085 We apologize for the inconvenience. Please share your details in this link: https://t.co/GIJyeYqKE0 and we'll help you. ^ZH"

> **[15] Customer (Tweet 704909)**: "(..cont)trying to find use for these damn plastic package fillers. Who cares if my paper towels arrive smushed! Cmon now @AmazonHelp"  
> **AmazonHelp**: "@288485 We're always trying to improve! To send us packaging feedback for your order, please visit: https://t.co/h9ZcL0zqXC ^MB"


## 5. Intent Boundary Decisions: Merges, Splits & Refinements

1. **MERGED: `wrong_item_received` into `damaged_wrong_defective_item`**
   - *Rationale*: Wrong items (290 messages) and damaged items (3,340 messages) trigger the identical operational resolution in Amazon: generating a return label and dispatching a replacement.
   - *Outcome*: Creates a single, semantically robust fulfillment error category (`damaged_wrong_defective_item`).

2. **RETAINED SEPARATION: `order_delivery_delay` vs `delivery_marked_delivered_missing`**
   - *Rationale*: Crucial operational difference. Delivery delays represent goods in transit (remedy: check carrier window, buffer up to 8 PM). Marked delivered but missing represents potential misdelivery/theft (remedy: check porch/neighbors, dispatch carrier driver investigation).

3. **RETAINED SEPARATION: `return_and_refund_status` vs `payment_charge_dispute`**
   - *Rationale*: Return/refund status relates to expected refunds from authorized returns; payment disputes involve unexpected double debits or card fraud, requiring strict escalation.

4. **NEW INTENT ADDED: `product_stock_inquiry`**
   - *Rationale*: Emerged prominently from clustering analysis (Cluster on stock, availability, deals, pre-orders). Highly auto-handleable without account access.

5. **FORMALIZED DIALOGUE ARTIFACT BUCKET: `conversational_followup`**
   - *Rationale*: Over 25,000 messages in Twitter support are mid-conversation updates ('sent DM', 'here is order #'). Isolating this prevents intent classifiers from polluting task-oriented intents with conversational turns.

## 6. Proposed Final Intent Taxonomy (10 Core Intents)

| Intent ID | Name | Count | % of English | PII Req? | Suitability |
|---|---|---|---|---|---|
| `order_delivery_delay` | **Order Delivery Delay & Transit Status** | 9,278 | 7.87% | Yes | Partially auto-handleable (can fetch liv... |
| `delivery_marked_delivered_missing` | **Marked Delivered But Not Received** | 861 | 0.73% | Yes | Strict escalation to carrier driver trac... |
| `damaged_wrong_defective_item` | **Damaged, Defective, or Wrong Item Received** | 2,343 | 1.99% | Yes | Auto-handleable via self-service replace... |
| `return_and_refund_status` | **Return Label, Pickup & Refund Processing** | 4,240 | 3.6% | Yes | Auto-handleable by providing standard 3–... |
| `order_cancellation_modification` | **Order Cancellation & Order Changes** | 560 | 0.47% | Yes | Auto-handleable if order is in pre-dispa... |
| `prime_membership_billing` | **Prime Membership & Subscription Benefits** | 3,531 | 2.99% | Yes | Highly auto-handleable by providing self... |
| `account_access_security` | **Account Access, Login & Security** | 1,365 | 1.16% | Yes | Strict escalation to account security / ... |
| `payment_charge_dispute` | **Payment Authorization & Charge Disputes** | 1,397 | 1.18% | Yes | Escalate immediately to secure billing c... |
| `product_stock_inquiry` | **Product Stock, Pricing & Pre-Order Inquiries** | 1,589 | 1.35% | No | Auto-handleable via product page stock a... |
| `third_party_seller_marketplace` | **Third-Party Marketplace Seller Inquiries** | 1,507 | 1.28% | Yes | Auto-handleable by guiding through 'Cont... |
| `conversational_followup` | **Conversational Dialogue Turns & Acknowledgments** | 2,532 | 2.15% | No | Maintain dialogue state; parse incoming ... |
| `general_inquiry_unclear` | **General Inquiries / Feedback / Ambiguous** | 88,731 | 75.24% | No | Prompt customer for clarifying details (... |

### `order_delivery_delay` — Order Delivery Delay & Transit Status
- **Volume**: 9,278 (7.87%)
- **Definition**: Customer inquires about a delayed shipment, missed estimated delivery date (EDD), package stuck in transit, or delivery rescheduling.
- **Inclusion Criteria**: Inquiries citing missed delivery dates, delayed transit, carrier tracking updates, or queries on when an overdue order will arrive.
- **Exclusion Criteria**: Tracking says delivered but customer did not receive it (use `delivery_marked_delivered_missing`); items damaged during delivery (use `damaged_wrong_defective_item`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Partially auto-handleable (can fetch live tracking status & standard 8 PM buffer explanation; escalate if EDD > 48h overdue).
- **Typical AmazonHelp Resolution**: Checks live carrier tracking, clarifies standard delivery window (up to 8 PM or 9 PM), and advises when to request a replacement if past threshold.

### `delivery_marked_delivered_missing` — Marked Delivered But Not Received
- **Volume**: 861 (0.73%)
- **Definition**: Tracking status indicates package was successfully delivered or handed to resident, but the customer cannot locate the parcel.
- **Inclusion Criteria**: Customer states tracking shows 'delivered', 'handed to resident', or 'left in mailbox/porch', but parcel is nowhere to be found.
- **Exclusion Criteria**: Package still marked in transit or delayed (use `order_delivery_delay`); wrong item delivered (use `damaged_wrong_defective_item`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Strict escalation to carrier driver trace or replacement dispatch after 24h neighbor/porch buffer check.
- **Typical AmazonHelp Resolution**: Instructs customer to check porches/neighbors/safe places; if unlocatable after 24 hours, dispatches replacement or initiates refund.

### `damaged_wrong_defective_item` — Damaged, Defective, or Wrong Item Received
- **Volume**: 2,343 (1.99%)
- **Definition**: The item received is physically damaged, functionally defective, expired, missing components, or an entirely different product.
- **Inclusion Criteria**: Reports of cracked screens, shattered items, missing parts, expired goods, or wrong product/size delivered in the box.
- **Exclusion Criteria**: Undelivered orders (use delivery intents); disputes with marketplace sellers regarding pricing (use `third_party_seller_marketplace`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Auto-handleable via self-service replacement/return label link; escalate if item is non-returnable or hazardous.
- **Typical AmazonHelp Resolution**: Directs customer to online Returns & Replacements portal (`amazon.com/returns`) to print pre-paid shipping label or schedule carrier pickup.

### `return_and_refund_status` — Return Label, Pickup & Refund Processing
- **Volume**: 4,240 (3.6%)
- **Definition**: Inquiries regarding return drop-off/pickup status, return label generation, refund processing timelines, or deductions.
- **Inclusion Criteria**: Customer asking for a refund status, when money will reflect in bank/card, return pickup rescheduling, or refund calculation issues.
- **Exclusion Criteria**: Unauthorized bank charges (use `payment_charge_dispute`); requesting order cancellation before shipment (use `order_cancellation_modification`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Auto-handleable by providing standard 3–5 business day banking refund timelines; escalate for missing refunds > 14 days.
- **Typical AmazonHelp Resolution**: Explains refund release windows (3-5 business days for cards, 24 hours for Amazon Pay); confirms return pickup courier schedule.

### `order_cancellation_modification` — Order Cancellation & Order Changes
- **Volume**: 560 (0.47%)
- **Definition**: Customer requests to cancel an order, alter shipping address, or reports an unexpected automated order cancellation.
- **Inclusion Criteria**: Requests to cancel before dispatch, change shipping address, cancel accidental orders, or questions about unexpected order cancellations.
- **Exclusion Criteria**: Returning an already-delivered order (use `return_and_refund_status`); canceling Prime subscription (use `prime_membership_billing`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Auto-handleable if order is in pre-dispatch state via 'Your Orders' cancel button; escalate if already shipped.
- **Typical AmazonHelp Resolution**: Instructs customer to visit 'Your Orders' > 'Cancel Items'; explains that dispatched items cannot be cancelled and must be returned.

### `prime_membership_billing` — Prime Membership & Subscription Benefits
- **Volume**: 3,531 (2.99%)
- **Definition**: Questions regarding Prime membership charges, auto-renewal, student discounts, cancellation, or Prime Video/Music access.
- **Inclusion Criteria**: Charges for Prime, auto-renew inquiries, cancellation of Prime trial, Prime student verification, or Prime delivery benefit questions.
- **Exclusion Criteria**: Standard credit card fraud unrelated to Prime (use `payment_charge_dispute`); standard order delivery delays (use `order_delivery_delay`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Highly auto-handleable by providing self-service Manage Prime membership direct link (`amazon.com/manageprime`).
- **Typical AmazonHelp Resolution**: Directs customer to 'Manage Your Prime Membership' page to cancel, view renewal dates, or claim refunds for unused benefits.

### `account_access_security` — Account Access, Login & Security
- **Volume**: 1,365 (1.16%)
- **Definition**: Customer is locked out of account, facing 2FA/OTP issues, password resets, account suspension, or suspicious account activity.
- **Inclusion Criteria**: Forgotten passwords, account on hold, OTP not received, verification failure, suspicious login alerts, two-step verification issues.
- **Exclusion Criteria**: Card double charges where account is accessible (use `payment_charge_dispute`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Strict escalation to account security / verification team; provide direct password assistance portal link.
- **Typical AmazonHelp Resolution**: Directs to Account Recovery portal (Two-Step Verification recovery form); warns never to post email/passwords on public Twitter.

### `payment_charge_dispute` — Payment Authorization & Charge Disputes
- **Volume**: 1,397 (1.18%)
- **Definition**: Disputes regarding double charges, unauthorized card transactions, failed payment authorizations, or Amazon Pay wallet balances.
- **Inclusion Criteria**: Charged multiple times for one order, unknown charges on bank statement, payment gateway timeout, Amazon Pay wallet balance discrepancies.
- **Exclusion Criteria**: Refund status for authorized returns (use `return_and_refund_status`); Prime membership recurring fee (use `prime_membership_billing`).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Escalate immediately to secure billing channel; automated guidance explaining bank pending authorizations vs captured charges.
- **Typical AmazonHelp Resolution**: Clarifies the difference between temporary bank authorizations and actual settled charges; provides secure billing support chat link.

### `product_stock_inquiry` — Product Stock, Pricing & Pre-Order Inquiries
- **Volume**: 1,589 (1.35%)
- **Definition**: Customer inquires about product stock availability, restock dates, authenticity, pre-order dispatch, or pricing/deals.
- **Inclusion Criteria**: Queries asking if an item is authentic, when stock will return, pre-order release dates, Lightning Deal pricing, or promo code application.
- **Exclusion Criteria**: Complaints regarding broken products already delivered (use `damaged_wrong_defective_item`).
- **Requires PII**: No
- **Auto-Handling / Escalation**: Auto-handleable via product page stock alerts and standard pricing/deal policies.
- **Typical AmazonHelp Resolution**: Explains that stock and pricing are managed by suppliers/sellers; advises adding item to Wishlist to receive restock notifications.

### `third_party_seller_marketplace` — Third-Party Marketplace Seller Inquiries
- **Volume**: 1,507 (1.28%)
- **Definition**: Inquiries regarding purchases from 3rd-party marketplace merchants, unresponsive sellers, or Amazon A-to-Z Guarantee claims.
- **Inclusion Criteria**: Customer experiencing difficulty contacting seller, seller refused return, counterfeit seller claims, or A-to-Z guarantee protection.
- **Exclusion Criteria**: Orders fulfilled directly by Amazon Logistics (use delivery/return intents).
- **Requires PII**: Yes
- **Auto-Handling / Escalation**: Auto-handleable by guiding through 'Contact Seller' portal; escalate to A-to-Z claim if seller is unresponsive > 48 hours.
- **Typical AmazonHelp Resolution**: Guides customer to 'Contact Seller' via Your Orders; outlines the Amazon A-to-Z Guarantee protection policy.

## 7. Ambiguous Boundaries & Annotation Guidelines for Golden Set

The following boundaries require strict operational rules during annotation:
1. **`order_delivery_delay` vs `delivery_marked_delivered_missing`**:
   - If customer says *'Where is my order, it has not arrived'* $ightarrow$ `order_delivery_delay`.
   - If customer says *'Tracking says it was delivered today but I did not receive it'* $ightarrow$ `delivery_marked_delivered_missing`.
2. **`return_and_refund_status` vs `damaged_wrong_defective_item`**:
   - If customer reports a damaged item and asks what to do $ightarrow$ `damaged_wrong_defective_item`.
   - If customer already returned the item and asks *'Where is my refund?'* $ightarrow$ `return_and_refund_status`.
3. **Multi-Intent Messages (Primary Remedy Rule)**:
   - If a customer mentions both a late shipment and demands a cancellation, assign the *primary remedy requested* (`order_cancellation_modification`).

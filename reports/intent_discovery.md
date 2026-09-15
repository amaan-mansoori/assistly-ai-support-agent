# Empirical Intent Discovery Report — AmazonHelp

> **Status**: Exploratory candidate issue areas discovered from empirical customer messages.
> These are **candidate issue areas**, NOT final locked intents.

## 1. Dataset Cleaning & Conversation Reconstruction
| Step | Record Count | Percentage |
|---|---|---|
| Raw AmazonHelp conversation pairs | 154,976 | 100.0% |
| Unusable noise filtered (<15 chars / non-substantive) | 14,215 | 9.17% |
| Duplicates filtered (normalized customer text) | 498 | 0.35% |
| **Cleaned unique customer messages** | **140,263** | **100.0%** |

## 2. Language Distribution
Language identified locally via functional vocabulary profiles and CJK unicode ranges:

| Language | Count | Percentage |
|---|---|---|
| `en` | 118,356 | 84.08% |
| `es` | 9,787 | 6.95% |
| `fr` | 6,108 | 4.34% |
| `de` | 3,601 | 2.56% |
| `ja` | 1,856 | 1.32% |
| `pt` | 1,032 | 0.73% |
| `unknown` | 21 | 0.01% |

**Cleaned English customer inquiries retained for modeling**: **117,934** (84.1%).

## 3. Discovered Candidate Issue Areas

| Candidate Issue Area | Count | Pct of English | Requires PII / Account Data? | Typical Resolution Action |
|---|---|---|---|---|
| **Delivery Delay & Late Shipment** (`delivery_delay`) | 7,527 | 6.38% | Yes | `tracking_delivery_guidance` |
| **Tracking Shows Delivered But Not Received** (`marked_delivered_not_received`) | 1,309 | 1.11% | Yes | `direct_troubleshooting` |
| **Prime Membership & Subscription** (`prime_benefits_membership`) | 3,714 | 3.15% | Yes | `direct_troubleshooting` |
| **Order Cancellation & Address Change** (`order_cancellation_modification`) | 547 | 0.46% | Yes | `direct_troubleshooting` |
| **Returns, Replacements & Damaged Items** (`return_replacement_damaged`) | 3,340 | 2.83% | Yes | `direct_troubleshooting` |
| **Refund Inquiries & Discrepancies** (`refund_status_missing`) | 3,802 | 3.22% | Yes | `direct_troubleshooting` |
| **Payment, Billing & Digital Wallet** (`payment_and_billing`) | 1,398 | 1.19% | Yes | `direct_troubleshooting` |
| **Account Access & Security** (`account_access_security`) | 1,331 | 1.13% | Yes | `direct_troubleshooting` |
| **Wrong Item or Incomplete Shipment** (`wrong_item_received`) | 290 | 0.25% | Yes | `direct_troubleshooting` |
| **Gift Cards, Coupons & Promotional Discounts** (`gift_card_promotions`) | 917 | 0.78% | No | `direct_troubleshooting` |
| **Third-Party Marketplace Seller Disputes** (`third_party_seller_issues`) | 1,368 | 1.16% | Yes | `direct_troubleshooting` |
| **Packaging & Delivery Driver Feedback** (`packaging_and_carrier_feedback`) | 3,087 | 2.62% | No | `direct_troubleshooting` |
| **Digital Devices & Subscriptions (Kindle, Echo, Audible)** (`digital_kindle_audible`) | 2,310 | 1.96% | No | `direct_troubleshooting` |
| **General Inquiry / Ambiguous / Other** (`general_inquiry_other`) | 86,994 | 73.76% | No | `mixed` |

## 4. Deep-Dive: Representative Real Examples & Resolution Patterns

### Delivery Delay & Late Shipment (`delivery_delay`)
- **Volume**: 7,527 messages (6.38%)
- **Description**: Customer order has not arrived by estimated delivery date or is experiencing transit delays.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'tracking_delivery_guidance': 3087, 'direct_troubleshooting': 2587, 'contact_channel_redirect': 926}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 2393496)**: "My order was cancelled for being "unauthorised" 3 times by @115830 then I got my sister to order it and now it's delayed with no info!"  
> **AmazonHelp**: "@689145 Hi Jana, sorry to hear this. Has your sister checked the status of the order? She can do this by clicking the link :  https://t.co/aaDyEz1VgE ^BZ"  
> *Response Action*: `direct_troubleshooting`

> **[2] Customer (Tweet 474279)**: "Pay for @115830 Prime and you’ll get next day delivery... one week on and I’m still waiting... 🤔"  
> **AmazonHelp**: "@227887 Hi, I am sorry to hear of about your delay. Did we contact you with an explanation? ^HS"  
> *Response Action*: `clarification_question`

> **[3] Customer (Tweet 1004644)**: "Impressive service from @115830 as always - didn’t even ask for next day delivery &amp; got it anyway. Great customer service 🙏🏻🙏🏻🙏🏻"  
> **AmazonHelp**: "@357788 When you're happy, so are we! ^GP"  
> *Response Action*: `direct_troubleshooting`


### Tracking Shows Delivered But Not Received (`marked_delivered_not_received`)
- **Volume**: 1,309 messages (1.11%)
- **Description**: Tracking status indicates package was delivered, but customer cannot locate it.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 619, 'tracking_delivery_guidance': 298, 'contact_channel_redirect': 189}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 2663994)**: "@115821 Whenever the shipping carrier is you I don't get my package correctly... How do I resolve? Still haven't received my package that was "delivered" yesterday."  
> **AmazonHelp**: "@750668 I'm sorry about this. We want to be sure you are receiving your parcels when they are expected. Please reach out to us directly here so that we can take a look into this for you: https://t.co/hApLpMlfHN We'd like to help! ^ZW"  
> *Response Action*: `contact_channel_redirect`

> **[2] Customer (Tweet 2465371)**: "@AmazonHelp : I was guaranteed cashback of Rs 500 when I bought from Amazon. Till now I haven't received cash back. pathetic service"  
> **AmazonHelp**: "@293938 Apologies for the trouble with cash back. Could you please help us with the offer page link/name. We'd like to check it. ^HD"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 2300807)**: "@115821 this is the second time I’ve ordered something for same day shipping and it be marked as delivered but not actually being delivered to my amazon pickup point your amazon logistics drivers are finessing you"  
> **AmazonHelp**: "@527796 This isn't at all the delivery experience we strive to provide! Please, when able, provide us details so that a specialist can personally investigate: https://t.co/N2udW3dbY7 ^JE"  
> *Response Action*: `tracking_delivery_guidance`


### Prime Membership & Subscription (`prime_benefits_membership`)
- **Volume**: 3,714 messages (3.15%)
- **Description**: Inquiries regarding Prime subscription fees, auto-renewal, free trial cancellation, or broken 2-day delivery benefits.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 1454, 'tracking_delivery_guidance': 819, 'prime_account_guidance': 517}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 2555102)**: "@AmazonHelp Two day shipping. I'm a prime member. I have order numbers if it helps"  
> **AmazonHelp**: "@725575 Thanks for confirming! We'd like to take a closer look at the orders with you. When you have a moment, please reach out to us here: https://t.co/hApLpMlfHN ^RA"  
> *Response Action*: `contact_channel_redirect`

> **[2] Customer (Tweet 555360)**: "@AmazonHelp Yep, been in touch with Amazon Customer Services, initially told delivery couldn’t be made due to inaccessible roads 😂😂😂, due to parties/ parades which is simply not true. Then told to wait until 05 December which leaves me wondering why am I paying for Prime membership? 🤔"  
> **AmazonHelp**: "@249664 I understand your frustration! We do try out best to meet our delivery date. Please let us know if you don't receive your package by the 5th at 21:00. ^LS"  
> *Response Action*: `tracking_delivery_guidance`

> **[3] Customer (Tweet 269458)**: "@AmazonHelp This is the receipt from our Amazon prime account so I think so? https://t.co/3DfCWjDbB7"  
> **AmazonHelp**: "@180264 We're happy to review available options with you directly if you get in touch with us here: https://t.co/hApLpMlfHN. ^EZ"  
> *Response Action*: `contact_channel_redirect`


### Order Cancellation & Address Change (`order_cancellation_modification`)
- **Volume**: 547 messages (0.46%)
- **Description**: Customer requests to cancel an order, alter shipping address, or reports an unexpected automated cancellation.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 318, 'contact_channel_redirect': 81, 'tracking_delivery_guidance': 48}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 827556)**: "@AmazonHelp How do I cancel my order and get my account reimbursed?"  
> **AmazonHelp**: "@317127 I'm sorry you haven't received your order, Les! Let's take a further look tino available options here: https://t.co/JzP7hlA23B ^ML"  
> *Response Action*: `contact_channel_redirect`

> **[2] Customer (Tweet 332421)**: "Hi @115850  I ordered same item twice and while clicking on cancel order link is not opening...how to cancel?"  
> **AmazonHelp**: "@195151 We'll surely help you. Please report this to our support team here: https://t.co/vlvfJr4nN9. ^MP"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 1821567)**: "@115850  you cancelled my order bcoz of price variation? so poor amazon https://t.co/25lNX5zXrw"  
> **AmazonHelp**: "@326546 We've responded to your concern here: https://t.co/EH90Xjh8tr please check. ^KA"  
> *Response Action*: `direct_troubleshooting`


### Returns, Replacements & Damaged Items (`return_replacement_damaged`)
- **Volume**: 3,340 messages (2.83%)
- **Description**: Item arrived broken, defective, or unusable; requesting return label, pickup, or replacement shipment.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 1583, 'return_replacement_guidance': 646, 'contact_channel_redirect': 407}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 347943)**: "@AmazonHelp Yes I know tht...want to know will I get valid warranty if purchased frm othr e-commerce site?"  
> **AmazonHelp**: "@198858 Apart from the kindles sold on Amazon.in, the list of authorized sellers are here: https://t.co/31dGrMjwv7. ^EM"  
> *Response Action*: `seller_guidance`

> **[2] Customer (Tweet 1574300)**: "@AmazonHelp Thanks. Here you go on damaged packaging details. https://t.co/ym7DKb3Omh"  
> **AmazonHelp**: "@403923 I'm sorry but as we're on Twitter, we won't be able to take any action unless you send us your details using the link. ^AM"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 472362)**: "@AmazonHelp I informed you guys on direct message. I was not offered replacement. Only a refund and a voucher. I am well out of pocket and have to spend more on a new one and only with amazon. See DM or emails."  
> **AmazonHelp**: "@227492 Why were you only offered a refund? Was this item sold by a seller, or was there no more in stock?^SM"  
> *Response Action*: `billing_refund_guidance`


### Refund Inquiries & Discrepancies (`refund_status_missing`)
- **Volume**: 3,802 messages (3.22%)
- **Description**: Questions regarding refund processing timelines, missing refunds after return pickup, or incorrect refund amounts.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 1913, 'billing_refund_guidance': 620, 'contact_channel_redirect': 363}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 1383989)**: "@115821 @115850  @AmazonHelp 10days of No product delivery, No proper customer support, No proper answers and NO REFUND #fuckyouamazon"  
> **AmazonHelp**: "@266372 I realize this is taking longer than expected, Yash. We've sent you a correspondence to your registered email address. Kindly check and reply to our correspondence and we'll reach out to you with further assistance. ^MO"  
> *Response Action*: `direct_troubleshooting`

> **[2] Customer (Tweet 288185)**: "@AmazonHelp I have been trying to get a refund of an order since 15 days without 1 satisfactory answer from you. Order no. 404-7609579-9353945."  
> **AmazonHelp**: "@184654 Also, please don't provide your order details as its considered personal info. Our Twitter page is visible to public. 2/2 ^AB"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 277129)**: "Thank you #AmazonIN for the great service". Dlvry boy phone to laya but deke nh gya. Or customer sprt b bht acha. Bina btaye refund kr dia."  
> **AmazonHelp**: "@182217 I'm sorry about that, I’d like to help you; please fill this form: https://t.co/beaaDm0muc and I’ll contact you soon. ^PJ"  
> *Response Action*: `dm_redirect`


### Payment, Billing & Digital Wallet (`payment_and_billing`)
- **Volume**: 1,398 messages (1.19%)
- **Description**: Unexpected card charges, double billing, Amazon Pay transactions, or payment authorization failures.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 862, 'billing_refund_guidance': 180, 'contact_channel_redirect': 130}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 152071)**: "@115830 you incorrectly charged me full price on all 10 items I purchased in your BlackFriday sale. Customer services of no use at all"  
> **AmazonHelp**: "@150750 I'm sorry for the poor experience. When you spoke with us, what insight/options did we provide? ^CO"  
> *Response Action*: `clarification_question`

> **[2] Customer (Tweet 857808)**: "@AmazonHelp I need my cash on my bank account"  
> **AmazonHelp**: "@318325 I understand your concern with the Amazon pay balance. Call us here: https://t.co/2t6DQoUmNZ and we'll be glad to help you.^SF"  
> *Response Action*: `contact_channel_redirect`

> **[3] Customer (Tweet 586806)**: "@AmazonHelp Yes the charge is on my bank account https://t.co/PUtQGyAHpF"  
> **AmazonHelp**: "@258575 Thank you for that information. What is the reference next to your charge? ^AR"  
> *Response Action*: `billing_refund_guidance`


### Account Access & Security (`account_access_security`)
- **Volume**: 1,331 messages (1.13%)
- **Description**: Inability to sign in, account suspended/on hold, password reset issues, or two-factor authentication (OTP) problems.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 863, 'contact_channel_redirect': 225, 'clarification_question': 190}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 2230058)**: "@AmazonHelp How can I go to this page if I have to log in and you’ve blocked my account??!??!? Is there a UK phone number please??"  
> **AmazonHelp**: "@650801 Sorry about that, please use this link instead: https://t.co/zYVX1Qi29G ^BG"  
> *Response Action*: `direct_troubleshooting`

> **[2] Customer (Tweet 2590136)**: "@115830 my log in didnt like my password, I have changed it now and checked orders &amp; addresses. Is there a way of seeing log in activity?"  
> **AmazonHelp**: "@483335 That's odd! Have you noticed any activity on your account or received any suspicious e-mails? ^HM"  
> *Response Action*: `clarification_question`

> **[3] Customer (Tweet 2825613)**: "@115850 Can you plz remove the two step login process..."  
> **AmazonHelp**: "@191152 You can disable Amazon's Two-Step Verification by following the steps from this Help page: https://t.co/0H10jS5o2v. ^AR"  
> *Response Action*: `direct_troubleshooting`


### Wrong Item or Incomplete Shipment (`wrong_item_received`)
- **Volume**: 290 messages (0.25%)
- **Description**: Package contained an entirely different product, wrong size/color, or is missing parts/items from the box.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 131, 'contact_channel_redirect': 60, 'return_replacement_guidance': 30}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 808110)**: "@115850 Despite of giving details, no action from ur side. Trap customer by sending wrong product and then refuse to return is ur habit"  
> **AmazonHelp**: "@296482 If you've shared your details, you must have received a correspondence from our team. Request you to check. ^SQ"  
> *Response Action*: `direct_troubleshooting`

> **[2] Customer (Tweet 2662420)**: "@115821, @AmazonHelp @115850, Wrong product delivered, and now no exchange and no return. Requested many times on CC. Very Bad company."  
> **AmazonHelp**: "@750364 I'd like to understand this better. Please share your details here: https://t.co/GIJyeYqKE0 and I'll reach out. ^KA"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 427733)**: "@AmazonHelp That wrong product which you delivered. I have posted return request three time. Still it has not picked."  
> **AmazonHelp**: "@216718 Sorry for the hassle Satish. Please share your details here: https://t.co/jwehwWy3Pp and I'll get back to you. ^RW"  
> *Response Action*: `direct_troubleshooting`


### Gift Cards, Coupons & Promotional Discounts (`gift_card_promotions`)
- **Volume**: 917 messages (0.78%)
- **Description**: Redemption errors with gift card codes, promo code application failures, or cashback queries.
- **Requires Private PII/Account Lookup**: No (can be solved via public self-service instructions)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 621, 'clarification_question': 100, 'contact_channel_redirect': 87}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 2265441)**: "@AmazonHelp It's not another gift card, it's the cash deposit scheme via delivery guy you can u are having!  It's cash."  
> **AmazonHelp**: "@659446 We would like to understand your concern better. Please call us here: https://t.co/vlvfJr4nN9 for further assistance. ^MJ"  
> *Response Action*: `contact_channel_redirect`

> **[2] Customer (Tweet 134826)**: "@AmazonHelp I ordered a deal on my app with a $50 gift card as a promo. It's only shipping a $25 gift card. She told me I ordered the wrong thing which doesn't even make sense."  
> **AmazonHelp**: "@146393 Hey Christian, did you get the deal directly from Amazon or a seller? Would you be able to give us the link to the promo so we can have a look?^MA"  
> *Response Action*: `seller_guidance`

> **[3] Customer (Tweet 1104393)**: "@115850 order number 402-2086510-5671522 as per support you confirmed me 15% cashback (rs450) but I have not yet received it. 7 days over https://t.co/j4NCQii05N"  
> **AmazonHelp**: "@380619 Please don’t provide your details as we consider them to be personal information. Our Twitter page is public. 3/3 ^SH"  
> *Response Action*: `direct_troubleshooting`


### Third-Party Marketplace Seller Disputes (`third_party_seller_issues`)
- **Volume**: 1,368 messages (1.16%)
- **Description**: Communication failures with 3rd-party marketplace sellers, counterfeit claims, or unfulfilled merchant orders.
- **Requires Private PII/Account Lookup**: Yes (requires secure web portal/auth for real resolution)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 623, 'seller_guidance': 306, 'contact_channel_redirect': 140}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 685754)**: "@AmazonHelp I have not rcv ny revrt .. can't u solve it at earliest...i purchased frm u nt frm tht seller.... Y would i cnct thm"  
> **AmazonHelp**: "@283696 I'm sorry for the miscommunication. Since you haven't received any correspondence, kindly share your details here: https://t.co/beaaDm0muc and we'll contact you soon. ^VH"  
> *Response Action*: `dm_redirect`

> **[2] Customer (Tweet 2338674)**: "@AmazonHelp Yes but he is saying that it's seller price he is selling on his price"  
> **AmazonHelp**: "@676548 Pricing and offers are a decision of the seller. Our third-party marketplace sellers are able to sell items at any (1/2)^VM"  
> *Response Action*: `seller_guidance`

> **[3] Customer (Tweet 1252012)**: "@AmazonHelp seller support is refusing to put a manager on the phone what is the policy?"  
> **AmazonHelp**: "@413692 I'm sorry for the inconvenience. Seller Support would be the best position to help you. ^EB"  
> *Response Action*: `seller_guidance`


### Packaging & Delivery Driver Feedback (`packaging_and_carrier_feedback`)
- **Volume**: 3,087 messages (2.62%)
- **Description**: Complaints regarding poor delivery driver behavior (thrown packages, bad placement), carrier issues, or excessive/inadequate packaging.
- **Requires Private PII/Account Lookup**: No (can be solved via public self-service instructions)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 1426, 'tracking_delivery_guidance': 846, 'contact_channel_redirect': 503}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 1373181)**: "Hey @115830 your "Amazon logistics" is terrible. 8am till 9pm delivery and then delivered to the wrong address and signed for a wrong name"  
> **AmazonHelp**: "@372058 I'm sorry for the poor experience! We'd like to help. Please contact us via phone or chat here: https://t.co/oGDklGgbCZ ^SJ"  
> *Response Action*: `contact_channel_redirect`

> **[2] Customer (Tweet 2481746)**: "@AmazonHelp My package was not included, arriving tomorrow. It's an Amazon-contracted carrier as I understand it (Amazon branded I guess?)."  
> **AmazonHelp**: "@709091 We'd like to look into this. Please send us as much information as you can for my team here: https://t.co/PfgLUyiyIg ^DW"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 1705393)**: "Hey @115830 , maybe next time you deliver you wouldn’t mind bringing me a new fence your driver decided to smash into? https://t.co/l0ldo53yzR"  
> **AmazonHelp**: "@516906 We want to escalate this issue to our transportation department! Please provide your info for us here: https://t.co/4hepQb7wPt ^TN"  
> *Response Action*: `direct_troubleshooting`


### Digital Devices & Subscriptions (Kindle, Echo, Audible) (`digital_kindle_audible`)
- **Volume**: 2,310 messages (1.96%)
- **Description**: Technical and subscription queries regarding Kindle e-readers, Audible audiobooks, Echo/Alexa devices, or Prime Video playback.
- **Requires Private PII/Account Lookup**: No (can be solved via public self-service instructions)
- **Historical AmazonHelp Response Patterns**: `{'direct_troubleshooting': 1527, 'contact_channel_redirect': 317, 'clarification_question': 305}`

**Sample Real Interactions**:
> **[1] Customer (Tweet 2236343)**: "Why is amazon charging me for prime and kindle when I never signed up for this?? 😤"  
> **AmazonHelp**: "@652188 I'm sorry for the unexpected charge! You'll be able to cancel the Amazon Prime Membership at this link here: https://t.co/bhTXbqkZdg ^VS"  
> *Response Action*: `billing_refund_guidance`

> **[2] Customer (Tweet 563925)**: "So...  I restarted my kindle app, again, &amp; is there any reason why the app is giving me this, @117634 ? https://t.co/TQRquxrUp3"  
> **AmazonHelp**: "@251448 I'm sorry to hear of the trouble! Can you please confirm which platform the Kindle app is installed on? Please let us know! Thanks. ^ST"  
> *Response Action*: `direct_troubleshooting`

> **[3] Customer (Tweet 1653464)**: "How to get free Amazon echo dot?@115850 @115821 @115833"  
> **AmazonHelp**: "@444922 Amazon Echo isn't available for free. Currently, it is available to purchase through invitation only. ^PS"  
> *Response Action*: `direct_troubleshooting`


## 5. Candidate Intent Quality Assessment

Critical observations for intent taxonomy construction:
1. **High Semantic Coherence**: Top categories such as `delivery_delay`, `marked_delivered_not_received`, and `return_replacement_damaged` have distinct vocabularies and specific operational triggers.
2. **Disentangling Overlapping Boundaries**:
   - `delivery_delay` vs `marked_delivered_not_received`: Both relate to shipping, but have fundamentally different agent action paths. Delays warrant carrier tracking checks; marked delivered requires verifying neighbors/porch and replacement dispatch if stolen.
   - `return_replacement_damaged` vs `refund_status_missing`: Return is initiation of return/replacement goods; refund is financial ledger status tracking.
3. **Public Auto-handling vs Human Escalation Distinction**:
   - Account-dependent issues (`payment_and_billing`, `account_access_security`, `order_cancellation_modification`) inherently require user verification and order IDs.
   - Policy inquiries (`prime_benefits_membership`, `gift_card_promotions`, `packaging_and_carrier_feedback`) can frequently be auto-handled via knowledge-grounded replies.

## 6. Proposed Golden-Set Sampling Strategy (150–250 Examples)

To support rigorous evaluation without class imbalance bias, we propose a **stratified uniform-proportional hybrid** sampling strategy targeting **200 examples**:

| Stratum (Candidate Intent) | Suggested Sample Size | Sampling Rationale |
|---|---|---|
| `delivery_delay` | 25 | High-frequency dominant intent; high real-world prevalence. |
| `marked_delivered_not_received` | 25 | Critical customer escalation driver. |
| `return_replacement_damaged` | 25 | Core post-purchase intent with rich factual resolutions. |
| `refund_status_missing` | 20 | High customer anxiety; requires clear timeline communication. |
| `prime_benefits_membership` | 20 | Subscription policy intent; clear auto-handling target. |
| `order_cancellation_modification` | 15 | Time-sensitive intent; tests escalation decision boundaries. |
| `payment_and_billing` | 15 | Financial discrepancy intent; strong human escalation candidate. |
| `account_access_security` | 15 | Security critical; strict escalation pattern. |
| `wrong_item_received` | 15 | Physical fulfillment failure; clean return/replacement flow. |
| `gift_card_promotions` | 10 | Policy/redemption intent; low volume but clear rules. |
| `third_party_seller_issues` | 10 | Boundary case testing A-to-Z guarantee vs merchant responsibility. |
| `packaging_and_carrier_feedback` | 10 | Feedback intent; auto-handle acknowledgment vs escalation. |
| `general_inquiry_other` / Ambiguous | 15 | Essential for testing fallback, clarification, and out-of-scope detection. |
| **Total Planned Golden Set** | **220** | **Balanced, representative evaluation corpus.** |

### Ambiguity & Multi-Intent Handling Rules:
- **Primary Intent Rule**: If a customer reports both a damaged package and demands a refund, assign the ultimate requested action (`refund_status_missing`) as primary.
- **Hard Ambiguity**: If a tweet lacks sufficient context (e.g. *"Need help with order"*), classify into `general_inquiry_other` rather than forcing a speculative label.

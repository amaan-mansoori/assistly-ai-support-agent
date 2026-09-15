# Conversation Provenance Audit

This audit uses only raw Twitter ID relationships. It does not modify `data/raw/twcs/twcs.csv`.

## Executive results

- Direct pair validity: **154,976/154,976 (100.00%)**.
- Context-chain validity: **50/50 (100.00%)**.
- Cross-account contamination: **0/50 (0.00%)**.
- Apparently unrelated semantic samples: **13/50 (26.00%)**.

The context traversal repeatedly looks up `in_response_to_tweet_id`; it never uses nearby rows, timestamps, or author adjacency.

## 30 direct pairs

- customer `423267` (author `215771`, inbound `True`): @115821 Trying to call ur call centre but it's just giving me my order details and then call disconnects. What kinda service is that? (2/2) -> AmazonHelp `423266` (inbound `False`, parent `423267`): @215771 I get you have to leave. However, we attempt deliveries until the end of the day. ^HA
- customer `126092` (author `144294`, inbound `True`): @AmazonHelp Day 17 still no pay balance! -> AmazonHelp `126093` (inbound `False`, parent `126092`): @144294 Our team will get back to you once we have an update. Your patience is much appreciated. ^SP
- customer `1178088` (author `397069`, inbound `True`): Que empresa sensacional! @117086 @117804 comprei meu Kindle ontem à tarde e chegou em menos de 24h em casa! https://t.co/uGWueP8Jyd -> AmazonHelp `1178087` (inbound `False`, parent `1178088`): @397069 Corremos para entregar os pacotes bem rápido, Rodrigo! Você já está lendo algum eBook? :3 ^CR
- customer `1020158` (author `224801`, inbound `True`): @AmazonHelp My mail already went for today, i received one of the packages that said delivery on Nov 25 also. But not this one -> AmazonHelp `1020160` (inbound `False`, parent `1020158`): @224801 Just to clarify, when you look at your order details, are you able to tell which carrier is assigned to this order: https://t.co/Y5jpI9gRhE? ^JP
- customer `919860` (author `224602`, inbound `True`): @115850 charged shipping charges inspite of invoice &amp; offer mentioning zero. Please refund. https://t.co/TwsCKBGq1N -> AmazonHelp `919859` (inbound `False`, parent `919860`): @224602 Please don't provide your order details, as we consider it to be personal information. Our Twitter page is public.​ ^EM
- customer `520664` (author `240192`, inbound `True`): i was charged for @115821 prime in July after cancelling my account and just noticed 😐 -> AmazonHelp `520663` (inbound `False`, parent `520664`): @240192 Oh no! I'm sorry to hear that! We are not able to see account information in Twitter. Please click here:  https://t.co/hApLpM3Ejd and contact us via chat or phone for further assistance on this matter.  ^TL
- customer `389345` (author `208145`, inbound `True`): @115850 taken two-day assured delivery. still not delivered -> AmazonHelp `389343` (inbound `False`, parent `389345`): @208145 Apologies for the miss. Did you happen to escalate this to our support team here: https://t.co/T6y6Xlutbs? ^VN
- customer `2802349` (author `781728`, inbound `True`): @AmazonHelp Was about an in stock product taking 6 days to get to me. -> AmazonHelp `2802351` (inbound `False`, parent `2802349`): @781728 Thanks for the information! Could you please send us a link to the product you ordered? We'd like to help if we can! ^AJ
- customer `341477` (author `197579`, inbound `True`): いつのまにかAmazonのプライム会員になってて、クレジットに請求来てビックリした💦 -> AmazonHelp `341476` (inbound `False`, parent `341477`): @197579 (2/2)なお、有料会員移行後にAmazonプライム特典のご利用がない場合は、会員登録の終了と年会費のご返金を承っております。詳細は、こちらのヘルプページをご参照ください。https://t.co/Aw1gyOpOa2 HM
- customer `2984640` (author `823023`, inbound `True`): @137341 just purchased a book on kindle app but could not find this 50₹ credit anywhere. Kindly help https://t.co/apBY7Kp12O -> AmazonHelp `2984639` (inbound `False`, parent `2984640`): @823023 That's strange! We'd like to you have this checked and locate the credit. Kindly reach out to our support team here:https://t.co/vlvfJr4nN9 and we'll look into it. ^EM
- customer `2147946` (author `631343`, inbound `True`): @AmazonHelp ups -> AmazonHelp `2147948` (inbound `False`, parent `2147946`): @631343 Does the latest order tracking show any delays or new expected delivery dates? ^CL
- customer `144151` (author `146876`, inbound `True`): Gracias @AmazonHelp y @116928 por haber solucionado el problema con rapidez. -> AmazonHelp `144150` (inbound `False`, parent `144151`): @146876 Con mucho gusto, estamos para ayudarte. ^FZ
- customer `138954` (author `147313`, inbound `True`): @119356 Fraud done by amazon india. Took 6000rs for a product and never delivered it. After talking to 10 customer executives, escalation help desk team and 2 leadership team. Each 48 hrs wait. 40 days gone nothing happened. -> AmazonHelp `138952` (inbound `False`, parent `138954`): @147313 Sorry about your recent experience, Prashant. We'll certainly help you with this. Kindly share your details here: https://t.co/beaaDm0muc and we'll get back to with an update soon. ^SY
- customer `360240` (author `201315`, inbound `True`): @AmazonHelp Placed the order on 5th and delivery was on 6th but today is 8th and no delivery yet. -> AmazonHelp `360242` (inbound `False`, parent `360240`): @201315 I'm sorry to know about the delay. Please drop in your details here: https://t.co/GIJyeYqKE0 and we'll contact you. ^MP
- customer `898421` (author `333341`, inbound `True`): @115850 Services are so fucked up that now I have lost all patience. So keep the rest of your prime subscription and services. -> AmazonHelp `898420` (inbound `False`, parent `898421`): @333341 That quite a statement. Could you let us know what went wrong? We'd like to help. ^SG
- customer `969869` (author `343708`, inbound `True`): @AmazonHelp ???? -> AmazonHelp `969871` (inbound `False`, parent `969869`): @343708 You can check &amp; respond to the correspondence sent here: https://t.co/8DAc10S7ww ^EM
- customer `2585500` (author `462912`, inbound `True`): Another stellar delivery by @115821. I’m starting a collection of #AmazonFail photos. You never got back to me the last time this happened like you said you would. https://t.co/s5kuE6BMip -> AmazonHelp `2585497` (inbound `False`, parent `2585500`): @462912 I'm terribly sorry about this! Can you please provide additional info about your previous contact with us? We'd also like to research this delivery a bit more. Who is the assigned carrier noted here: https://t.co/Y5jpI9ys9c? ^SH
- customer `130342` (author `145395`, inbound `True`): @AmazonHelp __email__.. Now you are asking for registered mail id from where I ordered. Anyway please update now.. -> AmazonHelp `130343` (inbound `False`, parent `130342`): @145395 Please don’t provide your account details as we consider them to be personal information. Our Twitter page is visible to public. We're unable to access the details over this medium, Sunil. Please use the secured link provided earlier to share details directly. ^JC
- customer `2869630` (author `796883`, inbound `True`): I sure hope an @115821 Drive dev is trying to fix this. 
But since the “upload crash details” step is failing too, they might be blissfully unaware. https://t.co/RyL1JmV8wV -> AmazonHelp `2869629` (inbound `False`, parent `2869630`): @796883 Have you had a chance to report this to our support? We can be reached here: https://t.co/hApLpMlfHN ^BH
- customer `799718` (author `310575`, inbound `True`): Still no sign of Skyrim for Switch that I preordered from @115830 Prime weeks ago and came out last Friday. Not what I've come to expect. -> AmazonHelp `799717` (inbound `False`, parent `799718`): @310575 Hi, really sorry to hear you have not received your pre-order yet! This is not what we want our customers to experience. Can you advise what the tracking states for your order? You can check tracking information via this link: https://t.co/aaDyEz1VgE. ^JC
- customer `2799370` (author `781028`, inbound `True`): Amazonプライム・ビデオでガルパン見放題
最高かな -> AmazonHelp `2799369` (inbound `False`, parent `2799370`): @781028 プライムをご利用いただき、ありがとうございます😊
ぜひお楽しみください( *• ̀ω•́ )b✨ YM
- customer `2131825` (author `627381`, inbound `True`): Ordered groceries from @117795 for the first time! It was awesome! Never leaving the house again! #hermitlife -> AmazonHelp `2131824` (inbound `False`, parent `2131825`): @627381 Hi, glad to hear that you like the service! Thanks for the feedback! ^JJ
- customer `910620` (author `336286`, inbound `True`): @AmazonHelp Still I don't received the product, how can cooperate with you. -> AmazonHelp `910619` (inbound `False`, parent `910620`): @336286 Could you let us know if you have filled in the details in the form provided earlier? ^JS
- customer `2299518` (author `322926`, inbound `True`): @AmazonHelp  https://t.co/oEoQzF661b -> AmazonHelp `2299520` (inbound `False`, parent `2299518`): @322926 Thanks for confirming, Samantha! We always aim to meet the estimated delivery date provided. Please keep us posted on delivery and let us know if anything changes! ^FD
- customer `2978280` (author `821392`, inbound `True`): @115850  ORDER # 408-4132672-3054750 return &amp; refund
सर , मैंने अपने ऑर्डर ORDER # 408-4132672-3054750 को return &amp; refund करने की रिकेवेस्ट भेजी थी लेकिन आज तक मुझे कोई सार्थक जवाब नहीं प्राप्त हुआ है ! -> AmazonHelp `2978279` (inbound `False`, parent `2978280`): @821392 I'm sorry about the delay in return confirmation. Kindly reach out to our team here: https://t.co/T6y6Xlutbs. They'll assist you accordingly. Also, please don't provide your order details, we consider it personal information. Our Twitter page is visible to public. ^VN
- customer `1199049` (author `401718`, inbound `True`): @115850 @AmazonHelp OrderNo 171-4833625-7391554 isn't delivered it's returning back to seller,Without any contact returning back.plz help -> AmazonHelp `1199048` (inbound `False`, parent `1199049`): @401718 Please don't provide your order details, we consider it to be personal information. Our page is visible to the public.(3/3)^SF
- customer `34505` (author `123478`, inbound `True`): @AmazonHelp Com certeza e é quase impossível eu não entrar hahah 💙 -> AmazonHelp `34506` (inbound `False`, parent `34505`): @123478 As pessoas costumam te perguntar quantos livros você já leu? 🙊 ^VL
- customer `605172` (author `263843`, inbound `True`): Omfg I though my life couldn’t get any worse then I just found out that the @129773 account I made so my friend has been charging me for prime every month even tho we cancelled it... -> AmazonHelp `605171` (inbound `False`, parent `605172`): @263843 Hi, sorry to hear that. If you click the following link to manage your Prime membership: https://t.co/D32Nnmth3M and sign in, does it still show that you are a member?^TI
- customer `2151864` (author `632355`, inbound `True`): Bonjour @120533 @AmazonHelp possible d’avoir un bon d’achat de 10€ à faire gagner sur Snapchat ? -> AmazonHelp `2151862` (inbound `False`, parent `2151864`): @632355 Bonjour, cela aurait été avec un grand plaisir mais ce n'est pas possible ^ME
- customer `1487687` (author `465531`, inbound `True`): @115833 has a nice collection of children's stories. My kid doesn't even ask me to tell a story anymore. Praise the AI overlords! -> AmazonHelp `1487686` (inbound `False`, parent `1487687`): @465531 Cool dad strikes ! :P We are overwhelmed with your echo story. ^MJ

## 50 recovered parent chains

### Customer `1097324`
- `customer` tweet `1097322`; author `202497`; inbound `True`; parent `(none)`; text: @AmazonHelp i love it when your support team transfers me four times to a dead line, really great service
- `AmazonHelp` tweet `1097320`; author `AmazonHelp`; inbound `False`; parent `1097322`; text: @202497 I'm sorry you were disconnected! We'd like to help if possible. W/o posting any personal info can you tell us what has happened?^EP
- `customer` tweet `1097321`; author `202497`; inbound `True`; parent `1097320`; text: @AmazonHelp keep getting transferred back and forth no help for the free audible book promo
- `AmazonHelp` tweet `1097323`; author `AmazonHelp`; inbound `False`; parent `1097321`; text: @202497 Can you tell us more about what's going on with the promo? Are you getting an error message when you attempt to redeem? ^KH
- `customer` tweet `1097324`; author `202497`; inbound `True`; parent `1097323`; text: @AmazonHelp its just not applying, support is just transferring me back and forth

### Customer `525546`
- `customer` tweet `525549`; author `241585`; inbound `True`; parent `(none)`; text: @115850 What the hell is going on.. I didn't received my order and it shows .. Item handed to customer. Poor service. Waiting from 4 days. I made online payment. Not expected poor service like that from #Amazon
- `AmazonHelp` tweet `525548`; author `AmazonHelp`; inbound `False`; parent `525549`; text: @241585 I'm sorry you've not received your order. We'd like to look into it. Please report it to our support team here: https://t.co/2t6DQpbXFx we'll help you out. ^AP
- `customer` tweet `525546`; author `241585`; inbound `True`; parent `525548`; text: @AmazonHelp I have reported my complaint already.. 2 days ago. But no response from ur side. I'm not expecting this. Pls refund my amount as soon as possible. I would prefer another service provider

### Customer `803948`
- `customer` tweet `803946`; author `311601`; inbound `True`; parent `(none)`; text: @AmazonHelp @115850 now you started giving false information also?? really pathetic poor amazon ..read my chat with cc 
Arun Prasath,
- `AmazonHelp` tweet `803943`; author `AmazonHelp`; inbound `False`; parent `803946`; text: @311601 Could you please tell us what went wrong Raman? ^HN
- `customer` tweet `803944`; author `311601`; inbound `True`; parent `803943`; text: @AmazonHelp they said we have cancelled your courier, they all told lie as still courier arrived, even after requesting for cancellation
- `AmazonHelp` tweet `803947`; author `AmazonHelp`; inbound `False`; parent `803944`; text: @311601 Sorry for the hassle. Please report this to our support team here: https://t.co/vlvfJr4nN9 and we'll check this. ^HN
- `customer` tweet `803948`; author `311601`; inbound `True`; parent `803947`; text: @AmazonHelp no i want strict punishment against the executives who told lie to me

### Customer `1367933`
- `customer` tweet `1367931`; author `438440`; inbound `True`; parent `(none)`; text: El servicio post venta de @116928 deja mucho que desear. Veinte llamadas por un producto defectuoso que prometen cambiar (desde la primera llamada). Y así hasta hoy. Así no, ¿eh? https://t.co/eMLXIEt8nI
- `AmazonHelp` tweet `1367928`; author `AmazonHelp`; inbound `False`; parent `1367931`; text: @438440 Hola, sin compartir información sensible como el número del pedido, ¿nos comentarías qué sucedió? ^HC
- `customer` tweet `1367929`; author `438440`; inbound `True`; parent `1367928`; text: @AmazonHelp Sí, muchas gracias! Veréis, un producto en garantía se averió. Acordasteis reembolsar el importe -bajo, por cierto-. Confirmasteis que lo habíais hecho. pero no llegó. Pedisteis certificación bancaria.La hemos enviado dos veces. Y todavía seguimos sin recibir el importe! Gracias!
- `AmazonHelp` tweet `1367932`; author `AmazonHelp`; inbound `False`; parent `1367929`; text: @438440 ¿Qué fue lo último que te informaron nuestros compañeros de Servicio al cliente? ^HC
- `customer` tweet `1367933`; author `438440`; inbound `True`; parent `1367932`; text: @AmazonHelp Lo último que nos han dicho, hoy, es que enviemos la carta. La misma carta que hemos enviado dos veces -como os recordaba, la última hace dos semanas-. Es insistir para que te digan lo mismo.Menos serio,suena a cualquier otra cosa. Os he enviado un mensaje privado con + detalles.

### Customer `351492`
- `customer` tweet `351488`; author `199613`; inbound `True`; parent `(none)`; text: @115850 - Ordered item auto cancelled without any prior info. Disgusting experience with Amazon shopping this time. Thumbs down!
- `AmazonHelp` tweet `351489`; author `AmazonHelp`; inbound `False`; parent `351488`; text: @199613 Canceled orders are followed by an email containing the reason for cancellation. Please refer to it. ^RB 1/2
- `customer` tweet `351490`; author `199613`; inbound `True`; parent `351489`; text: @AmazonHelp - If reason mentioned I would feel more happy. Simply cancelled with no justification. Not fair at all 😢
- `AmazonHelp` tweet `351491`; author `AmazonHelp`; inbound `False`; parent `351490`; text: @199613 Sorry for the hassle, Prasad. As mentioned earlier, you should've received an email with the reason for cancellation. ^MS
- `customer` tweet `351492`; author `199613`; inbound `True`; parent `351491`; text: @AmazonHelp - Colud u plz help me where it is mentioned the reason for the cancellation from the attached pic ? https://t.co/qLzCPvLVUz

### Customer `323288`
- `customer` tweet `323286`; author `192994`; inbound `True`; parent `(none)`; text: Hello @AmazonHelp si je pre commande un article , serais je debiter le jour de l'envoie ou de suite merci @120533
- `AmazonHelp` tweet `323284`; author `AmazonHelp`; inbound `False`; parent `323286`; text: @192994 Bonjour, effectivement le jour de l'expédition de votre article. ^ KO
- `customer` tweet `323285`; author `192994`; inbound `True`; parent `323284`; text: @AmazonHelp D'accord super precommande de #StarWarsBattlefrontII precommandé chez vous ;)
- `AmazonHelp` tweet `323287`; author `AmazonHelp`; inbound `False`; parent `323285`; text: @192994 Ah coool 🎮 #seriesaddict?? ^SM
- `customer` tweet `323288`; author `192994`; inbound `True`; parent `323287`; text: @AmazonHelp Amazon video et neflix ;)

### Customer `1578520`
- `customer` tweet `1578516`; author `486141`; inbound `True`; parent `(none)`; text: @115850  you do have pathetic transportation system.
Thank you for ruining my Diwali.

Amazon.in Order # 407-5892643-1477106
- `AmazonHelp` tweet `1578517`; author `AmazonHelp`; inbound `False`; parent `1578516`; text: @486141 I'm sorry to know about the delivery issue. Please share your details here: https://t.co/GIJyeYqKE0 and I'll reach out. ^KA
- `customer` tweet `1578520`; author `486141`; inbound `True`; parent `1578517`; text: @AmazonHelp I dont care if your page is public. I hv writen order no. m sure u can find out the the issue. I am typing detail experience on fb, public.

### Customer `336980`
- `customer` tweet `336982`; author `196398`; inbound `True`; parent `(none)`; text: Just got another email from @115830 welcoming me to Prime, this time it seems I have no option to cancel now. What the fresh hell is this? https://t.co/yl7EPEDCqR
- `AmazonHelp` tweet `336979`; author `AmazonHelp`; inbound `False`; parent `336982`; text: @196398 Very odd! We'd like to review your account and assist you directly, please reach us here: https://t.co/JzP7hlA23B ^AC
- `customer` tweet `336980`; author `196398`; inbound `True`; parent `336979`; text: @AmazonHelp but of course it might sign me up again whatever "it" is. I changed my password. I'm going to bed soon, I am too tired to fix your systems!!

### Customer `206052`
- `customer` tweet `206053`; author `164797`; inbound `True`; parent `(none)`; text: @115821 in India are back to being thieves without any honour. Phone never got delivered. Delviery exec on the lam. @115821  refuses to help
- `customer` tweet `206051`; author `164797`; inbound `True`; parent `206053`; text: @115821 @AmazonHelp are you invoking Prometheus to obtain embers for the oven? Run the risk of ruining the pudding. Meanwhile, hunger pangs riot.
- `customer` tweet `206052`; author `164797`; inbound `True`; parent `206051`; text: @115821 @AmazonHelp @AmazonHelp I must say that the lot of you, under the tutelage of principles of minting money are the same. Beyond the promises, nothing.

### Customer `1394604`
- `customer` tweet `802402`; author `311203`; inbound `True`; parent `(none)`; text: @118919 I received this damaged product. I doubt about my other orders which are yet to be delivered. https://t.co/JlV4qAac3j
- `customer` tweet `802404`; author `311203`; inbound `True`; parent `802402`; text: @118919 @118919 Amazon and @AmazonHelp Amazon drama of return started. Only dates are communicated but no one comes to pick for return. Shame
- `AmazonHelp` tweet `1394603`; author `AmazonHelp`; inbound `False`; parent `802404`; text: @311203 I apologize for the inconvenience. I’d like to help you; please fill this form: https://t.co/beaaDm0muc and I’ll contact you. ^JS
- `customer` tweet `1394604`; author `311203`; inbound `True`; parent `1394603`; text: @AmazonHelp Still i need 2 provide u further info. Kindly take back ur damaged product and refund. That all I need. No more shopping with amazon. Thnx

### Customer `1021664`
- `customer` tweet `1021665`; author `361776`; inbound `True`; parent `(none)`; text: @115821 i know it's Sunday but can i get this package before 8pm tonight.... Smh wanted to game tonight but i guess i have to wait till tomorrow after work...
- `AmazonHelp` tweet `1021663`; author `AmazonHelp`; inbound `False`; parent `1021665`; text: @361776 I'm sorry for the wait! What's the delivery date and most recent tracking update on the order: https://t.co/Y5jpI9gRhE? ^EP
- `customer` tweet `1021664`; author `361776`; inbound `True`; parent `1021663`; text: @AmazonHelp It's delivery date is today and i got the message that it's being shipped today at 9:45 a.m. but i guess I'm normally one of the last people on the delivery route. I have prime shipping and ordered on Friday

### Customer `177395`
- `customer` tweet `177396`; author `157768`; inbound `True`; parent `(none)`; text: Does @116090 sell Samsung s8 plus lifeproof cases? Not a great filter system when doing a search on the website. I'm not scrolling through 20,000 items
- `customer` tweet `177395`; author `157768`; inbound `True`; parent `177396`; text: @116090 @AmazonHelp

### Customer `2282024`
- `customer` tweet `2282020`; author `185401`; inbound `True`; parent `(none)`; text: @AmazonHelp We haven’t been able to access our account because there is an old phone number on file. Can u help?
- `AmazonHelp` tweet `2282017`; author `AmazonHelp`; inbound `False`; parent `2282020`; text: @185401 I'm sorry for the trouble with this! We'd like to take a closer look with you, please reach out to us here: https://t.co/vE7wlvKLJl ^SB
- `customer` tweet `2282019`; author `185401`; inbound `True`; parent `2282017`; text: @AmazonHelp This has to be resolved today. I have orders on my seller account that are waiting
- `AmazonHelp` tweet `2282021`; author `AmazonHelp`; inbound `False`; parent `2282019`; text: @185401 Hey, Maritza! When you contacted us, what did information did we provide regarding your account? ^LA
- `customer` tweet `2282022`; author `185401`; inbound `True`; parent `2282021`; text: @AmazonHelp Everything. Name, email, phone number, billing address
- `AmazonHelp` tweet `2282023`; author `AmazonHelp`; inbound `False`; parent `2282022`; text: @185401 When you contacted us was it via phone, chat, or e-mail? Were we able to offer you any information or insight into what's going on with your account? Were you able to speak to a member of our Seller Support team? ^LS
- `customer` tweet `2282024`; author `185401`; inbound `True`; parent `2282023`; text: @AmazonHelp Phone. Spoke with someone. Not sure what dept

### Customer `2683612`
- `customer` tweet `2683613`; author `202186`; inbound `True`; parent `(none)`; text: @115833 irgendwie brüllt einen Alexa seit 2Tagen nach dem Neustart immer an = merkt sich die eingestellte Lautstärke nicht. Normal?
- `AmazonHelp` tweet `2683611`; author `AmazonHelp`; inbound `False`; parent `2683613`; text: @202186 Hi, gerne kannst du das von unserem Echo-Support überprüfen lassen: https://t.co/ohyvGrpvrY Lieber Gruß ^SI
- `customer` tweet `2683612`; author `202186`; inbound `True`; parent `2683611`; text: @AmazonHelp erledigt. Danke. Ansonsten sollte man die Alexa TV Werbung überdenken.bringt meine Alexa immer ganz nervös bzw durcheinander 😉

### Customer `424993`
- `customer` tweet `424995`; author `216137`; inbound `True`; parent `(none)`; text: @115825 wo ist die neue Outlanderfolge?
- `AmazonHelp` tweet `424994`; author `AmazonHelp`; inbound `False`; parent `424995`; text: @216137 Die Kollegen arbeiten daran, die 10te Folge der 3ten Staffel "Outlander [OV/OmU]" so schnell als möglich online zu stellen. Bitte hab noch etwas Geduld und behalte unsere Seite im Auge. Viele Grüße ^DS
- `customer` tweet `424993`; author `216137`; inbound `True`; parent `424994`; text: @AmazonHelp Und da ist sie auch schon

### Customer `1555464`
- `customer` tweet `1555463`; author `481013`; inbound `True`; parent `(none)`; text: @115850 the service what you provide is not what we expect. #poorservice #AmazonIndia
- `customer` tweet `1555464`; author `481013`; inbound `True`; parent `1555463`; text: @115850 It's either the indian post or your delivery guy put the blame on, your investigations are left uninformed about the actions taken.

### Customer `284040`
- `customer` tweet `284041`; author `183647`; inbound `True`; parent `(none)`; text: @AmazonHelp I just Clicked the order cancellation button by mistakenly but I want that order...
The order is shipped and Will that reach me?
- `AmazonHelp` tweet `284039`; author `AmazonHelp`; inbound `False`; parent `284041`; text: @183647 I'm sorry to know that. Kindly get in touch with our team here: https://t.co/T6y6Xlutbs. They'll look into this for you. ^VN
- `customer` tweet `284040`; author `183647`; inbound `True`; parent `284039`; text: @AmazonHelp 408-3137785-3626763 this is my Order ID...
Please Make a confirm that This product won't be Cancelled

### Customer `2781753`
- `customer` tweet `2781761`; author `379972`; inbound `True`; parent `(none)`; text: Bought a #reputation CD? Reedem your #TaylorSwiftTix boost now at https://t.co/gHJEfrL8xJ. Still need to get your hands on a copy? Buy reputation here https://t.co/TBdGjdFwnF #reputationOUTNOW https://t.co/c9tbpfknAd
- `customer` tweet `2781760`; author `776865`; inbound `True`; parent `2781761`; text: @379972 I bought the two special edition magazines through @116316 but there were no codes included. Are they only provided to US customers? Would be a bummer, I'm from the Netherlands and would like to undertake a dream trip to see Taylor perform in Nashville.
- `AmazonHelp` tweet `2781759`; author `AmazonHelp`; inbound `False`; parent `2781760`; text: @776865 Please contact our support to take a look at: https://t.co/jOmwUpUUS5 Best regards ^TG
- `customer` tweet `2781753`; author `776865`; inbound `True`; parent `2781759`; text: @AmazonHelp I already did that, but they said they couldn’t help me because the ticket code was not mentioned in the product description on the website. Which isn’t strange, since promotional flyers are never mentioned on the Amazon site...

### Customer `1157958`
- `customer` tweet `1157961`; author `392397`; inbound `True`; parent `(none)`; text: @115821 what is up with Order# 113-5564825-4549854.  Ordered two day shipping three days ago and it has not shipped yet.
- `AmazonHelp` tweet `1157960`; author `AmazonHelp`; inbound `False`; parent `1157961`; text: @392397 We do our best to meet the delivery date in your order details: https://t.co/q4LAMZ3tbE Have we missed it? ^GL
- `customer` tweet `1157958`; author `392397`; inbound `True`; parent `1157960`; text: @AmazonHelp Two day shipping, ordered three days ago and you still haven't shipped it yet.   Why would you wait to ship so I can get it on Monday?

### Customer `1488705`
- `customer` tweet `1488722`; author `465794`; inbound `True`; parent `(none)`; text: @115850 @1560 
Bad experience with Amazon. Order No. 405-6497515-7367543. Till product not received. Want Recovery. OrderDetails https://t.co/olz6J5kUrb
- `AmazonHelp` tweet `1488721`; author `AmazonHelp`; inbound `False`; parent `1488722`; text: @465794 Sorry to hear this. We'd like to sort this out. Please share your details here: https://t.co/beaaDm0muc for support. 1/2 ^RS
- `customer` tweet `1488720`; author `465794`; inbound `True`; parent `1488721`; text: @AmazonHelp Already share all the details. Today also talk with your toll free number.
- `AmazonHelp` tweet `1488719`; author `AmazonHelp`; inbound `False`; parent `1488720`; text: @465794 I understand there's been an unpleasant experience. Thanks for filling in the details, we'll get in touch with you soon. ^JC
- `customer` tweet `1488717`; author `465794`; inbound `True`; parent `1488719`; text: @AmazonHelp When I will get my product. I have paid amount already.
- `AmazonHelp` tweet `1488716`; author `AmazonHelp`; inbound `False`; parent `1488717`; text: @465794 the link provided earlier and we'll get back to you with an appropriate resolution. 2/2 ^SY
- `customer` tweet `1488715`; author `465794`; inbound `True`; parent `1488716`; text: @AmazonHelp details shared
- `AmazonHelp` tweet `1488714`; author `AmazonHelp`; inbound `False`; parent `1488715`; text: @465794 We have sent a correspondence to your registered email id. Request you to check and reply for further assistance. ^SB
- `customer` tweet `1488713`; author `465794`; inbound `True`; parent `1488714`; text: @AmazonHelp Mail not received
- `AmazonHelp` tweet `1488712`; author `AmazonHelp`; inbound `False`; parent `1488713`; text: @465794 Apologies, we are working on it. We'll get back to you soon with an update. ^SI
- `customer` tweet `1488711`; author `465794`; inbound `True`; parent `1488712`; text: @AmazonHelp When. I want my product today only.
- `AmazonHelp` tweet `1488710`; author `AmazonHelp`; inbound `False`; parent `1488711`; text: @465794 I understand it's taking time but please be assured as mentioned earlier, we will get back to you at the earliest. ^PB
- `customer` tweet `1488700`; author `465794`; inbound `True`; parent `1488710`; text: @AmazonHelp any updates
- `AmazonHelp` tweet `1488698`; author `AmazonHelp`; inbound `False`; parent `1488700`; text: @465794 Please share the required details from the order related account for best assistance. (2/2)^YP
- `customer` tweet `1488699`; author `465794`; inbound `True`; parent `1488698`; text: @AmazonHelp I have already share
- `AmazonHelp` tweet `1488701`; author `AmazonHelp`; inbound `False`; parent `1488699`; text: @465794 If you've shared the details, you'll receive a correspondence from our team. Kindly find it here: https://t.co/ubzNHWZvL2 ^SG
- `customer` tweet `1488702`; author `465794`; inbound `True`; parent `1488701`; text: @AmazonHelp What about my product. https://t.co/y6vnvfEVjY
- `AmazonHelp` tweet `1488704`; author `AmazonHelp`; inbound `False`; parent `1488702`; text: @465794 Vijay, I gt the concern. Please reply to the email for further assistance. ^MS
- `customer` tweet `1488705`; author `465794`; inbound `True`; parent `1488704`; text: @AmazonHelp Till i not received any mail

### Customer `2902486`
- `customer` tweet `2902484`; author `803914`; inbound `True`; parent `(none)`; text: @AmazonHelp what do I need to do to disable 2-step verification on my account which i am locked out of? I've called customer support several times over the last couple months and have initiated the 2-step verification account recovery. Nothing else has been done to resolve this.
- `AmazonHelp` tweet `2902482`; author `AmazonHelp`; inbound `False`; parent `2902484`; text: @803914 Hey there! Please reach out to us by phone here: https://t.co/jzvkhdlrK5 so that we can look into this with you. Talk to you soon! ^KJ
- `customer` tweet `2902483`; author `803914`; inbound `True`; parent `2902482`; text: @AmazonHelp I just spoke with customer service last week (and have a 5 or 6 times before regarding this) and all they do is try and do a password reset. I'm still waiting for the account specialist to contact me to disable the 2-step. It's been 3 months when it should have been 1-2 days.
- `AmazonHelp` tweet `2902485`; author `AmazonHelp`; inbound `False`; parent `2902483`; text: @803914 Have you received any correspondence from our Account Specialist? Please be sure to check you spam/junk folder. ^AC
- `customer` tweet `2902486`; author `803914`; inbound `True`; parent `2902485`; text: @AmazonHelp No I have not received anything from them yet.

### Customer `698766`
- `customer` tweet `698770`; author `286677`; inbound `True`; parent `(none)`; text: @115821 sucks!  They say 2 day delivery but fail to deliver!
- `AmazonHelp` tweet `698769`; author `AmazonHelp`; inbound `False`; parent `698770`; text: @286677 We always strive to deliver by the date provided in your confirmation e-mail. Have we missed this date? We're here to help! ^ML
- `customer` tweet `698768`; author `286677`; inbound `True`; parent `698769`; text: @AmazonHelp Yeah!  Deceptive delivery advertising.  I’ll do my best to not use amazon again.  And let everyone else know as well!  Prime? Hahahahaha!
- `AmazonHelp` tweet `698767`; author `AmazonHelp`; inbound `False`; parent `698768`; text: @286677 I understand your frustration. What does the most recent tracking info state here: https://t.co/q4LAMZ3tbE? ^GG
- `customer` tweet `698766`; author `286677`; inbound `True`; parent `698767`; text: @AmazonHelp Says 8🤔.  Look at the time🙄. https://t.co/SM7XezAD83

### Customer `257819`
- `customer` tweet `257823`; author `177334`; inbound `True`; parent `(none)`; text: @AmazonHelp ordered something on prime. It's been out for delivery all day. Showing on tracking in Nottingham.. I live in Nuneaton...
- `AmazonHelp` tweet `257822`; author `AmazonHelp`; inbound `False`; parent `257823`; text: @177334 Have been given an attempted delivery notification or a notification of delay? ^ZW
- `customer` tweet `257820`; author `177334`; inbound `True`; parent `257822`; text: @AmazonHelp No, nothing has come through. It still says 'out for delivery' on the tracking.
- `AmazonHelp` tweet `257818`; author `AmazonHelp`; inbound `False`; parent `257820`; text: @177334 Deliveries can be made up to 10pm. Please keep us updated on its arrival! We're here to help. ^ZW
- `customer` tweet `257819`; author `177334`; inbound `True`; parent `257818`; text: @AmazonHelp Still no delivery and tracking still says out for delivery. What happens now please? Really wanted the item today 🙁 https://t.co/YvgyaWbwD0

### Customer `180251`
- `customer` tweet `180253`; author `158410`; inbound `True`; parent `(none)`; text: See what @115850 is doing not able to deliver the product admitt their mistake apolzs and inform  returning your amount but not get it yet https://t.co/ryh83lVEbx
- `AmazonHelp` tweet `180252`; author `AmazonHelp`; inbound `False`; parent `180253`; text: @158410 DId we happen to miss the estimated delivery date? ^AG
- `customer` tweet `180251`; author `158410`; inbound `True`; parent `180252`; text: @AmazonHelp @115851 It was sowing delivered but not delivered to me when complain reply me wrongly update if not get by 8 we will refund https://t.co/nSWem4Wort

### Customer `856034`
- `customer` tweet `856047`; author `323282`; inbound `True`; parent `(none)`; text: @AmazonHelp 
This keeps poping up when i go to my orders page. Help? https://t.co/vtHSYxD7KY
- `AmazonHelp` tweet `856046`; author `AmazonHelp`; inbound `False`; parent `856047`; text: @323282 Sorry to see this. Have you tried restarting the app? Or restarting the phone itself? Keep us posted. ^PK
- `customer` tweet `856045`; author `323282`; inbound `True`; parent `856046`; text: @AmazonHelp Yeah ive tried both. This issue is even happening on my secondary device.
- `AmazonHelp` tweet `856044`; author `AmazonHelp`; inbound `False`; parent `856045`; text: @323282 Have you checked your connection? If it is happening on both devices? ^NV
- `customer` tweet `856043`; author `323282`; inbound `True`; parent `856044`; text: @AmazonHelp Yep tried it on wifi and cellular data.
- `AmazonHelp` tweet `856042`; author `AmazonHelp`; inbound `False`; parent `856043`; text: @323282 What Amazon website do you use? https://t.co/xJXEJm9Z6c? ^JJ
- `customer` tweet `856041`; author `323282`; inbound `True`; parent `856042`; text: @AmazonHelp https://t.co/uwLltInzJI
- `AmazonHelp` tweet `856037`; author `AmazonHelp`; inbound `False`; parent `856041`; text: @323282 Thanks for confirming. Are you able to view your orders via this link: https://t.co/Y5jpI9gRhE? ^JJ
- `customer` tweet `856036`; author `323282`; inbound `True`; parent `856037`; text: @AmazonHelp Its strange because i just ordered something off that email 8 hours ago
- `AmazonHelp` tweet `856035`; author `AmazonHelp`; inbound `False`; parent `856036`; text: @323282 That is strange. Please reach out to us directly here: https://t.co/hApLpMlfHN and we can look into it. ^PK
- `customer` tweet `856034`; author `323282`; inbound `True`; parent `856035`; text: @AmazonHelp I cant use that link because i cant log in

### Customer `1140808`
- `customer` tweet `1140806`; author `388536`; inbound `True`; parent `(none)`; text: La nueva aplicación de @117634 es amor. Ya le tocaba un lavado de cara.
- `AmazonHelp` tweet `1140804`; author `AmazonHelp`; inbound `False`; parent `1140806`; text: @388536 ¡Óscar, es mucho amor, verdad! ¿Qué fue lo que más te gustó? ❤ ^DA
- `customer` tweet `1140805`; author `388536`; inbound `True`; parent `1140804`; text: @AmazonHelp El libro que estoy leyendo en la barra de navegación de la aplicación. 😍
- `AmazonHelp` tweet `1140807`; author `AmazonHelp`; inbound `False`; parent `1140805`; text: @388536 Que hermoso eso. ¿Cuál libro estás leyendo? 😱💙 ^DA
- `customer` tweet `1140808`; author `388536`; inbound `True`; parent `1140807`; text: @AmazonHelp «El color de la magia» de Terry Pratchett.

### Customer `286802`
- `customer` tweet `286804`; author `184337`; inbound `True`; parent `(none)`; text: @AmazonHelp my order was due to arrive yesterday and still hasn't- its needed for tomorrow!?
- `AmazonHelp` tweet `286801`; author `AmazonHelp`; inbound `False`; parent `286804`; text: @184337 I'm so sorry about this. Please reach out by phone so we can investigate this further with you: https://t.co/qy3J24VGxb ^GR
- `customer` tweet `286802`; author `184337`; inbound `True`; parent `286801`; text: @AmazonHelp Hello?!

### Customer `210418`
- `AmazonHelp` tweet `210417`; author `AmazonHelp`; inbound `False`; parent `(none)`; text: @165805 Hello, the contest is genuine, there will be 2 winners who will receive iPhone 8 by 30 November 2017. ^RD
- `customer` tweet `210418`; author `165805`; inbound `True`; parent `210417`; text: @AmazonHelp I agree. But I guys have mentioned IPhone 8 32 GB. It is not available in 32gb. It’s available in 64gb

### Customer `349447`
- `customer` tweet `349451`; author `170761`; inbound `True`; parent `(none)`; text: @115850 by mistake I cancel my order can u pls revert back and delivered to me asap.
- `customer` tweet `349447`; author `170761`; inbound `True`; parent `349451`; text: @115850 Order # 408-0365818-9451558  pls arrange delivery of my order by mistake it has been canceled by me 2day morning but I need this asap.

### Customer `1579700`
- `customer` tweet `1579696`; author `486414`; inbound `True`; parent `(none)`; text: @115850 @115821 unable to add pay balance and calls not connecting to support. Says can't find your order and call disconnects. Unhappy
- `AmazonHelp` tweet `1579694`; author `AmazonHelp`; inbound `False`; parent `1579696`; text: @486414 Sorry to know you were unable to reach out support, Adil. Please reach us via chat or email. We'll assist. ^SV
- `customer` tweet `1579695`; author `486414`; inbound `True`; parent `1579694`; text: @AmazonHelp Too late, when I wanted help I didn't get. God knows where is it chat option and emails take too long. Will not want to use Amazon pay ever.
- `AmazonHelp` tweet `1579697`; author `AmazonHelp`; inbound `False`; parent `1579695`; text: @486414 I understand your concern, Adil. The chat option would appear right below the phone option on the contact us page. ^AP
- `customer` tweet `1579698`; author `486414`; inbound `True`; parent `1579697`; text: @AmazonHelp I don't see any chat option anywhere. https://t.co/ffEXINjthJ
- `AmazonHelp` tweet `1579699`; author `AmazonHelp`; inbound `False`; parent `1579698`; text: @486414 This is unusual, could you try from any browser &amp; keep us posted. ^MJ
- `customer` tweet `1579700`; author `486414`; inbound `True`; parent `1579699`; text: @AmazonHelp You should have figured it by now I am using app and trying to do it from app. It's not on a browser.

### Customer `1097687`
- `customer` tweet `1097692`; author `379032`; inbound `True`; parent `(none)`; text: A bit disappointed that I bought something that has Prime marked on it and it won't be here for another week, possibly. @AmazonHelp
- `AmazonHelp` tweet `1097691`; author `AmazonHelp`; inbound `False`; parent `1097692`; text: @379032 I'm sorry for the wait. Will we miss our delivery date from your original order confirmation: https://t.co/amPZYIJKOB? ^EA
- `customer` tweet `1097688`; author `379032`; inbound `True`; parent `1097691`; text: @AmazonHelp I selected 2 day shipping with my prime and ordered yesterday. The other items I bought have shipped...
- `AmazonHelp` tweet `1097685`; author `AmazonHelp`; inbound `False`; parent `1097688`; text: @379032 Not all items may ship at the same time. What's the delivery date shown in your order confirmation e-mail for this item? ^CL
- `customer` tweet `1097687`; author `379032`; inbound `True`; parent `1097685`; text: @AmazonHelp It says Oct 31. I just thought with Prime and if marked as Prime, it was 2 days. If you go on the item now, it says 2 days if ordered today.

### Customer `2254393`
- `customer` tweet `2254394`; author `656688`; inbound `True`; parent `(none)`; text: @AmazonHelp  seriously for the last 3 months waiting for my refund no one is helping me . Bank told me that transaction number is incorrect and you are saying please contact bank . I am fed up from all this . Already sent bank statement to u (1/2)
- `customer` tweet `2254393`; author `656688`; inbound `True`; parent `2254394`; text: @AmazonHelp This type of services is not expected frm Amazon please help guys my 688 is still not received continuously sending mail and you guys are saying to charge a dispute but bank customer care is denying to raise the dispute charge even I visited branch 6 times please help @115851

### Customer `1497292`
- `customer` tweet `1497293`; author `467639`; inbound `True`; parent `(none)`; text: Love it when you buy a course book from Amazon &amp; it hasn't come so you email the seller &amp; they basically say there's nothing they can do 👍🏼😤
- `AmazonHelp` tweet `1497291`; author `AmazonHelp`; inbound `False`; parent `1497293`; text: @467639 Hi, sorry to hear that. Did the Seller offer any options? What's the delivery date? Is the order fulfilled by the Seller? ^JJ
- `customer` tweet `1497292`; author `467639`; inbound `True`; parent `1497291`; text: @AmazonHelp Hi, no they didn't. Delivery date was 26th October and the seller said they no longer had the book and couldn't access their account anymore

### Customer `550483`
- `customer` tweet `550479`; author `248239`; inbound `True`; parent `(none)`; text: Hola @AmazonHelp, pedí un libro por https://t.co/tB3R3JLrz1 y estaba para llegar el 30 de noviembre pero todavía no llega. ¿Hay alguna posibilidad de rastrear el paquete?
- `AmazonHelp` tweet `550477`; author `AmazonHelp`; inbound `False`; parent `550479`; text: @248239 ¡Hola Ana.! Sentimos los inconvenientes con tu pedido. Sin compartir información personal ni confidencial, ¿Podrías indicarnos si el producto  es vendido directamente por Amazon o si ha sido vendido por un vendedor externo? ^PC
- `customer` tweet `550478`; author `248239`; inbound `True`; parent `550477`; text: @AmazonHelp Por amazon directamente.
- `AmazonHelp` tweet `550480`; author `AmazonHelp`; inbound `False`; parent `550478`; text: @248239 Ana, ¿ya verificaste la siguiente información sobre como contactar al transportista, accesando el siguiente enlace?: https://t.co/QuK3kbLa0x. ^NB
- `customer` tweet `550481`; author `248239`; inbound `True`; parent `550480`; text: @AmazonHelp Es que no supe cuál es, porque en el pedido aparece imexx.
- `AmazonHelp` tweet `550482`; author `AmazonHelp`; inbound `False`; parent `550481`; text: @248239 Ana ¿Podrías revisar si en el correo de confirmación de compra se indica el número de guía o de seguimiento? de ser así puedes ingresar en el siguiente enlace para rastrear el paquete con esa información: https://t.co/jHUOZhf1qM  ^PC
- `customer` tweet `550483`; author `248239`; inbound `True`; parent `550482`; text: @AmazonHelp No me deja rastrearlo, y me preocupa que se haya perdido porque lo pedí desde el exterior y no tengo casillero. Algunas personas me han dicho que es necesario el casillero, ¿es cierto? ¿Qué podría hacer entonces si se perdió?

### Customer `1528688`
- `customer` tweet `1528690`; author `474602`; inbound `True`; parent `(none)`; text: "Livraison de COD:WWII Mardi 7 Novembre " Merci @120533 😒
- `AmazonHelp` tweet `1528689`; author `AmazonHelp`; inbound `False`; parent `1528690`; text: @474602 Bonsoir, s'agit-il de la date communiquée en passant votre commande ? ^MA
- `customer` tweet `1528688`; author `474602`; inbound `True`; parent `1528689`; text: @AmazonHelp Non c'était marqué le 3

### Customer `1447996`
- `customer` tweet `1447997`; author `456020`; inbound `True`; parent `(none)`; text: @115830 I ordered items, never got delivered. On a prime trial ? Is this how #guaranteeworks ? Got told unable to confirm delivery address
- `AmazonHelp` tweet `1447995`; author `AmazonHelp`; inbound `False`; parent `1447997`; text: @456020 I'm so sorry! Please contact us via phone/chat here: https://t.co/JzP7hlA23B so we may look into this with you. ^KL
- `customer` tweet `1447996`; author `456020`; inbound `True`; parent `1447995`; text: @AmazonHelp Its refunded now.

### Customer `783400`
- `customer` tweet `783416`; author `306987`; inbound `True`; parent `(none)`; text: @115850 7 calls and 2 emails regarding one order to the customer service, still no delivery. Shame on you guys.
- `customer` tweet `783413`; author `306987`; inbound `True`; parent `783416`; text: @115850 Before you ask order tracking id:210166605807 customer email id: __email__
- `AmazonHelp` tweet `783412`; author `AmazonHelp`; inbound `False`; parent `783413`; text: @306987 Date. I request you to kindly wait till then and I'm positive that the order would be delivered. Also, 2/3 ^SB
- `customer` tweet `783409`; author `306987`; inbound `True`; parent `783412`; text: @AmazonHelp My estimated delivery date was 25th October. Should i wait till next year?
- `customer` tweet `783403`; author `306987`; inbound `True`; parent `783409`; text: @AmazonHelp Delivery agent has the audacity to say he won't deliver it today for absurd reasons.
- `AmazonHelp` tweet `783402`; author `AmazonHelp`; inbound `False`; parent `783403`; text: @306987 so we could have a closer look at this. Also, we've forwarded your feedback internally to the appropriate team. 2/2^RS
- `customer` tweet `783400`; author `306987`; inbound `True`; parent `783402`; text: @AmazonHelp Done!! What else. ? Called customer care 8 times , mailed twice. Should I write a postcard now? @115851 should be disappointed in u.

### Customer `1035121`
- `customer` tweet `1035123`; author `364856`; inbound `True`; parent `(none)`; text: I did not receive cashback of1500 INR on using SBI card for buying OnePlus 5 device on Amazon. @115850 @AmazonHelp @115821 . Bad service.
- `customer` tweet `1035121`; author `364856`; inbound `True`; parent `1035123`; text: @115850 @AmazonHelp @115821 No reply yet even after submission of bank statements and filling the form.

### Customer `268182`
- `customer` tweet `268183`; author `179945`; inbound `True`; parent `(none)`; text: 【拡散希望】
『日めくりカレンダー』
ついに御予約開始となります❣️一家に一冊、必携だよ(*^o^*)
よろこんでいきる まいにちひふみん パルコ https://t.co/901Y2uGy3w @116313より
- `customer` tweet `268182`; author `179944`; inbound `True`; parent `268183`; text: @179945 @116313 予約しまーす(⌒‐⌒)♥

### Customer `592154`
- `customer` tweet `592155`; author `260133`; inbound `True`; parent `(none)`; text: Geil. Wird jetzt @116316 zu @39144 und löscht regelkonforme Rezensionen ohne Kommentar und Begründung? Good job 👏
- `AmazonHelp` tweet `592152`; author `AmazonHelp`; inbound `False`; parent `592155`; text: @260133 Hallo, wenn du der Meinung bist, dass deine Rezension fälschlicherweise entfernt wurde, kannst du das gerne von den Kollegen prüfen lassen: https://t.co/ohyvGrpvrY. Aber prüfe bitte vorab unsere Rezensionsrichtlinien: https://t.co/i2ZEbfqIpA. Schönen Gruß ^JS
- `customer` tweet `592154`; author `260133`; inbound `True`; parent `592152`; text: @AmazonHelp Danke! Soeben getan. Denn regelkonform war es zu 100%, das hatte ich schon vor dem Posten gecheckt.

### Customer `2675335`
- `customer` tweet `2675336`; author `753065`; inbound `True`; parent `(none)`; text: @AmazonHelp when I change the format of the Hesit Society Book 1 to kindle. It changes to a completely different title! :/ https://t.co/KozRIqrRWk
- `AmazonHelp` tweet `2675334`; author `AmazonHelp`; inbound `False`; parent `2675336`; text: @753065 That is odd, Tina! I've tried the App and multiple browsers, and all seems well. Have you tried clearing cache/cookies? ^JZ
- `customer` tweet `2675335`; author `753065`; inbound `True`; parent `2675334`; text: @AmazonHelp Nope. Looks the same :/ when I search 4 the xmas title I get 2 different prices. However the top 1 is the heist book 1 when I change formats https://t.co/OhPk0VcsMD

### Customer `939357`
- `customer` tweet `939365`; author `342674`; inbound `True`; parent `(none)`; text: @115821 @AmazonHelp I may just have one of the worst and most disappointing orders with your company. I honestly hope it gets resolve.
- `AmazonHelp` tweet `939364`; author `AmazonHelp`; inbound `False`; parent `939365`; text: @342674 Could you provide us with a few details about the issue without giving personal info? We'd like to help any way we can. ^WM
- `customer` tweet `939355`; author `342674`; inbound `True`; parent `939364`; text: @AmazonHelp Order a collectors edition, said there was a problem with address delivery when everyone of my other orders have been delivered no issue.
- `AmazonHelp` tweet `939353`; author `AmazonHelp`; inbound `False`; parent `939355`; text: @342674 Who is the listed carrier for this recent order? You can review these details here: https://t.co/Y5jpI9gRhE ^WM
- `customer` tweet `939354`; author `342674`; inbound `True`; parent `939353`; text: @AmazonHelp Said it’s sold by you guys.
- `AmazonHelp` tweet `939356`; author `AmazonHelp`; inbound `False`; parent `939354`; text: @342674 When you check the tracking info, who's the carrier? Here's a list of carriers if you need: https://t.co/Ws30Y0VSHM ^DW
- `customer` tweet `939357`; author `342674`; inbound `True`; parent `939356`; text: @AmazonHelp There is no carrier the items been return the only thing I have is he order # and the prices details

### Customer `553403`
- `customer` tweet `551947`; author `248654`; inbound `True`; parent `(none)`; text: @116875 hola, acabo de comprar un Amazon stick y cuando quiero ingresar al contenido prime me aparece esto, ¿cómo lo arreglo? https://t.co/FqtclD8Yc8
- `customer` tweet `551949`; author `248654`; inbound `True`; parent `551947`; text: @116875 hola! ya seguí las instrucciones, básicamente reinicie el stock porque el mando si responde y sigue igual, no puedo ver el contenido prime mismo error 5505.
- `AmazonHelp` tweet `553402`; author `AmazonHelp`; inbound `False`; parent `551949`; text: @248654 En este caso por favor contacta nuestro Servicio al Cliente en este enlace: https://t.co/beR78zMMYB ^JJ
- `customer` tweet `553403`; author `248654`; inbound `True`; parent `553402`; text: @AmazonHelp marque y ya quedó :) el problema era que el país de mis contenidos era en USA  y ajustándolo a México quedó

### Customer `2290290`
- `customer` tweet `2290065`; author `665263`; inbound `True`; parent `(none)`; text: Refund completed for a product on amazon, but still money is not credited to bank accnt. Promised date was 30th Sept.
Amazon accnt:  9160085536
We spoke/mailed to canarabank but no response from the bank.
@115850 @13509 https://t.co/yTKn971kf3
- `customer` tweet `2290066`; author `665263`; inbound `True`; parent `2290065`; text: @AmazonHelp  I did not find the link, can you please send it again.
- `AmazonHelp` tweet `2290289`; author `AmazonHelp`; inbound `False`; parent `2290066`; text: @665263 You may share your details here: https://t.co/GIJyeYqKE0. ^SB
- `customer` tweet `2290290`; author `665263`; inbound `True`; parent `2290289`; text: @AmazonHelp @AmazonHelp  i have shared the details through the link..please look into that.

### Customer `1576244`
- `customer` tweet `1576256`; author `485639`; inbound `True`; parent `(none)`; text: @485640 @174957 @50245 would you please reply? Or don't have any responsibility for the devices sold via @115850. Faulty? https://t.co/CP44oiTfC3
- `customer` tweet `1576255`; author `174957`; inbound `True`; parent `1576256`; text: @485639 @485640 @50245 @115850 Shyam, please reach out to our technical support team at https://t.co/SsyXddhs4E
- `customer` tweet `1576244`; author `485639`; inbound `True`; parent `1576255`; text: @174957 @485640 @50245 @115850 See this, after 3 visit to yr centre based in Lajpat Nagar 2 Delhi, India. They say, they have only this latest os which can be reinstalled https://t.co/R0q3FVuHtI

### Customer `1047210`
- `customer` tweet `1046061`; author `118919`; inbound `True`; parent `(none)`; text: Yay! Amazon has been ranked as the world’s most authentic brand and among the top 3 authentic brands in India by @45958 https://t.co/dzTbCCETaq
- `customer` tweet `1046062`; author `311023`; inbound `True`; parent `1046061`; text: @118919 @45958 Steange....Had an pathetic service from you..both product wise and customer support wise....
- `AmazonHelp` tweet `1047208`; author `AmazonHelp`; inbound `False`; parent `1046062`; text: @311023 It looks like you've had an unpleasant experience with us. Could you please let us know what went wrong? ^OS
- `customer` tweet `1047210`; author `311023`; inbound `True`; parent `1047208`; text: @AmazonHelp Looks like......wow....had I not had an bad experience would I comment like dat...I'm tired of complaining and I hv given up

### Customer `2812785`
- `customer` tweet `2812787`; author `784298`; inbound `True`; parent `(none)`; text: ねえこれ何？？？
Amazonなんか使ってないんだけど
アカウントはあるけど何も買ってないんだけど。
誰かにアカウント悪用されてるのかな？？？かけたほうがいいの？？？ https://t.co/enCIy8aFML
- `AmazonHelp` tweet `2812786`; author `AmazonHelp`; inbound `False`; parent `2812787`; text: @784298 (*´-`).｡oO(こちらは、Amazonからのご請求ではございませんので、ご連絡されませんように。。。)
また、携帯大手3社をご利用の場合には、迷惑メール対策として、申告窓口を設置しています。今後受信しないためにも、各窓口へご申告ください。TY
- `customer` tweet `2812785`; author `784298`; inbound `True`; parent `2812786`; text: @AmazonHelp わかりました。ありがとうございます

### Customer `235115`
- `customer` tweet `235110`; author `115850`; inbound `True`; parent `(none)`; text: Sellers of India are burning the midnight oil to brighten India’s Diwali #thankyousellers https://t.co/y4GZ5JlcTP
- `customer` tweet `235115`; author `214057`; inbound `True`; parent `235110`; text: @115850 Customers like me is struggling without smart phone from last 7 days coz 1 of your fraud seller. Feeling frustrated 1st time in last 6 yrs.

### Customer `1310236`
- `customer` tweet `1310231`; author `426184`; inbound `True`; parent `(none)`; text: @115850  please let me know the correct price of this product. MRP on shoe is Rs. 499 while Rs 999 charged in the invoice. #fraud? https://t.co/lgtRjTi9S0
- `AmazonHelp` tweet `1310229`; author `AmazonHelp`; inbound `False`; parent `1310231`; text: @426184 Please don't provide your order details, we consider it personal information. Our Twitter page is visible to public. ^HA
- `customer` tweet `1310230`; author `426184`; inbound `True`; parent `1310229`; text: @AmazonHelp Please help me out of this,
- `AmazonHelp` tweet `1310232`; author `AmazonHelp`; inbound `False`; parent `1310230`; text: @426184 product belonging to a different batch or different M.R.P.s being used by manufacturers in different regions. (2/2) ^SC
- `customer` tweet `1310234`; author `426184`; inbound `True`; parent `1310232`; text: @AmazonHelp Apart from all these reasons, this is a malpractice and customer exploitation. Please help me asap
- `AmazonHelp` tweet `1310235`; author `AmazonHelp`; inbound `False`; parent `1310234`; text: @426184 I’m sorry about the issue you’re facing. Let us look into it. Please share your details (1/2)^HR
- `customer` tweet `1310236`; author `426184`; inbound `True`; parent `1310235`; text: @AmazonHelp I have already shared the details via link given by Amazon.in

### Customer `222644`
- `customer` tweet `222650`; author `169191`; inbound `True`; parent `(none)`; text: @115850 @AmazonHelp hd placd 1 ordr, nw seller calng continously askng to cancel d ordr as he unabl 2 ship d sm,bt nt cnfrmng d refund amt
- `AmazonHelp` tweet `222649`; author `AmazonHelp`; inbound `False`; parent `222650`; text: @169191 necessary actions to make things right for you. (2/2) ^ST
- `customer` tweet `222648`; author `169191`; inbound `True`; parent `222649`; text: @AmazonHelp Pls update me on this order. Seller is continously calling and harassing 2 cancel the order bt not confirming how much amount he will refund https://t.co/j7zYwW4acN
- `AmazonHelp` tweet `222647`; author `AmazonHelp`; inbound `False`; parent `222648`; text: @169191 I'm sorry you had to face such an ordeal. Please write back to us https://t.co/beaaDm0muc and we'll get back to you soon. (1/2) ^SI
- `customer` tweet `222646`; author `169191`; inbound `True`; parent `222647`; text: @AmazonHelp Written back 2 days ago, still no response!! @115851 @115850
- `AmazonHelp` tweet `222645`; author `AmazonHelp`; inbound `False`; parent `222646`; text: @169191 Apologies, please find the email correspondence here: https://t.co/DTSNmGldJf and revert to us. We'll be glad to help you. ^SI
- `customer` tweet `222644`; author `169191`; inbound `True`; parent `222645`; text: @AmazonHelp Issue is still not resolve fully. When I contacted the seller for refund, he asked me to contact you. Pls refund the full amount ASAP

## Semantic inspection sample

- `clearly related` customer `950268`: @AmazonHelp Thanks. Additional information submitted. I appreciate the help. -> @345386 I can confirm, we have received your information. We will be in contact shortly.  ^AG
- `clearly related` customer `145769`: @AmazonHelp: Hi.  Is there any way to Cancel amazon Prime Trial so I can use it at another time? -> @149064 Hello there! You can definitely cancel your Prime trial at any time, but you will not be able to use the free benefits later. If you don't cancel, you will automatically continue to a paid membership after the trial: https://t.co/vlwG9yh30X. I hope this helps! ^SD
- `clearly related` customer `1369918`: @AmazonHelp They gave me a message "refund is successful" but there was no refund on my fathers bank acc. I immediately contacted the customer service -> @438872 Sorry for the hassle. Please report this to our support team here: https://t.co/vlvfJr4nN9 and we'll check this. ^HN
- `clearly related` customer `1869791`: @AmazonHelp I've chatted with your representatives many many times over the past 2 years about the issues i've been having with deliveries and nothing has been resolved, though i've been reassured each time that it will never happen again. I'll be contacting you guys again tomorrow. -> @558457 Please keep us posted. We want to make sure you're receiving your packages. ^BH
- `clearly related` customer `1135095`: @120533 ou est le colis? Boite aux lettre vide! Et je vais passer par vos 18 services comme la dernière fois pour que vous le trouviez. https://t.co/w01VEBNJsH -> @387416 Bonjour, je vous invite à prendre contact auprès de notre SAV via: https://t.co/hgIrz98cdI afin qu'il fasse le nécessaire.^FT
- `apparently unrelated` customer `277832`: Amazonの返品の仕方がわかりません(＞＜)(＞＜)(＞＜) -> @182355 リプライ失礼いたします、Amazon公式です。返品の手続き方法や返送方法についてご案内したヘルプページがございますので、よろしければご参照ください。https://t.co/E93zubGhpU 
ご不明なことがあればお知らせください HM
- `weakly related` customer `854328`: @AmazonHelp Colissimo non abîmé -> @176366 Je vous informe que vous avez la possibilité d'évaluer l'emballage du colis en utilisant ce lien: https://t.co/fgvoz7708P ^FT
- `clearly related` customer `2888344`: @115850 I think there is some error. Many daily needs products(fmcg goods) have minimum quantity 2. Its very inconvenient. Please change the policy -> @705573 These limits cannot be increased. Items with quantity restrictions have very low prices and/or a limited supply and we want to ensure that many customers are able to order these items. However, as our prices and product supply change, these limits may change too. ^RB
- `clearly related` customer `1366266`: @AmazonHelp All I need to know is where I can take the parcel to send it! Is it to a pass my parcel shop or can I take it to a post office? -> @438057 Sorry, we're unable to access your account via Twitter. Please, use the link below to get further assistance. Take care! ^DA
- `weakly related` customer `863357`: @AmazonHelp my order was apparently delivered and handed to residents yesterday but we haven’t got it?? -> @325012 Hi, sorry to hear that, have you tried the tips from this help page: https://t.co/L76CBge35P? ^JJ
- `clearly related` customer `2545393`: @AmazonHelp When you make such a blunder you shouldn't worry about the order number being made public. Please focus on getting my friend a replacement asap. -> @723491 Thank you for the confirmation. Our support team will look into the concern and update the account holder accordingly. ^AM
- `clearly related` customer `1786091`: @115850 My Amazon account has been hacked. Wanted to speak to a customer service executive for help, but 1800 3000 9009 does not give that option. Kindly help. -> @536624 I'm sorry your account has been hacked. We take these issues seriously. Please share your details here: https://t.co/WOvZ2b2Xe6 and I'll get back to you. ^SH
- `apparently unrelated` customer `2338864`: @115821 cheers! The one package I needed this week you guys have fucked me on. Real good job there you massive bellends! -> @676580 What happened Edward? ^KM
- `weakly related` customer `530728`: @AmazonHelp llamame y te lo cuento -> @242926 Mariajo, por estos medios no contamos con acceso a tu cuenta. Sin embargo te recomendamos entrar en contacto con nuestro Equipo de Servicio al cliente por medio del siguiente enlace: https://t.co/3VUNgKe6KR ^FZ
- `apparently unrelated` customer `1124604`: @AmazonHelp Me han llamado pero no podía cogerlo -> @385171 ¿Cuál es el transportista encargado de la entrega de tu pediod, Zei? ^LG
- `clearly related` customer `520720`: @AmazonHelp Don’t see one. Track Package still says “Expected 30 Nov”. Last update is arrival scan in Richmond at 10:37 last night. -> @240209 I'm sorry for the delay with your package! Please contact us here for assistance: https://t.co/hApLpM3Ejd ^MO
- `clearly related` customer `1031725`: @AmazonHelp please help. @126705 have kept my parcel hostage with no effort to help me or resolve the issue -> @364125 I'm sorry to hear this! When you spoke with Royal Mail, what insight and options were they able to provide you? ^GL
- `apparently unrelated` customer `2870665`: @116875 Hola, necesito ayuda, su centro de atención a clientes no me está dando respuestas ni su área de logística, ¿cómo es posible que una caja de más de 1 metro de dimensiones esté desaparecido? -> @797117 Hola, Albert. Lamento el contratiempo. ¿Qué te indicó nuestro Servicio al Cliente? ¿Qué opciones te brindaron? ^JQ
- `clearly related` customer `2768238`: @AmazonHelp well, i made an order on saturday morning, was put almost instantly in process, and was shipped only today , and is going to arrive on friday.

usually my orders take half the time ... -> @774043 What was the delivery date communicated to you in the order confirmation e-mail please? ^FA
- `clearly related` customer `1115771`: @AmazonHelp I have given all the details..plz look into the matter @117157 @AmazonHelp -> @201415 Thank your for sharing your details, Paul. We'll reach out to you at the earliest. ^SA
- `weakly related` customer `2957011`: @AmazonHelp C’est Amazon Logistics -> @816249 Avez-vous contacté notre service client à ce sujet? Vous a-t-on expliqué la raison de ce retard je vous prie? ^SA
- `apparently unrelated` customer `2192449`: @AmazonHelp Vou aguardar então, obrigado pessoal. 😌 -> @641718 Imagina Gabriel, estamos para lhe ajudar. ^AZ
- `weakly related` customer `2953623`: @AmazonHelp Nope. -> @815508 Hmm... that is odd. I'd like us to look into this further for you! Please reach out here: https://t.co/hApLpMlfHN so we can get this resolved! ^AD
- `clearly related` customer `1843601`: @AmazonHelp Me again! Email says I have to return the damaged book. Surely I shouldn't be inconvienenced for your driver's incompetence? -> @552389 Hi, the book would have to be returned if damaged. Have we provided you with a return label and instructions on how to proceed with the return ? ^CR
- `weakly related` customer `1598917`: @AmazonHelp marketplace - I've just spoken to a member of your team and it's all sorted. Thanks -> @491045 Great ! Do reach out to us if we can help further. Have a great day. ^CR
- `clearly related` customer `902283`: @AmazonHelp It's says 5 to 8 business days. I usually order from Amazon and it never took so long even to start shipping. -> @334206 We may take a longer than you expect to ship out your order. Read more about calculations here: https://t.co/adwVIWHTrn ^TG
- `weakly related` customer `514713`: @AmazonHelp But it hasn’t been delivered, yet we have an email saying it was handed to customer. Seeing as it’s a pocket knife and wasn’t delivered due to no adult being home I’m guessing your driver has kept it? -> @238519 Thanks for filling us in. We want to review and explore available options with you. Please reach out to us here for further assistance: https://t.co/JzP7hlRCV9 ^SH
- `clearly related` customer `2604253`: @AmazonHelp Done all that 

It says delivered to me yet shows this https://t.co/0KJKO3niVS -> @462389 Hey Robert, can you contact us so that we can investigate this further: https://t.co/oGDklGgbCZ? ^PJ
- `weakly related` customer `2522315`: @AmazonHelp I have the email. -> @407433 Can you provided us with the seller? You can find that information here: https://t.co/Y5jpI9gRhE ^LS
- `clearly related` customer `351440`: @115850 Order # 408-2638076-8341900 was cancelled on 26th sep but my refund is still not initiated. Please work asap. Reg No- 8777602446 -> @199602 Don’t provide your order and contact details as its personal information. Our Twitter page is visible to public.(2/2)^RS
- `weakly related` customer `210339`: @115850 @AmazonHelp order no 405-3129805-1022740 . its already been returned . i dont want the product . please initiate the refund -> @165784 We'll surely help you out Kishore. Kindly reach out to our support team here: https://t.co/beaaDm0muc, (1/2)^AP
- `apparently unrelated` customer `420647`: @AmazonHelp Ah, they have different tracking numbers. Does this mean I should expect two deliveries?, and how will I know which is which? -> @215261 It's very possible that both will arrive together, if with the same carrier. ^TP
- `clearly related` customer `574498`: Is @119625 down? Haven't been able to stream a single video all week. -> @255127 Could you kindly elaborate on the issue for us to help you better? Also, what is the exact error you see when you try to stream? ^PB
- `apparently unrelated` customer `606210`: @AmazonHelp 先日半年ぶりくらいにアマゾンで買い物した際、気づかずに登録したのかもしれません。先程プライム退会いたしました。対応ありがとうございます。 -> @264069 左様でございましたか、お手数をおかけいたしました。　よろしければ、今後ともAmazonをどうぞよろしくお願いいたします。　リプライありがとうございました。　SM
- `clearly related` customer `2149515`: Hey @115821 I tried to pick up this box and nearly threw it to the roof 😂😂 https://t.co/J6CxQee7sE -> @631753 Thank you for bringing this to our attention! You can leave packaging feedback here: https://t.co/VU9eQ37klD ^EB
- `weakly related` customer `271245`: today I had to help the amazon delivery guy figure out how to scan the package he was delivering to us. so basically i work for amazon now -> @180713 We'd like to look into this further, please provide your contact info, and order details here: https://t.co/WoLGQdscf6 ^AG
- `clearly related` customer `1727654`: @AmazonHelp That I know but exchange offer showing for my location for lg q6 mobile from 14th to yesterday till 9 pm but post that not showing -> @521664 We understand your concern about exchange, Mayur. Please reach us from here: https://t.co/rS49hgaADF we'll assist you. ^SV
- `apparently unrelated` customer `1714220`: @AmazonHelp @132703 Creo que vosotros sois los que tenéis un contrato con ellos, así que vosotros debéis estar pendientes de que cumplan lo que prometeis. -> @519116 Rachel, ¿el pedido fue gestionado por Amazon o por un vendedor desde nuestro sitio?
- `clearly related` customer `2388895`: @AmazonHelp i have shared all details to __email__. can you pls take details from their and resolve the same. -> @174237 Unfortunately, we would not be able to access your account/order info here. Kindly fill in your details through the link mentioned earlier and we'll reach out to you soon. ^VM
- `apparently unrelated` customer `2720039`: @AmazonHelp びっくり！ご丁寧にありがとうございます！今回はAmazon発送の商品なので出荷明細書が同梱されていると思い込んでおりましたが、付いていない場合も有り得るということですね！？それなら安心しました。 https://t.co/jkUEfenFq3 -> @763265 とんでもないことでございます。どうぞよろしくお願いいたします。TN
- `weakly related` customer `1055268`: @AmazonHelp Thanks for checking the conversation, do help me by fulfilling the commitment done. #AwaitingResolution https://t.co/QsUNlq47l5 -> @369338 Please don't provide your order details, as we consider it to be personal information. Our Twitter page is public.​ ^RW
- `weakly related` customer `2832995`: @115821 what’s up with your site . Trying to place an order and can’t get past the exit quantities page ! -> @788687 Thanks for reaching out to us! Let's troubleshoot! To begin, could you tell us how you're shopping with us? Are you using an app, or are you on a computer? ^TK
- `clearly related` customer `65701`: @AmazonHelp Sorry, I fail to see how pointing me at your self help page is meant to help. May as well just call again. Please take ownership of the case and give me regular updates. While I've got your attention. It would be nice to have a case management section in account details. -> @131036 Hi. The link we provided previously was the "Contact Us" link. As we are unable to access accounts through social media, it is the best means of proceeding. ^DC
- `clearly related` customer `431246`: @AmazonHelp It was pointless. They said if u don't want it anymore. Just return it when u get it. They just reread the return policy -_- -> @204063 Hey Aakash, we strive to deliver by the date given at checkout &amp; I'm sorry if there's been a delay. Please let us know if (1/2)
- `apparently unrelated` customer `2761243`: 昨日Amazonの荷物の中敷き5枚あったんで思い付きでやっつけ仕事でインコにおもちゃ作ったんだけど、目見当で折ったり鋏開いたの刺したりしたわりに良くできたと思う。壊すためのおもちゃだしね！十分。 https://t.co/Pr1KcSEWap -> @772564 |ω・)
Amazonのご利用ありがとうございます！
インコちゃんも、楽しんでいただけそうなおもちゃが完成しましたね～
(*´-`).｡oO(最初見た時に、黒いのが、、、、、ビックリ、、、)TY
- `apparently unrelated` customer `1131222`: @AmazonHelp me responde @AmazonHelp porquê hoje é o último dia da promoção e estou pensando em assinar ela. -> @386196 Olá Varzim o que acontece, é que o valor total de três meses sem promoção é R$ 59,70 (19,90x3). ^HC
- `clearly related` customer `1487324`: @115821 has a good gig. I pay prime, but they don't have to deliver the packages 2nd day because they just cancel my orders. -> @465436 Hey Shawn, I know this can be frustrating. Could you let us know who sold the items? Check here: https://t.co/tiyq2irCcL Thanks!^BA
- `apparently unrelated` customer `423814`: @AmazonHelp Yes I would love to scroll pages instead of flipping them. Please implement this feature.... -> @190607 I get your point, Vivek. I'll be sure to pass this as a feedback internally. ^AR
- `apparently unrelated` customer `1263092`: @AmazonHelp Il mio era un complimento ! -> @415819 Grazie per il tuo riscontro Dario. Qualora necessitassi, siamo a disposizione! A presto! ^MP
- `clearly related` customer `2240667`: @115850 nokia 8 polish blue bajaj no cost emi plz available it on offer -> @415812 I get your concern, I will certainly take your feedback internally to see if we get this available for no cost EMI. Appreciate your understanding. ^BS

## Cross-account contamination

Found **0** contaminated sampled chains (0.00%). Account-marker mentions occurred in **23** chains, but mentions in customer text are not contamination. Markers checked: `home town, @115821, @115850, @115830`.
No unrelated/other-account turn occurred in the sampled recovered chains.

## Coverage Gap suspicious examples

### Tweet `814386`
- Provenance determination: **valid AmazonHelp-linked chain**.
- `customer` tweet `814388`; author `313954`; inbound `True`; parent `(none)`; text: Dear @115821 , Why has the book that I pre-ordered back in May and was released three days ago still not yet shipped? No love, me
- `AmazonHelp` tweet `814385`; author `AmazonHelp`; inbound `False`; parent `814388`; text: @313954 Oh no! We'd like to help. What delivery date were you given? Without revealing account info., can you give us more details? ^SE
- `customer` tweet `814386`; author `313954`; inbound `True`; parent `814385`; text: @AmazonHelp Book was released on 10/17 and the status has been “not yet shipped” since then.
- `AmazonHelp` tweet `814389`; author `AmazonHelp`; inbound `False`; parent `814386`; text: @313954 Some orders ship and arrive in the same day! We do still expect your book to arrive between 10/23 and 10/24 as expected. ^BE

### Tweet `1381536`
- Provenance determination: **valid AmazonHelp-linked chain**.
- `customer` tweet `1381131`; author `441471`; inbound `True`; parent `(none)`; text: @115821 even confirmation for order by Amazon and hometown that my order will be delivered. Both have no clues of my delivered #cheater
- `customer` tweet `1381133`; author `441471`; inbound `True`; parent `1381131`; text: @115821 Ready for dispatch; Order no. 0210232119 for 2 quantity. Thank you for choosing Home Town!For any queries call 18002100004 received on 26/10
- `AmazonHelp` tweet `1381535`; author `AmazonHelp`; inbound `False`; parent `1381133`; text: @441471 Sorry for the inconvenience. Please contact our support team here: https://t.co/vlvfJr4nN9 we will get it resolved. ^GU
- `customer` tweet `1381536`; author `441471`; inbound `True`; parent `1381535`; text: @AmazonHelp My order details Order no. 0210232119 for 2 quantity.
- `AmazonHelp` tweet `1381537`; author `AmazonHelp`; inbound `False`; parent `1381536`; text: @441471 Just to confirm, have you reported this to our support team as requested earlier? If not kindly let them know about it. ^AB

### Tweet `1387233`
- Provenance determination: **valid AmazonHelp-linked chain**.
- `customer` tweet `1387236`; author `442781`; inbound `True`; parent `(none)`; text: @115850 : you people tourchered me lot and latter offer Rs 250 as gift card for all those mental tourchered.
- `customer` tweet `1387234`; author `442781`; inbound `True`; parent `1387236`; text: @115850 Is this what value of your services. Really too much embrassing from me . You just take your piecemeal gift card I don't it.
- `AmazonHelp` tweet `1387231`; author `AmazonHelp`; inbound `False`; parent `1387234`; text: @442781 Sorry for any ordeal, Shweta. Could you let us know what went wrong? We'd like to look into it. ^HD
- `customer` tweet `1387233`; author `442781`; inbound `True`; parent `1387231`; text: @AmazonHelp It's regarding my last order of one plus 5 phone
- `AmazonHelp` tweet `1387235`; author `AmazonHelp`; inbound `False`; parent `1387233`; text: @442781 Sorry for the hassle. Please report this to our support team here: https://t.co/vlvfJr4nN9 and we'll check this. ^HN

### Tweet `2103681`
- Provenance determination: **valid AmazonHelp-linked chain**.
- `customer` tweet `2103681`; author `621113`; inbound `True`; parent `(none)`; text: @115850 pathetic pickup experience for my order # 404-3967148-4720314
Have requested pickup since 1 week and no one shows up, only rescheduling. Calling customer care only rescheduled it further.
- `AmazonHelp` tweet `2103680`; author `AmazonHelp`; inbound `False`; parent `2103681`; text: @621113 Apologies for hassle, I'd like to assist you with this, please fill this form; https://t.co/beaaDm0muc &amp; I’ll contact you soon.^AH

### Tweet `741527`
- Provenance determination: **valid AmazonHelp-linked chain**.
- `customer` tweet `741527`; author `297346`; inbound `True`; parent `(none)`; text: @115830 why am i not getting an email confirmation of my order? plus i sent myself a gift card and that has also not been received. please advise
- `AmazonHelp` tweet `741525`; author `AmazonHelp`; inbound `False`; parent `741527`; text: @297346 Oh no! Have you checked your Spam or Junk folders?  ^CO

## Decisions

- Semantic heuristic sample counts: `{'clearly related': 25, 'apparently unrelated': 13, 'weakly related': 12}`. These are local screening results, not LLM judgments.
- The interim file is **provenance-safe** (100% direct ID validity; 0% unrelated turns in the sampled recovered context), but it is **not safe as an unfiltered golden set**: the local semantic screen found apparently unrelated responses and requires human review/filtering.
- Existing scripts need correction if they treat a referenced row as a customer without checking inbound status, or label every non-inbound ancestor as AmazonHelp. The audit's strict rules should be used before downstream work.

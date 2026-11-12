# Proxy tables (crawl 20261027, 20261027-printdontint; duel ladder_arms.json; 1470 summaries)

Team index k is PROXY_TEAM (k = -1: all twelve pooled). Draft: maps with a lineup, games behind them, the
share of games that used the map's most common lineup, and the pick order for maps without data.

Recall: share of its contact rounds in which the team started a recall; above 0.5 the proxy ends every
turn with a recall and cancels it next turn (PROXY_PERMA_RECALL).

| k | Team | Maps | Games | Modal share | Recall | Fallback order |
|---:|---|---:|---:|---:|---:|---|
| -1 | top | 70 | 8470 | 0.16 | 0.00 | vesper_vale heart_of_ruin vendetta marcella ryth prism varg ren cassi_and_issac tavi stellar willow |
| 0 | Ad Astra | 70 | 680 | 1.00 | 0.01 | heart_of_ruin vesper_vale ryth ren marcella cassi_and_issac |
| 1 | Claudus Maximus | 70 | 750 | 0.64 | 0.01 | vesper_vale heart_of_ruin vendetta marcella varg ryth |
| 2 | Intercontinental Fish | 70 | 770 | 1.00 | 0.01 | vesper_vale vendetta heart_of_ruin cassi_and_issac marcella ren willow tavi |
| 3 | Mite | 70 | 770 | 1.00 | 0.92 | vesper_vale vendetta heart_of_ruin varg marcella cassi_and_issac |
| 4 | NEETCoders | 70 | 735 | 1.00 | 0.97 | heart_of_ruin vendetta marcella vesper_vale ryth cassi_and_issac ren varg |
| 5 | Sponge(Albert and Bob) | 70 | 610 | 0.93 | 0.00 | heart_of_ruin ryth vendetta marcella tavi stellar prism vesper_vale willow ren |
| 6 | Trzy Kwaterki | 70 | 745 | 0.97 | 0.91 | marcella vendetta ryth vesper_vale heart_of_ruin ren varg cassi_and_issac |
| 7 | Univardisty of Shingtonwash | 70 | 488 | 0.73 | 0.00 | marcella heart_of_ruin vesper_vale ren ryth vendetta tavi varg stellar cassi_and_issac prism willow |
| 8 | hello | 70 | 535 | 1.00 | 0.01 | vendetta varg ryth vesper_vale marcella cassi_and_issac heart_of_ruin ren |
| 9 | print dont int | 70 | 847 | 1.00 | 0.94 | vesper_vale heart_of_ruin vendetta marcella ryth |
| 10 | prism best girl | 70 | 770 | 1.00 | 0.01 | prism marcella vesper_vale heart_of_ruin ryth vendetta |
| 11 | willow best girl | 70 | 770 | 0.88 | 0.92 | prism vendetta marcella heart_of_ruin tavi vesper_vale varg |

## Items

Opening milestones (shard: owned count), then the stack; agree = share of the
hero's appearances whose first milestones match the opening.

| k | Team | Hero | Apps | Agree | Opening | Stack |
|---:|---|---|---:|---:|---|---|
| -1 | top | cassi | 221 | 0.63 | power focus 5 > durability focus 5 | bruiser health only |
| -1 | top | heart_of_ruin | 1770 | 0.11 | treasure health 5 > jungle focus 5 > bruiser health 5 > bruiser focus 5 | bruiser focus : durability health = 5:1 |
| -1 | top | issac | 221 | 0.37 | treasure strength 5 > power strength 5 > home health 5 | power strength : durability health = 2:1 |
| -1 | top | marcella | 1764 | 0.12 | treasure focus 5 > durability health 5 > bruiser focus 5 > bruiser focus 10 | bruiser focus only |
| -1 | top | prism | 384 | 0.53 | durability health 5 > monster health 5 > jungle health 5 > home health 5 | bruiser health only |
| -1 | top | ren | 44 | 0.71 | treasure health 5 > bruiser health 5 > jungle focus 5 > durability health 5 | bruiser health only |
| -1 | top | ryth | 1069 | 0.31 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser health only |
| -1 | top | stellar | 76 | 0.71 | treasure focus 5 > power focus 5 > home health 5 > durability health 5 | bruiser health only |
| -1 | top | tavi | 423 | 0.14 | treasure strength 5 > durability health 5 > monster strength 5 > bruiser strength 5 | bruiser strength : bruiser health = 2:1 |
| -1 | top | varg | 223 | 0.30 | jungle strength 5 > treasure strength 5 > bruiser health 5 > durability health 5 | bruiser health only |
| -1 | top | vendetta | 1566 | 0.10 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength only |
| -1 | top | vesper_vale | 1578 | 0.12 | treasure strength 5 > jungle strength 5 > durability health 5 > monster strength 5 | bruiser strength : bruiser health = 1:1 |
| -1 | top | willow | 239 | 0.29 | treasure focus 5 > jungle focus 5 | durability focus : bruiser health = 2:1 |
| 0 | Ad Astra | cassi | 8 | 1.00 | jungle focus 5 | bruiser strength only |
| 0 | Ad Astra | heart_of_ruin | 155 | 1.00 | jungle focus 5 > treasure focus 5 > durability health 5 > bruiser focus 5 | bruiser focus : bruiser health = 2:1 |
| 0 | Ad Astra | issac | 8 | 1.00 | jungle strength 5 > treasure strength 5 | durability health only |
| 0 | Ad Astra | marcella | 155 | 0.85 | jungle focus 5 > treasure focus 5 > durability health 5 > bruiser focus 5 | bruiser health only |
| 0 | Ad Astra | ryth | 131 | 1.00 | jungle health 5 > treasure health 5 > durability health 5 | bruiser health only |
| 0 | Ad Astra | varg | 89 | 1.00 | jungle strength 5 > treasure strength 5 | bruiser strength : durability health = 1:1 |
| 0 | Ad Astra | vesper_vale | 155 | 1.00 | treasure strength 5 > jungle strength 5 > durability health 5 > monster strength 5 | bruiser strength : bruiser health = 1:1 |
| 1 | Claudus Maximus | heart_of_ruin | 180 | 1.00 | treasure health 5 > jungle focus 5 > durability health 5 > bruiser focus 5 | bruiser focus : bruiser health = 2:1 |
| 1 | Claudus Maximus | marcella | 127 | 1.00 | jungle strength 5 > durability health 5 > bruiser focus 5 > bruiser health 5 | bruiser strength : bruiser health = 3:1 |
| 1 | Claudus Maximus | ryth | 69 | 1.00 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength : bruiser health = 3:1 |
| 1 | Claudus Maximus | tavi | 91 | 1.00 | treasure strength 5 > durability health 5 > monster strength 5 | bruiser strength : bruiser health = 3:1 |
| 1 | Claudus Maximus | vendetta | 180 | 0.58 | treasure health 5 > jungle strength 5 > monster strength 5 > durability health 5 | bruiser strength : bruiser health = 2:1 |
| 1 | Claudus Maximus | vesper_vale | 180 | 0.57 | treasure strength 5 > jungle strength 5 > monster strength 5 > durability health 5 | bruiser strength : bruiser health = 2:1 |
| 2 | Intercontinental Fish | cassi | 152 | 0.94 | power focus 5 > durability focus 5 | bruiser health only |
| 2 | Intercontinental Fish | heart_of_ruin | 180 | 0.83 | treasure health 5 > jungle focus 5 > bruiser health 5 > bruiser health 10 | bruiser health only |
| 2 | Intercontinental Fish | issac | 152 | 0.87 | treasure strength 5 > power strength 5 | power strength : home health = 1:1 |
| 2 | Intercontinental Fish | marcella | 96 | 1.00 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength only |
| 2 | Intercontinental Fish | ren | 26 | 1.00 | bruiser health 5 > durability health 5 | power focus only |
| 2 | Intercontinental Fish | varg | 17 | 1.00 | monster strength 5 > jungle health 5 > power strength 5 > power strength 10 | power strength only |
| 2 | Intercontinental Fish | vendetta | 157 | 0.86 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength only |
| 2 | Intercontinental Fish | vesper_vale | 180 | 0.90 | treasure strength 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength only |
| 2 | Intercontinental Fish | willow | 15 | 1.00 | treasure strength 5 > power strength 5 | home health : durability health = 2:1 |
| 3 | Mite | cassi | 26 | 1.00 | treasure focus 5 > jungle focus 5 | bruiser health : durability health = 5:1 |
| 3 | Mite | heart_of_ruin | 185 | 0.81 | treasure health 5 > jungle focus 5 > bruiser health 5 > bruiser focus 5 | bruiser focus : durability health = 5:1 |
| 3 | Mite | issac | 26 | 0.42 | treasure strength 5 > capture strength 5 > power strength 5 > monster strength 5 | bruiser health : durability health = 4:1 |
| 3 | Mite | marcella | 122 | 0.36 | treasure focus 5 > capture focus 5 > jungle focus 5 > monster focus 5 | power focus : bruiser health = 6:1 |
| 3 | Mite | tavi | 122 | 0.19 | treasure health 5 > treasure strength 5 > bruiser strength 5 > monster strength 5 | bruiser strength : bruiser health = 3:1 |
| 3 | Mite | vendetta | 185 | 0.61 | treasure strength 5 > jungle strength 5 > monster strength 5 > bruiser health 5 | bruiser strength : bruiser health = 2:1 |
| 3 | Mite | vesper_vale | 185 | 0.21 | treasure strength 5 > monster strength 5 > power strength 5 > jungle health 5 | bruiser strength : bruiser health = 2:1 |
| 4 | NEETCoders | cassi | 19 | 0.78 | monster focus 5 | power focus : bruiser health = 2:1 |
| 4 | NEETCoders | heart_of_ruin | 165 | 0.54 | hunter health 5 > jungle focus 5 > bruiser health 5 > bruiser health 10 | bruiser health only |
| 4 | NEETCoders | issac | 19 | 1.00 | monster strength 5 > power strength 5 > home health 5 > durability health 5 | bruiser strength only |
| 4 | NEETCoders | marcella | 110 | 0.51 | hunter focus 5 > jungle focus 5 > durability health 5 > bruiser focus 5 | bruiser focus : bruiser health = 2:1 |
| 4 | NEETCoders | ryth | 83 | 0.81 | jungle health 5 > monster health 5 > durability health 5 > bruiser health 5 | bruiser strength : bruiser health = 2:1 |
| 4 | NEETCoders | varg | 19 | 1.00 | monster strength 5 > power strength 5 > home health 5 > durability health 5 | bruiser strength only |
| 4 | NEETCoders | vendetta | 164 | 0.50 | hunter strength 5 > jungle strength 5 > durability health 5 > bruiser strength 5 | bruiser health only |
| 4 | NEETCoders | vesper_vale | 161 | 0.52 | hunter strength 5 > jungle health 5 > durability health 5 > bruiser strength 5 | bruiser strength : bruiser health = 2:1 |
| 5 | Sponge(Albert and Bob) | heart_of_ruin | 154 | 0.73 | treasure focus 5 > power focus 5 > durability health 5 > home health 5 | bruiser health only |
| 5 | Sponge(Albert and Bob) | marcella | 154 | 1.00 | treasure health 5 > jungle strength 5 > durability strength 5 > bruiser health 5 | bruiser health only |
| 5 | Sponge(Albert and Bob) | prism | 21 | 1.00 | treasure focus 5 | power focus : home health = 2:1 |
| 5 | Sponge(Albert and Bob) | ren | 15 | 1.00 | treasure health 5 > bruiser health 5 > jungle focus 5 > durability health 5 | bruiser health only |
| 5 | Sponge(Albert and Bob) | ryth | 178 | 0.82 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser health only |
| 5 | Sponge(Albert and Bob) | stellar | 51 | 1.00 | treasure focus 5 > power focus 5 > home health 5 > durability health 5 | bruiser health only |
| 5 | Sponge(Albert and Bob) | varg | 7 | 1.00 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength : bruiser health = 1:1 |
| 5 | Sponge(Albert and Bob) | vendetta | 95 | 1.00 | treasure health 5 > jungle strength 5 > durability strength 5 > bruiser health 5 | bruiser health : power health = 2:1 |
| 5 | Sponge(Albert and Bob) | vesper_vale | 10 | 1.00 | treasure strength 5 > jungle strength 5 > bruiser strength 5 > durability health 5 | power strength only |
| 5 | Sponge(Albert and Bob) | willow | 83 | 1.00 | treasure focus 5 > jungle focus 5 | durability focus : bruiser health = 2:1 |
| 6 | Trzy Kwaterki | heart_of_ruin | 114 | 0.15 | prospector health 5 > treasure focus 5 > durability health 5 > bruiser focus 5 | bruiser health : monster health = 6:1 |
| 6 | Trzy Kwaterki | marcella | 180 | 0.08 | prospector focus 5 > treasure health 5 > jungle focus 5 > bruiser health 5 | bruiser health only |
| 6 | Trzy Kwaterki | ryth | 180 | 0.15 | prospector health 5 > treasure focus 5 > bruiser health 5 | bruiser health : jungle health = 6:1 |
| 6 | Trzy Kwaterki | tavi | 10 | 0.17 | prospector health 5 > treasure focus 5 > jungle health 5 > bruiser strength 5 | bruiser focus : durability health = 1:1 |
| 6 | Trzy Kwaterki | varg | 13 | 1.00 | prospector strength 5 | treasure health : monster health = 3:1 |
| 6 | Trzy Kwaterki | vendetta | 180 | 0.14 | prospector health 5 > treasure strength 5 > jungle health 5 > monster strength 5 | bruiser strength : bruiser health = 1:1 |
| 6 | Trzy Kwaterki | vesper_vale | 152 | 0.25 | prospector strength 5 > treasure strength 5 > jungle strength 5 > monster health 5 | bruiser strength : bruiser health = 1:1 |
| 7 | Univardisty of Shingtonwash | cassi | 14 | 0.40 | treasure focus 5 > bruiser health 5 > durability focus 5 | power focus : bruiser health = 4:1 |
| 7 | Univardisty of Shingtonwash | heart_of_ruin | 101 | 0.61 | treasure focus 5 > bruiser health 5 > durability health 5 > bruiser health 10 | bruiser health only |
| 7 | Univardisty of Shingtonwash | issac | 14 | 0.78 | jungle strength 5 > treasure strength 5 > bruiser health 5 > durability health 5 | bruiser health only |
| 7 | Univardisty of Shingtonwash | marcella | 106 | 0.47 | treasure strength 5 > bruiser health 5 > durability health 5 > bruiser health 10 | bruiser health only |
| 7 | Univardisty of Shingtonwash | prism | 28 | 0.50 | jungle focus 5 > treasure focus 5 > power focus 5 > durability health 5 | power focus : bruiser health = 6:1 |
| 7 | Univardisty of Shingtonwash | ryth | 63 | 0.55 | jungle strength 5 > treasure strength 5 > bruiser health 5 > durability health 5 | bruiser health only |
| 7 | Univardisty of Shingtonwash | stellar | 25 | 0.78 | jungle focus 5 > treasure focus 5 > power focus 5 > durability health 5 | power focus only |
| 7 | Univardisty of Shingtonwash | tavi | 38 | 0.42 | treasure focus 5 > bruiser health 5 > durability focus 5 > bruiser health 10 | power focus only |
| 7 | Univardisty of Shingtonwash | varg | 76 | 0.55 | jungle strength 5 > treasure strength 5 > bruiser health 5 > durability health 5 | bruiser health only |
| 7 | Univardisty of Shingtonwash | vendetta | 51 | 0.43 | jungle strength 5 > treasure strength 5 > power strength 5 > durability health 5 | bruiser health only |
| 7 | Univardisty of Shingtonwash | vesper_vale | 89 | 0.65 | treasure strength 5 > power strength 5 > durability health 5 > bruiser health 5 | power strength only |
| 7 | Univardisty of Shingtonwash | willow | 27 | 0.55 | treasure strength 5 > bruiser health 5 > durability health 5 > bruiser health 10 | power strength only |
| 8 | hello | marcella | 150 | 0.35 | treasure focus 5 > jungle strength 5 > monster strength 5 > bruiser strength 5 | bruiser focus : bruiser health = 1:1 |
| 8 | hello | ryth | 121 | 0.33 | treasure health 5 > jungle strength 5 > bruiser health 5 > durability health 5 | bruiser strength : bruiser health = 1:1 |
| 8 | hello | tavi | 148 | 0.27 | bruiser strength 5 > durability health 5 > monster strength 5 > treasure strength 5 | bruiser strength : bruiser health = 4:1 |
| 8 | hello | vendetta | 148 | 0.31 | treasure strength 5 > jungle strength 5 > durability strength 5 > bruiser health 5 | bruiser strength : bruiser health = 2:1 |
| 8 | hello | vesper_vale | 91 | 0.35 | treasure strength 5 > power strength 5 > durability health 5 > jungle health 5 | bruiser strength : bruiser health = 2:1 |
| 9 | print dont int | heart_of_ruin | 210 | 1.00 | treasure focus 5 > power focus 5 > home health 5 > durability health 5 | bruiser focus : bruiser health = 4:1 |
| 9 | print dont int | marcella | 210 | 1.00 | treasure focus 5 > durability health 5 > bruiser focus 5 > bruiser focus 10 | bruiser focus only |
| 9 | print dont int | ryth | 122 | 0.68 | treasure health 5 > durability health 5 > bruiser strength 5 | bruiser strength : bruiser health = 3:1 |
| 9 | print dont int | vendetta | 169 | 0.59 | treasure strength 5 > durability health 5 > bruiser strength 5 > bruiser strength 10 | bruiser strength : bruiser health = 2:1 |
| 9 | print dont int | vesper_vale | 210 | 0.97 | treasure strength 5 > power strength 5 > durability health 5 > bruiser strength 5 | bruiser strength : bruiser health = 3:1 |
| 10 | prism best girl | heart_of_ruin | 149 | 0.95 | jungle focus 5 > bruiser health 5 > durability health 5 > bruiser focus 5 | bruiser health only |
| 10 | prism best girl | marcella | 169 | 0.98 | bruiser strength 5 > bruiser health 5 > bruiser focus 5 > bruiser strength 10 | bruiser health only |
| 10 | prism best girl | prism | 187 | 0.99 | durability health 5 > monster health 5 > jungle health 5 > home health 5 | bruiser health only |
| 10 | prism best girl | ryth | 122 | 0.97 | jungle strength 5 > bruiser health 5 > durability health 5 > power strength 5 | power strength only |
| 10 | prism best girl | vendetta | 52 | 1.00 | jungle strength 5 > bruiser strength 5 > bruiser health 5 > durability health 5 | bruiser strength : bruiser health = 1:1 |
| 10 | prism best girl | vesper_vale | 165 | 0.98 | jungle strength 5 > bruiser strength 5 > bruiser health 5 > durability health 5 | bruiser strength : bruiser health = 1:1 |
| 11 | willow best girl | heart_of_ruin | 175 | 0.19 | hunter focus 5 > jungle focus 5 > bruiser focus 5 > bruiser focus 10 | bruiser focus only |
| 11 | willow best girl | marcella | 185 | 0.11 | prospector focus 5 > jungle focus 5 > bruiser focus 5 > bruiser focus 10 | bruiser focus only |
| 11 | willow best girl | prism | 148 | 0.19 | monster focus 5 > bruiser focus 5 > bruiser focus 10 > jungle health 5 | bruiser focus only |
| 11 | willow best girl | tavi | 10 | 0.33 | prospector strength 5 > hunter strength 5 > monster strength 5 > jungle strength 5 | bruiser strength : bruiser health = 4:1 |
| 11 | willow best girl | vendetta | 185 | 0.27 | hunter health 5 > monster strength 5 > jungle strength 5 > power strength 5 | power strength : durability health = 6:1 |
| 11 | willow best girl | willow | 114 | 0.40 | jungle strength 5 > power strength 5 | power strength : durability health = 6:1 |

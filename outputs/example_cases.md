# Example cases (test split)

## Successes
### Q312495_1950_P166 — Andrei Grechko
- missing year: 1950 (hidden type: award)
- context: 1945: received Order of Lenin | 1945: received Order of Suvorov, 1st class | 1957: began serving as Commander-in-Chief of the Russian Ground Forces | 1958: received Hero of the Soviet Union
  - [ ] A (same_type_near_year, p=0.170): received Order of San Marino
  - [ ] B (same_type_near_year, p=0.157): received Hughes Medal
  - [ ] C (same_person_wrong_time, p=0.169): received Hero of the Czechoslovak Socialist Republic
  - [ ] D (same_type_random, p=0.157): received list of Swimming World Swimmers of the Year
  - [✓] E (correct, p=0.175): received Order of the Red Banner
  - [ ] F (label_similar_same_type, p=0.172): received Order the Red Banner
- point: E; sets: 0.80→{A,C,E,F}; 0.90→{A,C,E,F}; 0.95→{A,B,C,D,E,F}

### Q655494_1967_P166 — Yuri Ozerov
- missing year: 1967 (hidden type: award)
- context: 1945: received Order of the Red Banner | 1965: received Honored art worker of the Russian Soviet Federative Socialist Republic | 1971: received Order of Lenin | 1972: received Grand Star of People's Friendship
  - [ ] A (same_type_near_year, p=0.177): received Guggenheim Fellowship
  - [ ] B (same_person_wrong_time, p=0.173): received Medal "For Battle Merit"
  - [ ] C (label_similar_same_type, p=0.176): received Commander of the order of Honour
  - [✓] D (correct, p=0.183): received Order of the Badge of Honour
  - [ ] E (same_type_random, p=0.157): received Eisner Award for Best Writer
  - [ ] F (same_type_near_year, p=0.135): received Golden Globe Award for Best Actress in a Motion Picture – Musical or Comedy
- point: D; sets: 0.80→{A,B,C,D}; 0.90→{A,B,C,D}; 0.95→{A,B,C,D,E}

### Q974542_1916_P166 — Jan Syrový
- missing year: 1916 (hidden type: award)
- context: 1915: received Order of St. George, 4th class | 1915: received Order of Saint Stanislaus, 3rd class | 1917: received Order of Saint Anna, 4th class | 1919: received Knight Commander of the Order of the Bath
  - [ ] A (same_type_near_year, p=0.171): received Cross of Military Merit with Red Decoration
  - [✓] B (correct, p=0.171): received Order of St. Vladimir, 4th class
  - [ ] C (same_person_wrong_time, p=0.165): received Grand Cordon of the order of Nichan Iftikhar
  - [ ] D (same_type_near_year, p=0.168): received Cross of St. George 2nd class
  - [ ] E (label_similar_same_type, p=0.160): received Order of St. Vladimir, 1st class
  - [ ] F (same_type_random, p=0.164): received Grand Cross of the Order of Charles III
- point: B; sets: 0.80→{A,B,C,D,F}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q229369_2002_P166 — Lois McMaster Bujold
- missing year: 2002 (hidden type: award)
- context: 1995: received Hugo Award for Best Novel | 1995: received Locus Award for Best Science Fiction Novel | 2004: received Hugo Award for Best Novel | 2004: received Locus Award for Best Fantasy Novel
  - [ ] A (same_person_wrong_time, p=0.166): received Edward E. Smith Memorial Award
  - [ ] B (same_type_random, p=0.171): received Harvey Award for Best Colorist
  - [✓] C (correct, p=0.174): received Mythopoeic Fantasy Award for Adult Literature
  - [ ] D (same_type_near_year, p=0.154): received AVN Award Female Foreign Performer of the Year
  - [ ] E (same_type_near_year, p=0.164): received Coretta Scott King Award
  - [ ] F (label_similar_same_type, p=0.170): received Mythopoeic Fantasy Award for Children's Literature
- point: C; sets: 0.80→{A,B,C,E,F}; 0.90→{A,B,C,E,F}; 0.95→{A,B,C,D,E,F}

### Q6698469_2017_P39 — Lucy Powell
- missing year: 2017 (hidden type: position)
- context: 2015: began serving as member of the 56th Parliament of the United Kingdom | 2015: began serving as Shadow Secretary of State for Education | 2019: began serving as member of the 58th Parliament of the United Kingdom | 2020: began serving as Shadow Minister for Business and Consumers
  - [ ] A (same_type_random, p=0.172): began serving as member of the French National Assembly
  - [ ] B (same_person_wrong_time, p=0.156): began serving as Shadow Minister for the Cabinet Office
  - [ ] C (same_type_near_year, p=0.164): began serving as Minister for Sustainability, Environment and Conservation
  - [ ] D (same_type_near_year, p=0.169): began serving as Minister of Agriculture and Agri-Food
  - [✓] E (correct, p=0.177): began serving as member of the 57th Parliament of the United Kingdom
  - [ ] F (label_similar_same_type, p=0.162): began serving as member of the 15th Parliament of the United Kingdom
- point: E; sets: 0.80→{A,C,D,E}; 0.90→{A,C,D,E,F}; 0.95→{A,B,C,D,E,F}

## Failures
### Q18687923_2012_P166 — Ingrid Scheffer
- missing year: 2012 (hidden type: award)
- context: 2005: began working for University of Melbourne | 2011: began working for Florey Institute of Neuroscience and Mental Health | 2014: received Prime Minister's Prize for Science | 2014: received Fellow of the Australian Academy of Science
  - [ ] A (label_similar_same_type, p=0.159): received North Carolina Award for Science
  - [ ] B (same_type_near_year, p=0.173): received Warren Alpert Foundation Prize
  - [ ] C (same_person_wrong_time, p=0.177): received Fellow of the Australian Academy of Health and Medical Sciences
  - [ ] D (same_type_random, p=0.152): received Golden Mask
  - [ ] E (same_type_near_year, p=0.178): received honorary doctorate of the University of Tirana
  - [✓] F (correct, p=0.161): received L'Oréal-UNESCO Award For Women in Science
- point: E; sets: 0.80→{B,C,E}; 0.90→{A,B,C,E,F}; 0.95→{A,B,C,D,E,F}

### Q4444966_1917_P108 — Mikhail Subbotin
- missing year: 1917 (hidden type: employment)
- context: 1912: began working for University of Warsaw | 1915: began studying at Rostov State University | 1922: began working for Ulugh Beg Astronomical Institute | 1922: began working for National University of Uzbekistan named after Mirzo Ulugbek
  - [ ] A (same_type_random, p=0.166): began working for Jordanhill College
  - [ ] B (same_type_near_year, p=0.159): began working for University of Padua
  - [ ] C (same_person_wrong_time, p=0.184): received Order of the Red Banner of Labour
  - [ ] D (same_type_near_year, p=0.162): began working for First Australian Imperial Force
  - [ ] E (label_similar_same_type, p=0.169): began working for California State Polytechnic University, Pomona
  - [✓] F (correct, p=0.159): began working for Platov South-Russian State Polytechnic University
- point: C; sets: 0.80→{A,C,E}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q6168998_1999_P69 — Jean-Baptiste Soufron
- missing year: 1999 (hidden type: education)
- context: 1997: began studying at University of Limoges | 2001: began studying at Robert Schuman University | 2001: began studying at Centre for International Intellectual Property Studies
  - [ ] A (same_person_wrong_time, p=0.166): began studying at Panthéon-Assas University Paris
  - [ ] B (same_type_random, p=0.176): began studying at Cégep de Rimouski
  - [ ] C (same_type_near_year, p=0.170): began studying at University of Rochester
  - [✓] D (correct, p=0.163): began studying at University of Paris 1 Pantheon-Sorbonne
  - [ ] E (label_similar_same_type, p=0.166): began studying at University of Paderborn
  - [ ] F (same_type_near_year, p=0.159): began studying at University of London
- point: B; sets: 0.80→{A,B,C,D,E}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q1392426_1998_P166 — Philaret
- missing year: 1998 (hidden type: award)
- context: 1988: received Honorary Diploma of the Presidium of the Supreme Soviet of the RSFSR | 1995: received Medal of Francysk Skaryna | 2003: received Order "For Merit to the Fatherland", 4th class | 2003: received Order of Francisc Skorina
  - [ ] A (same_type_near_year, p=0.166): received Honorary Knight Grand Cross of the Order of the Bath
  - [ ] B (label_similar_same_type, p=0.170): received Order of Fatherland
  - [ ] C (same_type_random, p=0.164): received FIFA FIFPro World XI
  - [ ] D (same_person_wrong_time, p=0.166): received honorary citizen of Polotsk
  - [ ] E (same_type_near_year, p=0.166): received Engler Medal in Gold
  - [✓] F (correct, p=0.168): received Order of Fatherland 3rd Class
- point: B; sets: 0.80→{A,B,C,D,E,F}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q42786_1987_P166 — Audrey Hepburn
- missing year: 1987 (hidden type: award)
- context: 1968: received Special Tony Award | 1980: received star on Hollywood Walk of Fame | 1988: began serving as UNICEF Goodwill Ambassador | 1989: received Golden Globe Cecil B. DeMille Award
  - [ ] A (same_person_wrong_time, p=0.140): received Presidential Medal of Freedom
  - [ ] B (same_type_near_year, p=0.174): received Prix Laure Bataillon
  - [ ] C (same_type_near_year, p=0.177): received honorary doctorate from Princeton University
  - [✓] D (correct, p=0.176): received Commandeur des Arts et des Lettres
  - [ ] E (same_type_random, p=0.158): received Golden Mask
  - [ ] F (label_similar_same_type, p=0.176): received Chevalier des Arts et des Lettres
- point: C; sets: 0.80→{B,C,D,F}; 0.90→{B,C,D,E,F}; 0.95→{B,C,D,E,F}

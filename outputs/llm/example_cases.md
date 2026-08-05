# Example cases (test split)

## Successes
### Q4444966_1917_P108 — Mikhail Subbotin
- missing year: 1917 (hidden type: employment)
- context: 1912: began working for University of Warsaw | 1915: began studying at Rostov State University | 1922: began working for Ulugh Beg Astronomical Institute | 1922: began working for National University of Uzbekistan named after Mirzo Ulugbek
  - [ ] A (same_type_random, p=0.060): began working for Jordanhill College
  - [ ] B (same_type_near_year, p=0.060): began working for University of Padua
  - [ ] C (same_person_wrong_time, p=0.340): received Order of the Red Banner of Labour
  - [ ] D (same_type_near_year, p=0.050): began working for First Australian Imperial Force
  - [ ] E (label_similar_same_type, p=0.040): began working for California State Polytechnic University, Pomona
  - [✓] F (correct, p=0.450): began working for Platov South-Russian State Polytechnic University
- point: F; sets: 0.80→{C,F}; 0.90→{C,F}; 0.95→{C,F}

### Q17714_1982_P166 — Stephen Hawking
- missing year: 1982 (hidden type: award)
- context: 1979: began serving as Lucasian Professor of Mathematics | 1981: received Franklin Medal | 1985: received Gold Medal of the Royal Astronomical Society | 1987: received IOP Dirac Medal
  - [✓] A (correct, p=0.720): received Commander of the Order of the British Empire
  - [ ] B (same_type_near_year, p=0.050): received London Film Critics Circle Award for Director of the Year
  - [ ] C (same_person_wrong_time, p=0.080): received Fellow of the Royal Society
  - [ ] D (same_type_random, p=0.060): received Pour le Mérite for Sciences and Arts order
  - [ ] E (same_type_near_year, p=0.050): received James Tait Black Memorial Prize
  - [ ] F (label_similar_same_type, p=0.040): received Dame Commander of the Order of the British Empire
- point: A; sets: 0.80→{A}; 0.90→{A}; 0.95→{A}

### Q116966_1932_P108 — Georges de Rham
- missing year: 1932 (hidden type: employment)
- context: 1926: began studying at University of Paris | 1930: began studying at University of Göttingen | 1936: began working for University of Geneva | 1944: began serving as chairperson
  - [✓] A (correct, p=0.350): began working for University of Lausanne
  - [ ] B (label_similar_same_type, p=0.030): began working for University of Lagos
  - [ ] C (same_type_random, p=0.130): began working for Royal Aircraft Establishment
  - [ ] D (same_person_wrong_time, p=0.100): received doctor honoris causa from the University of Grenoble
  - [ ] E (same_type_near_year, p=0.220): began working for University of Rennes
  - [ ] F (same_type_near_year, p=0.170): began working for Physico-Mathematical Institute of the Russian Academy of Sciences
- point: A; sets: 0.80→{A,E}; 0.90→{A,C,E,F}; 0.95→{A,C,E,F}

### Q126107514_2016_P108 — Omkhar Arasaratnam
- missing year: 2016 (hidden type: employment)
- context: 2012: began working for Toronto-Dominion Bank | 2014: began working for Deutsche Bank | 2018: began working for JPMorgan Chase | 2018: began working for New York University Tandon School of Engineering
  - [ ] A (same_type_near_year, p=0.020): began working for Sambalpur University
  - [ ] B (same_type_near_year, p=0.020): began working for London School of Hygiene and Tropical Medicine
  - [✓] C (correct, p=0.550): began working for Credit Suisse
  - [ ] D (label_similar_same_type, p=0.150): began working for Crédit Lyonnais
  - [ ] E (same_type_random, p=0.030): began working for Sara Lee Corporation
  - [ ] F (same_person_wrong_time, p=0.230): began working for IBM
- point: C; sets: 0.80→{C,F}; 0.90→{C,D,F}; 0.95→{C,D,F}

### Q655494_1967_P166 — Yuri Ozerov
- missing year: 1967 (hidden type: award)
- context: 1945: received Order of the Red Banner | 1965: received Honored art worker of the Russian Soviet Federative Socialist Republic | 1971: received Order of Lenin | 1972: received Grand Star of People's Friendship
  - [ ] A (same_type_near_year, p=0.060): received Guggenheim Fellowship
  - [ ] B (same_person_wrong_time, p=0.180): received Medal "For Battle Merit"
  - [ ] C (label_similar_same_type, p=0.070): received Commander of the order of Honour
  - [✓] D (correct, p=0.580): received Order of the Badge of Honour
  - [ ] E (same_type_random, p=0.030): received Eisner Award for Best Writer
  - [ ] F (same_type_near_year, p=0.080): received Golden Globe Award for Best Actress in a Motion Picture – Musical or Comedy
- point: D; sets: 0.80→{D}; 0.90→{B,D}; 0.95→{B,D}

## Failures
### Q18687923_2012_P166 — Ingrid Scheffer
- missing year: 2012 (hidden type: award)
- context: 2005: began working for University of Melbourne | 2011: began working for Florey Institute of Neuroscience and Mental Health | 2014: received Prime Minister's Prize for Science | 2014: received Fellow of the Australian Academy of Science
  - [ ] A (label_similar_same_type, p=0.050): received North Carolina Award for Science
  - [ ] B (same_type_near_year, p=0.080): received Warren Alpert Foundation Prize
  - [ ] C (same_person_wrong_time, p=0.500): received Fellow of the Australian Academy of Health and Medical Sciences
  - [ ] D (same_type_random, p=0.030): received Golden Mask
  - [ ] E (same_type_near_year, p=0.090): received honorary doctorate of the University of Tirana
  - [✓] F (correct, p=0.250): received L'Oréal-UNESCO Award For Women in Science
- point: C; sets: 0.80→{C,F}; 0.90→{C,F}; 0.95→{C,F}

### Q6168998_1999_P69 — Jean-Baptiste Soufron
- missing year: 1999 (hidden type: education)
- context: 1997: began studying at University of Limoges | 2001: began studying at Robert Schuman University | 2001: began studying at Centre for International Intellectual Property Studies
  - [ ] A (same_person_wrong_time, p=0.320): began studying at Panthéon-Assas University Paris
  - [ ] B (same_type_random, p=0.030): began studying at Cégep de Rimouski
  - [ ] C (same_type_near_year, p=0.050): began studying at University of Rochester
  - [✓] D (correct, p=0.300): began studying at University of Paris 1 Pantheon-Sorbonne
  - [ ] E (label_similar_same_type, p=0.050): began studying at University of Paderborn
  - [ ] F (same_type_near_year, p=0.250): began studying at University of London
- point: A; sets: 0.80→{A,D,F}; 0.90→{A,D,F}; 0.95→{A,D,F}

### Q1392426_1998_P166 — Philaret
- missing year: 1998 (hidden type: award)
- context: 1988: received Honorary Diploma of the Presidium of the Supreme Soviet of the RSFSR | 1995: received Medal of Francysk Skaryna | 2003: received Order "For Merit to the Fatherland", 4th class | 2003: received Order of Francisc Skorina
  - [ ] A (same_type_near_year, p=0.050): received Honorary Knight Grand Cross of the Order of the Bath
  - [ ] B (label_similar_same_type, p=0.080): received Order of Fatherland
  - [ ] C (same_type_random, p=0.030): received FIFA FIFPro World XI
  - [ ] D (same_person_wrong_time, p=0.550): received honorary citizen of Polotsk
  - [ ] E (same_type_near_year, p=0.240): received Engler Medal in Gold
  - [✓] F (correct, p=0.050): received Order of Fatherland 3rd Class
- point: D; sets: 0.80→{D,E}; 0.90→{D,E}; 0.95→{D,E}

### Q42786_1987_P166 — Audrey Hepburn
- missing year: 1987 (hidden type: award)
- context: 1968: received Special Tony Award | 1980: received star on Hollywood Walk of Fame | 1988: began serving as UNICEF Goodwill Ambassador | 1989: received Golden Globe Cecil B. DeMille Award
  - [ ] A (same_person_wrong_time, p=0.300): received Presidential Medal of Freedom
  - [ ] B (same_type_near_year, p=0.030): received Prix Laure Bataillon
  - [ ] C (same_type_near_year, p=0.100): received honorary doctorate from Princeton University
  - [✓] D (correct, p=0.280): received Commandeur des Arts et des Lettres
  - [ ] E (same_type_random, p=0.020): received Golden Mask
  - [ ] F (label_similar_same_type, p=0.270): received Chevalier des Arts et des Lettres
- point: A; sets: 0.80→{A,D,F}; 0.90→{A,D,F}; 0.95→{A,D,F}

### Q312495_1950_P166 — Andrei Grechko
- missing year: 1950 (hidden type: award)
- context: 1945: received Order of Lenin | 1945: received Order of Suvorov, 1st class | 1957: began serving as Commander-in-Chief of the Russian Ground Forces | 1958: received Hero of the Soviet Union
  - [ ] A (same_type_near_year, p=0.030): received Order of San Marino
  - [ ] B (same_type_near_year, p=0.020): received Hughes Medal
  - [ ] C (same_person_wrong_time, p=0.150): received Hero of the Czechoslovak Socialist Republic
  - [ ] D (same_type_random, p=0.020): received list of Swimming World Swimmers of the Year
  - [✓] E (correct, p=0.390): received Order of the Red Banner
  - [ ] F (label_similar_same_type, p=0.390): received Order the Red Banner
- point: F; sets: 0.80→{E,F}; 0.90→{C,E,F}; 0.95→{C,E,F}

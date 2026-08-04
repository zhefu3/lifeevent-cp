# Example cases (test split)

## Successes
### Q441178_1961_P108 — Raymond Smullyan
- missing year: 1961 (hidden type: employment)
- context: 1957: began studying at Princeton University | 1958: began working for Princeton University | 1968: began working for City University of New York | 1982: began working for Indiana University
  - [ ] A (same_type_random, p=0.030): began working for Grupo Salinas
  - [ ] B (same_type_near_year, p=0.030): began working for Howard School of Academics and Technology
  - [ ] C (same_person_wrong_time, p=0.150): began studying at University of Chicago
  - [✓] D (correct, p=0.450): began working for Yeshiva University
  - [ ] E (label_similar_same_type, p=0.120): began working for Sophia University
  - [ ] F (same_type_near_year, p=0.220): began working for Krantz Films, Inc.
- point: D; sets: 0.80→{D}; 0.90→{C,D,F}; 0.95→{C,D,E,F}

### Q5548717_1978_P39 — Ger Connolly
- missing year: 1978 (hidden type: position)
- context: 1977: began serving as Teachta Dála | 1977: began serving as Representative of the Parliamentary Assembly of the Council of Europe | 1979: began serving as Minister of State at the Department of Housing, Local Government and Heritage | 1981: began serving as Teachta Dála
  - [✓] A (correct, p=0.400): began serving as substitute member of the Parliamentary Assembly of the Council of Europe
  - [ ] B (same_type_near_year, p=0.030): began serving as member of the Indiana House of Representatives
  - [ ] C (same_type_near_year, p=0.060): began serving as Secretary of State for Business, Innovation, Science and Trade
  - [ ] D (same_type_random, p=0.200): began serving as Minister for Energy
  - [ ] E (same_type_near_year, p=0.050): began serving as procurador en Cortes
  - [ ] F (label_similar_same_type, p=0.260): began serving as Observer of the Parliamentary Assembly of the Council of Europe
- point: A; sets: 0.80→{A,F}; 0.90→{A,D,F}; 0.95→{A,D,F}

### Q1333582_1987_P166 — Richard Wilbur
- missing year: 1987 (hidden type: award)
- context: 1983: received Drama Desk Special Award | 1983: received PEN Translation Prize | 1988: received Laurence Olivier Award for Best New Musical | 1989: received Pulitzer Prize for Poetry
  - [ ] A (same_type_random, p=0.010): received Silver Slugger Award
  - [ ] B (same_person_wrong_time, p=0.080): received Guggenheim Fellowship
  - [ ] C (same_type_near_year, p=0.030): received Grand Officer of the Legion of Honour
  - [✓] D (correct, p=0.750): received United States Poet Laureate
  - [ ] E (label_similar_same_type, p=0.050): received Young People's Poet Laureate
  - [ ] F (same_type_near_year, p=0.080): received Priestley Medal
- point: D; sets: 0.80→{D}; 0.90→{D}; 0.95→{B,D,F}

### Q1251707_1975_P39 — Doug Bereuter
- missing year: 1975 (hidden type: position)
- context: 1967: began serving as director | 1968: began serving as bureaucrat | 1979: began serving as United States representative | 1981: began serving as United States representative
  - [ ] A (same_type_near_year, p=0.030): began serving as Secretary of State for Business, Innovation, Science and Trade
  - [✓] B (correct, p=0.650): began serving as Nebraska Legislature
  - [ ] C (same_person_wrong_time, p=0.100): began serving as urban planner
  - [ ] D (same_type_near_year, p=0.070): began serving as ambassador of Spain to France
  - [ ] E (label_similar_same_type, p=0.100): began serving as Member of the Legislative Yuan
  - [ ] F (same_type_random, p=0.050): began serving as Secretary of State for Health and Social Care
- point: B; sets: 0.80→{B}; 0.90→{B}; 0.95→{B,C,D,E}

### Q1687846_1975_P39 — Jerry Kleczka
- missing year: 1975 (hidden type: position)
- context: 1969: began serving as member of the Wisconsin State Assembly | 1970: began studying at University of Wisconsin–Milwaukee | 1980: began serving as delegate | 1984: began serving as United States representative
  - [✓] A (correct, p=0.850): began serving as member of the State Senate of Wisconsin
  - [ ] B (label_similar_same_type, p=0.030): began serving as member of the State Senate of Wyoming
  - [ ] C (same_type_near_year, p=0.030): began serving as president of Germany
  - [ ] D (same_type_near_year, p=0.050): began serving as United States senator
  - [ ] E (same_type_near_year, p=0.020): began serving as Shadow Leader of the House of Commons
  - [ ] F (same_type_random, p=0.020): began serving as Minister for Finance (Ireland)
- point: A; sets: 0.80→{A}; 0.90→{A}; 0.95→{A}

## Failures
### Q2093915_2010_P166 — Pierre Rosanvallon
- missing year: 2010 (hidden type: award)
- context: 2004: began working for Le Monde | 2008: received honorary doctor of the Queen Mary University of London | 2012: received honorary degree of HEC Paris | 2012: received International Spinoza Prize
  - [ ] A (label_similar_same_type, p=0.200): received Grand Officer of the Legion of Honour
  - [ ] B (same_person_wrong_time, p=0.300): received Corresponding Fellow of the British Academy
  - [ ] C (same_type_random, p=0.030): received Tony Award for Best Actor in a Play
  - [ ] D (same_type_near_year, p=0.030): received Screen Actors Guild Award for Outstanding Performance by a Female Actor in a Drama Series
  - [ ] E (same_type_near_year, p=0.240): received Fellow of the Royal Society of Edinburgh
  - [✓] F (correct, p=0.200): received Officer of the Legion of Honour
- point: B; sets: 0.80→{B,E}; 0.90→{A,B,E,F}; 0.95→{A,B,E,F}

### Q7789484_2007_P108 — Thomas F Krauss
- missing year: 2007 (hidden type: employment)
- context: 1997: began working for California Institute of Technology | 2000: began working for University of St Andrews | 2012: began working for University of York | 2022: received Young Medal and Prize
  - [ ] A (label_similar_same_type, p=0.200): began working for RheinMain University of Applied Sciences
  - [ ] B (same_type_random, p=0.080): began working for Estonian Academy of Arts
  - [ ] C (same_person_wrong_time, p=0.200): began studying at University of Glasgow
  - [✓] D (correct, p=0.200): began working for Karlsruhe University of Applied Sciences
  - [ ] E (same_type_near_year, p=0.120): began working for University of Skövde
  - [ ] F (same_type_near_year, p=0.200): began working for Royal Society of Chemistry
- point: F; sets: 0.80→{}; 0.90→{A,C,D,F}; 0.95→{A,B,C,D,E,F}

### Q61095374_1987_P108 — Cliona O'Farrelly
- missing year: 1987 (hidden type: employment)
- context: 1985: began working for University of Sussex | 1990: began working for Trinity College, Dublin | 1991: began working for Scripps Research
  - [ ] A (same_type_near_year, p=0.200): began working for University of Michigan
  - [ ] B (same_person_wrong_time, p=0.250): began working for University College Dublin
  - [ ] C (same_type_near_year, p=0.100): began working for Vatican Museums
  - [ ] D (label_similar_same_type, p=0.150): began working for Howard University
  - [✓] E (correct, p=0.150): began working for Harvard University
  - [ ] F (same_type_random, p=0.150): began working for Arizona State University
- point: B; sets: 0.80→{B}; 0.90→{A,B,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q2685_2023_P166 — Arnold Schwarzenegger
- missing year: 2023 (hidden type: award)
- context: 2015: received Goldene Kamera | 2022: received Bavarian TV Awards | 2024: received honorary doctorate
  - [ ] A (same_person_wrong_time, p=0.030): received Nickelodeon Kids' Choice Awards
  - [ ] B (same_type_near_year, p=0.350): received Knight Grand Cross with Collar of the Order of Merit of the Italian Republic
  - [✓] C (correct, p=0.050): received White Cross "HONOR ET GLORIA"
  - [ ] D (same_type_random, p=0.200): received Officer of the Order of Australia
  - [ ] E (label_similar_same_type, p=0.300): received Silver Cross of Merit
  - [ ] F (same_type_near_year, p=0.070): received Sporting News Men's College Basketball Player of the Year
- point: B; sets: 0.80→{B,E}; 0.90→{B,D,E}; 0.95→{B,D,E,F}

### Q76357_1997_P166 — Jürgen Habermas
- missing year: 1997 (hidden type: award)
- context: 1994: received Fellow of the British Academy | 1995: received Karl Jaspers Prize | 1999: received Theodor Heuss Award | 2000: received Helmholtz Medal
  - [ ] A (same_type_random, p=0.100): received Knight of Justice of the Order of Saint John
  - [ ] B (same_person_wrong_time, p=0.280): received Geschwister-Scholl-Preis
  - [ ] C (same_type_near_year, p=0.100): received Berlin-Brandenburg Academy Award
  - [ ] D (same_type_near_year, p=0.220): received Austrian Decoration for Science and Art
  - [✓] E (correct, p=0.150): received honorary doctor of Paris 8 University
  - [ ] F (label_similar_same_type, p=0.150): received honorary doctor of Paris Dauphine University
- point: B; sets: 0.80→{B}; 0.90→{B,D,E,F}; 0.95→{A,B,C,D,E,F}

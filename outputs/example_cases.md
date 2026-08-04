# Example cases (test split)

## Successes
### Q61095374_1987_P108 — Cliona O'Farrelly
- missing year: 1987 (hidden type: employment)
- context: 1985: began working for University of Sussex | 1990: began working for Trinity College, Dublin | 1991: began working for Scripps Research
  - [ ] A (same_type_near_year, p=0.153): began working for University of Michigan
  - [ ] B (same_person_wrong_time, p=0.165): began working for University College Dublin
  - [ ] C (same_type_near_year, p=0.169): began working for Vatican Museums
  - [ ] D (label_similar_same_type, p=0.151): began working for Howard University
  - [✓] E (correct, p=0.198): began working for Harvard University
  - [ ] F (same_type_random, p=0.164): began working for Arizona State University
- point: E; sets: 0.80→{B,C,E,F}; 0.90→{B,C,E,F}; 0.95→{A,B,C,D,E,F}

### Q1004154_1983_P108 — Frédéric Barbier
- missing year: 1983 (hidden type: employment)
- context: 1976: began serving as Director of the Municipal Library of Valenciennes | 1982: began working for National Center for Scientific Research | 1991: began working for University Lille-II | 1993: began working for École pratique des hautes études
  - [✓] A (correct, p=0.178): began working for University of Paris 1 Pantheon-Sorbonne
  - [ ] B (same_type_near_year, p=0.161): began working for University of California, Santa Cruz
  - [ ] C (same_person_wrong_time, p=0.161): began studying at École des chartes
  - [ ] D (same_type_near_year, p=0.167): began working for Mario Negri Institute for Pharmacological Research
  - [ ] E (same_type_random, p=0.174): began working for Lycée Fustel-de-Coulanges (Strasbourg)
  - [ ] F (label_similar_same_type, p=0.159): began working for University of Saint Katherine
- point: A; sets: 0.80→{A,B,C,D,E}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q17714_1981_P166 — Stephen Hawking
- missing year: 1981 (hidden type: award)
- context: 1979: received Albert Einstein Medal | 1979: began serving as Lucasian Professor of Mathematics | 1982: received Commander of the Order of the British Empire | 1985: received Gold Medal of the Royal Astronomical Society
  - [✓] A (correct, p=0.178): received Franklin Medal
  - [ ] B (same_type_random, p=0.163): received Silver Bear Grand Jury Prize
  - [ ] C (label_similar_same_type, p=0.168): received Frink Medal
  - [ ] D (same_type_near_year, p=0.160): received Gold medal with hero rank of GDR
  - [ ] E (same_person_wrong_time, p=0.175): received Albert Einstein Award
  - [ ] F (same_type_near_year, p=0.156): received American Music Award for Favorite Pop/Rock Album
- point: A; sets: 0.80→{A,B,C,D,E}; 0.90→{A,B,C,D,E}; 0.95→{A,B,C,D,E,F}

### Q47755_2006_P166 — Imre Kertész
- missing year: 2006 (hidden type: award)
- context: 2005: received honorary doctor of the Sorbonne Nouvelle University | 2005: received Honorary doctor of the Free University of Berlin | 2007: received Marion Samuel Prize | 2009: received Jean Améry award
  - [ ] A (same_type_near_year, p=0.154): received BBC World Sport Star of the Year
  - [ ] B (label_similar_same_type, p=0.176): received Oersted Medal
  - [✓] C (correct, p=0.176): received Ernst Reuter Medal
  - [ ] D (same_type_random, p=0.145): received Laurence Olivier Award for Best Actor
  - [ ] E (same_person_wrong_time, p=0.175): received Kossuth Prize
  - [ ] F (same_type_near_year, p=0.173): received Meldola Medal and Prize
- point: C; sets: 0.80→{B,C,E,F}; 0.90→{B,C,E,F}; 0.95→{A,B,C,E,F}

### Q1679925_1915_P69 — James Emman Kwegyir Aggrey
- missing year: 1915 (hidden type: education)
- context: 1912: began studying at Livingstone College | 1914: began studying at Livingstone College | 1924: began working for Achimota School | 1924: began serving as vice-principal
  - [✓] A (correct, p=0.178): began studying at Columbia University
  - [ ] B (same_type_near_year, p=0.159): began studying at University of Bologna
  - [ ] C (same_type_near_year, p=0.166): began studying at Beijing No. 2 Experimental Primary School
  - [ ] D (same_type_random, p=0.164): began studying at New York Studio School of Drawing, Painting and Sculpture
  - [ ] E (label_similar_same_type, p=0.165): began studying at Colgate University
  - [ ] F (same_type_near_year, p=0.167): began studying at Köllnisches Gymnasium
- point: A; sets: 0.80→{A,C,D,E,F}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

## Failures
### Q441178_1961_P108 — Raymond Smullyan
- missing year: 1961 (hidden type: employment)
- context: 1957: began studying at Princeton University | 1958: began working for Princeton University | 1968: began working for City University of New York | 1982: began working for Indiana University
  - [ ] A (same_type_random, p=0.170): began working for Grupo Salinas
  - [ ] B (same_type_near_year, p=0.162): began working for Howard School of Academics and Technology
  - [ ] C (same_person_wrong_time, p=0.165): began studying at University of Chicago
  - [✓] D (correct, p=0.168): began working for Yeshiva University
  - [ ] E (label_similar_same_type, p=0.168): began working for Sophia University
  - [ ] F (same_type_near_year, p=0.167): began working for Krantz Films, Inc.
- point: A; sets: 0.80→{A,B,C,D,E,F}; 0.90→{A,B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q2093915_2010_P166 — Pierre Rosanvallon
- missing year: 2010 (hidden type: award)
- context: 2004: began working for Le Monde | 2008: received honorary doctor of the Queen Mary University of London | 2012: received honorary degree of HEC Paris | 2012: received International Spinoza Prize
  - [ ] A (label_similar_same_type, p=0.177): received Grand Officer of the Legion of Honour
  - [ ] B (same_person_wrong_time, p=0.174): received Corresponding Fellow of the British Academy
  - [ ] C (same_type_random, p=0.142): received Tony Award for Best Actor in a Play
  - [ ] D (same_type_near_year, p=0.165): received Screen Actors Guild Award for Outstanding Performance by a Female Actor in a Drama Series
  - [ ] E (same_type_near_year, p=0.169): received Fellow of the Royal Society of Edinburgh
  - [✓] F (correct, p=0.173): received Officer of the Legion of Honour
- point: A; sets: 0.80→{A,B,D,E,F}; 0.90→{A,B,D,E,F}; 0.95→{A,B,D,E,F}

### Q5548717_1978_P39 — Ger Connolly
- missing year: 1978 (hidden type: position)
- context: 1977: began serving as Teachta Dála | 1977: began serving as Representative of the Parliamentary Assembly of the Council of Europe | 1979: began serving as Minister of State at the Department of Housing, Local Government and Heritage | 1981: began serving as Teachta Dála
  - [✓] A (correct, p=0.169): began serving as substitute member of the Parliamentary Assembly of the Council of Europe
  - [ ] B (same_type_near_year, p=0.184): began serving as member of the Indiana House of Representatives
  - [ ] C (same_type_near_year, p=0.154): began serving as Secretary of State for Business, Innovation, Science and Trade
  - [ ] D (same_type_random, p=0.160): began serving as Minister for Energy
  - [ ] E (same_type_near_year, p=0.162): began serving as procurador en Cortes
  - [ ] F (label_similar_same_type, p=0.171): began serving as Observer of the Parliamentary Assembly of the Council of Europe
- point: B; sets: 0.80→{A,B,E,F}; 0.90→{A,B,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q1333582_1987_P166 — Richard Wilbur
- missing year: 1987 (hidden type: award)
- context: 1983: received Drama Desk Special Award | 1983: received PEN Translation Prize | 1988: received Laurence Olivier Award for Best New Musical | 1989: received Pulitzer Prize for Poetry
  - [ ] A (same_type_random, p=0.153): received Silver Slugger Award
  - [ ] B (same_person_wrong_time, p=0.167): received Guggenheim Fellowship
  - [ ] C (same_type_near_year, p=0.184): received Grand Officer of the Legion of Honour
  - [✓] D (correct, p=0.164): received United States Poet Laureate
  - [ ] E (label_similar_same_type, p=0.169): received Young People's Poet Laureate
  - [ ] F (same_type_near_year, p=0.163): received Priestley Medal
- point: C; sets: 0.80→{B,C,D,E,F}; 0.90→{B,C,D,E,F}; 0.95→{A,B,C,D,E,F}

### Q1251707_1975_P39 — Doug Bereuter
- missing year: 1975 (hidden type: position)
- context: 1967: began serving as director | 1968: began serving as bureaucrat | 1979: began serving as United States representative | 1981: began serving as United States representative
  - [ ] A (same_type_near_year, p=0.163): began serving as Secretary of State for Business, Innovation, Science and Trade
  - [✓] B (correct, p=0.169): began serving as Nebraska Legislature
  - [ ] C (same_person_wrong_time, p=0.171): began serving as urban planner
  - [ ] D (same_type_near_year, p=0.169): began serving as ambassador of Spain to France
  - [ ] E (label_similar_same_type, p=0.184): began serving as Member of the Legislative Yuan
  - [ ] F (same_type_random, p=0.143): began serving as Secretary of State for Health and Social Care
- point: E; sets: 0.80→{A,B,C,D,E}; 0.90→{A,B,C,D,E}; 0.95→{A,B,C,D,E}

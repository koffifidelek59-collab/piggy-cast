# Synthèse de recherche : quels indicateurs du Climate Impact Explorer (CIE) pour le Niger ?

**Méthode.** Google Scholar bloque l'accès depuis cet environnement. La recherche a donc porté sur les mêmes
bases académiques, interrogées via un moteur de recherche : revues à comité de lecture (Nature, ERL,
Earth's Future, PLOS ONE…), dépôts IRD, CIRAD et KIT, publications WASCAL et rapports d'attribution
(World Weather Attribution). Les résultats viennent des résumés et des notices bibliographiques. Avant de
citer un chiffre précis, ouvrez l'article via le DOI indiqué.

---

## 1. Ce que WASCAL apporte

- **WASCAL** (*West African Science Service Centre on Climate Change and Adapted Land Use*) est le centre de
  recherche climat financé par l'Allemagne et 12 pays d'Afrique de l'Ouest.
- **Au Niger**, WASCAL est présent à l'**Université Abdou Moumouni de Niamey** (programme doctoral
  *Climate Change & Energy*).

Trois travaux affiliés à WASCAL sont directement utiles :

| Étude | Affiliation WASCAL | Ce qu'elle dit | Indicateur CIE soutenu |
|---|---|---|---|
| **Sylla et al. (2018)**, *Earth's Future* 6(7), 1029–1044. DOI 10.1029/2018EF000873 | M. B. Sylla, WASCAL Ouagadougou ; A. Faye, programme WASCAL | Dès 1,5–2 °C de réchauffement mondial, plus de 50 % de la population de la majeure partie de l'Afrique de l'Ouest serait en inconfort thermique saisonnier. De nouvelles zones « à risque pour la plupart des habitants » apparaissent au Sahel. L'étude utilise des **indices de chaleur (heat index)**. | **Days per year with dangerous heat risk (HI > 40 °C)** |
| **Mohamed, Salack, Mkuhlani, Chemura et al. (2025)**, *PLOS ONE* 20(10), e0333963 | S. Salack, WASCAL Competence Center | Modèle CERES-Millet, calibré au Niger (Goungoubon, Fandou) sur 3 zones agroécologiques et 2015–2100. Les rendements de **mil** baissent dans la plupart des scénarios ; les pertes maximales surviennent sous SSP5-8.5 en 2075–2100. | **Area under severe drought (SPEI < -1.5)**, pour son effet sur les cultures |
| **Salack et al. (2014)**, *Climate Dynamics* | S. Salack, aujourd'hui chercheur WASCAL | Les **poches de sécheresse** en saison des pluies (plus de 2 semaines sans pluie après les premières pluies) sont fortement liées aux pertes de rendement au Sahel. L'étude s'appuie sur 43 stations, dont 12 au Niger. | **Consecutive Dry Days** (voir la mise en garde §3) |

Autres sources solides, non WASCAL :

| Source | Ce qu'elle dit | Indicateur CIE soutenu |
|---|---|---|
| **Diedhiou et al. (2018)**, *ERL* 13, 065020 | Le Sahel central et oriental, donc le Niger, se réchauffe **plus vite que la moyenne mondiale**. Les vagues de chaleur y deviennent plus fréquentes et plus longues. | Chaleur |
| **Taylor et al. (2017)**, *Nature* 544, 475–478 | La fréquence des orages sahéliens extrêmes a **triplé depuis 1982**, en lien avec la hausse des températures. Les modèles sous-estiment cette intensification. | **Annual Maximum 5-day Precipitation** |
| **World Weather Attribution (2022)** | Le changement climatique a rendu les pluies meurtrières de 2022 (Niger, Nigeria, Tchad) **environ 80 fois plus probables**. | Pluies extrêmes |
| **World Weather Attribution (2024)** | La vague de chaleur sahélienne d'avril 2024 aurait été **impossible** sans le réchauffement actuel (1,2 °C). | Chaleur |
| **Klutse et al. (2018)**, *ERL* 13, 055013 | Les jours secs consécutifs augmentent à 1,5 et 2 °C, surtout sur la côte guinéenne. | Consecutive Dry Days |
| **Banque mondiale (2022)**, CCDR G5 Sahel | PIB du Niger en 2050 : de −2,2 % (scénario humide) à −11,9 % (scénario sec). | Argument économique |

---

## 2. Proposition finale : 3 indicateurs, tous disponibles dans le CIE

| # | Indicateur CIE (menu exact) | Pourquoi pour le Niger | Appui scientifique |
|---|---|---|---|
| **1** | Heat → **Days per year with dangerous heat risk (HI > 40 °C)** | C'est le signal le plus robuste. Plus de 80 % des actifs travaillent dehors, avec peu d'électricité et de climatisation. | Sylla et al. 2018 (WASCAL) ; Diedhiou et al. 2018 ; WWA 2024 |
| **2** | Drought → **Area under severe drought (SPEI < -1.5)** | Le SPEI tient compte de l'évaporation : il mesure l'effet de la chaleur sur les sols et les pâturages, même si la pluie change peu. Il touche directement le mil et le sorgho, et donc la sécurité alimentaire. | Mohamed et al. 2025 (WASCAL) ; Sultan et al. 2013 |
| **3** | Extreme precipitation → **Annual Maximum 5-day Precipitation** | C'est l'aléa à l'origine des inondations de Niamey et de la vallée du fleuve (2020 ; 2024 : 339 morts). | Taylor et al. 2017 ; WWA 2022 |

**Ce sont les trois indicateurs déjà utilisés dans la note.** La recherche les confirme et leur donne une
base scientifique plus solide. La note cite maintenant Sylla et al. 2018, Mohamed et al. 2025, Taylor et al.
2017 et les deux études WWA.

### Indicateur complémentaire possible
**Labour productivity → Labour Productivity Loss due to Heat Stress.** Il chiffre directement le coût
économique de la chaleur. Il peut remplacer l'indicateur 1 si vous voulez un argument plus économique ; dans
ce cas, il faut réécrire la ligne 1 du tableau.

---

## 3. Indicateurs à éviter, et pourquoi (argument de « Judgment »)

| Indicateur CIE | Pourquoi l'écarter |
|---|---|
| **Maize / Rice / Soy Yields** | Ce ne sont pas les aliments de base du Niger (mil, sorgho, niébé). Ils donneraient une image trompeuse. |
| **Consecutive Dry Days (Annual)** | **Piège :** au Sahel, le maximum annuel de jours secs consécutifs mesure surtout la longueur de la **saison sèche** (7 à 9 mois sans pluie), et non les poches de sécheresse pendant la saison des pluies, qui détruisent les récoltes. Il n'a de sens que si le menu *Temporal average* propose une saison (par exemple juin–août ou JJA). |
| **Mean Air Temperature** | Ce n'est pas un impact : un décideur ne voit pas ce que « +2 °C de moyenne » change concrètement. |
| **Length of the fire season / Fire weather** | C'est un risque secondaire au Niger par rapport à la chaleur, la sécheresse et les inondations. |
| **River Discharge** | Le débit du fleuve Niger à Niamey dépend surtout des pluies en amont (Guinée, Mali). La moyenne nationale est difficile à interpréter. |

---

## 4. Pour l'outil : réglages et relevés

- **Réglages :** Niger ; Scenario **NGFS below 2 degree** ; Alternative **NGFS current policies** ; Annual ;
  Area-weighted average.
- **Valeurs à relever :** aujourd'hui (≈ 2020) et 2100 pour chaque scénario, avec la bande hachurée (bouton
  **Download** pour les chiffres exacts).
- **Graphique :** capture du graphique chaleur, à enregistrer sous `latex/cie_figure.png`.

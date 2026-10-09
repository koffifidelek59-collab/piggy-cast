# Devoir 1 — Niger : guide pour le Climate Impact Explorer et la note LaTeX

Fichier de la note : `latex/niger_climate_memo.tex`, en anglais. Les éléments surlignés en jaune dans le PDF
sont les seules valeurs à compléter.

## Réglages communs aux 3 indicateurs

| Champ | Valeur |
|---|---|
| Country | **Niger** (laissez *Province* vide) |
| Scenario | **NGFS below 2 degree** |
| Alternative scenario | **NGFS current policies** |
| Temporal average | **Annual** |
| Spatial aggregation method | **Area-weighted average** |

## Les 3 indicateurs retenus

| # | Catégorie → indicateur | Macros dans le .tex | Unité |
|---|---|---|---|
| 1 | Heat → **Days per year with dangerous heat risk (HI > 40 °C)** | `\HeatNow`, `\HeatLow`, `\HeatHigh` | jours |
| 2 | Drought → **Area under severe drought (SPEI < -1.5)** | `\DroughtNow`, `\DroughtLow`, `\DroughtHigh` | % de la superficie |
| 3 | Extreme precipitation → **Annual Maximum 5-day Precipitation** | `\RainNow`, `\RainLow`, `\RainHigh` | mm |

Pour chaque indicateur, relevez :

- **Now** : la valeur de la première année du graphique (≈ 2020) ;
- **Low** : la valeur en **2100** avec *NGFS below 2 degree* (courbe médiane) ;
- **High** : la valeur en **2100** avec *NGFS current policies* ;
- **…Range** : le bas et le haut de la bande hachurée en 2100, par exemple `85--140`.

Le plus précis est le bouton **Download** de chaque graphique (fichier de données) : les valeurs exactes y
figurent.

## Le graphique

Faites une capture du graphique **Heat** (les deux courbes visibles, avec la légende) et enregistrez-la sous
`latex/cie_figure.png`. Si les bandes hachurées **se chevauchent** en 2100, remplacez `\bandsseparatetrue`
par `\bandsseparatefalse`.

## Finaliser

1. Remplissez `\AuthorName` et `\CIEAccessDate`.
2. Passez `\finalfalse` à `\finaltrue`.
3. Compilez (Overleaf → pdfLaTeX).
4. Vérifiez : 2 pages, plus la page de références, et aucun « ?? ».
5. Remettez le PDF.

## Pourquoi ces 3 indicateurs (argument de « Judgment »)

- **Chaleur dangereuse** : c'est le signal le plus robuste, et la majorité des actifs travaillent dehors,
  sans climatisation.
- **Sécheresse sévère (SPEI)** : l'indice tient compte de l'évaporation. Il montre donc l'effet de la chaleur
  sur les sols et les pâturages, même si la pluie change peu.
- **Pluies extrêmes sur 5 jours** : elles sont à l'origine des inondations de Niamey et de la vallée du fleuve
  (2020, 2024).
- **Rendements de maïs, riz et soja écartés** : ce ne sont pas les aliments de base du Niger (mil, sorgho).
  La note le dit explicitement.

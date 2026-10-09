# Devoir 1 — Niger : guide pour finaliser la note LaTeX (≈ 30–45 min)

Fichier principal : `latex/niger_climate_memo.tex`, en anglais. Le PDF actuel
(`latex/niger_climate_memo.pdf`) est un **aperçu** : les éléments surlignés en jaune sont les seules valeurs
à compléter. Ce sont les chiffres du **Climate Impact Explorer (CIE)**, inaccessible depuis l'environnement
où la note a été préparée, plus votre nom. Inventer ces chiffres coûterait le critère « Accuracy ».

## 1. Compiler

- **Overleaf (le plus simple)** : *New Project > Upload Project*, puis importez `niger_climate_memo.tex`
  (et plus tard `cie_figure.png`). Compilateur : **pdfLaTeX**, réglage par défaut.
- **En local** : lancez `pdflatex niger_climate_memo.tex` deux fois.

## 2. Remplir les valeurs : un seul bloc à modifier

Toutes les valeurs sont regroupées **en haut du fichier .tex**, dans le bloc
`CLIMATE IMPACT EXPLORER VALUES`. Le texte, le tableau et la légende se mettent à jour automatiquement.

```latex
\newcommand{\HeatLow}{\todo{??}}         % devient par exemple  \newcommand{\HeatLow}{4.2}
\newcommand{\HeatLowRange}{\todo{??--??}} % devient par exemple  \newcommand{\HeatLowRange}{2.1--6.0}
```

Site : <https://climate-impact-explorer.climateanalytics.org>, pays **Niger**, vue par **niveaux de
réchauffement** (*warming levels*). Relevez la **médiane** (le chiffre) et la **bande colorée** (la fourchette)
à **1,5 °C** et à **3 °C** :

| Macros | Indicateur CIE | Si l'indicateur n'existe pas |
|---|---|---|
| `\HeatLow…`, `\HeatHigh…` | *Land area annually exposed to heatwaves* (%) | *Hot days* / jours > 35 °C |
| `\CropLow…`, `\CropHigh…` | *Land area annually exposed to crop failures* (%) | *Land area exposed to droughts* |
| `\FloodLow…`, `\FloodHigh…` | *Population annually exposed to river floods* (%) | *Annual expected damage from river floods* (% du PIB) |

Si vous changez d'indicateur ou d'unité, modifiez aussi le libellé en italique de la 1re colonne du tableau
et la phrase correspondante du *Key message*.

Si vous préférez comparer des **scénarios** (« 1.5 °C pathway » contre « Current policies » vers 2050 ou 2100) :
modifiez `\newcommand{\high}{3\degC}` et la ligne en italique *Source: …* au-dessus du tableau.

Remplissez aussi `\AuthorName` et `\CIEAccessDate`.

## 3. Ajouter le graphique (obligatoire)

1. Faites une capture du graphique CIE de l'indicateur **crop failure**, avec les deux courbes visibles.
2. Enregistrez-la sous **`cie_figure.png`** dans le même dossier que le `.tex` (ou importez-la dans Overleaf).
   Elle remplace automatiquement le cadre gris.
3. Regardez les bandes d'incertitude :
   - si le bas de la bande à 3 °C reste **au-dessus** du haut de la bande à 1,5 °C, laissez `\bandsseparatetrue` ;
   - si les bandes **se chevauchent**, remplacez par `\bandsseparatefalse`.

   La légende s'adapte toute seule. C'est exactement la compétence « communiquer l'incertitude » évaluée.

## 4. Si les données surprennent

- **L'exposition aux pertes de récoltes change peu :** mettez la chaleur en avant dans le *Key message* et
  présentez les cultures comme un risque « incertain mais à fort enjeu ».
- **Les crues baissent à 3 °C :** dites-le. Les modèles divergent sur les pluies au Sahel, et la section
  *What the evidence does, and does not, say* le prépare déjà.

## 5. Avant de remettre

- [ ] Passez `\finalfalse` à **`\finaltrue`**. Le surlignage disparaît ; s'il reste un « ?? » dans le PDF,
      une valeur a été oubliée.
- [ ] Vérifiez qu'il y a toujours **2 pages** avant les références. Si le graphique fait déborder, réduisez
      `height=6.6cm` dans `\includegraphics`.
- [ ] Remettez le **PDF** dans « Assignment 1. Due Oct 14 ».

## Correspondance avec la grille d'évaluation

| Critère | Ce qui y répond dans la note |
|---|---|
| **Accuracy** | Médiane et fourchette CIE ; chaque chiffre externe est sourcé ; les pertes de PIB sont présentées comme une fourchette entre scénarios (−2,2 % à −11,9 %), pas comme une prévision. |
| **Judgment** | Indicateurs choisis pour le Niger : travail en plein air, mil et sorgho pluviaux, vallée du fleuve et Niamey. Les rendements de maïs ou de blé, peu pertinents ici, sont écartés. |
| **Analysis** | Chaque impact est relié à des personnes et des secteurs précis ; une chaîne de risques en cascade ; les limites de l'adaptation (Sultan et al., 2013). |
| **Communication** | *Key message* en tête, tableau lisible en 30 secondes, une seule figure avec une légende qui dit quoi regarder, position de négociation concrète. |

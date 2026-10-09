# Devoir 1 — Niger : il ne reste qu'à mettre votre nom

La note `latex/niger_climate_memo.tex` contient maintenant **vos vraies données du Climate Impact Explorer**
(fichiers CSV téléchargés le 9 octobre 2026, copiés dans `donnees_cie/`). Le graphique est votre capture
`1.png`, copiée sous `latex/cie_figure.png`.

## Pour finaliser (5 minutes)

1. Dans le haut du `.tex`, remplacez `\todo{Your name}` par votre nom :
   `\newcommand{\AuthorName}{Prénom Nom}`.
2. Remplacez `\finalfalse` par `\finaltrue`.
3. Compilez : sur Overleaf, importez `niger_climate_memo.tex` **et** `cie_figure.png`, avec le compilateur
   pdfLaTeX ; en local, lancez `pdflatex` deux fois.
4. Remettez le PDF dans « Assignment 1. Due Oct 14 ».

## Chiffres utilisés

Médiane des modèles ; entre crochets, la fourchette 5–95 %.

| Indicateur | Aujourd'hui (2020) | Below 2 °C, 2050 / 2100 | Current policies, 2050 / 2100 | Net Zero 2050 (1,5 °C), 2100 |
|---|---|---|---|---|
| Jours de chaleur dangereuse (HI > 40 °C) | 31 [25–38] | 45 [33–69] / 42 [29–72] | 54 [41–84] / 91 [59–134] | 32 [24–50] |
| Superficie avec au moins 1 mois de sécheresse sévère (SPEI < -1,5) | 84 % [72–97] | 98 % / 98 % [81–100] | ≈100 % / 100 % [98–100] | 87 % [66–100] |
| Pluie maximale sur 5 jours (variation par rapport à 1995–2014) | +8 % [−7 ; +29] | +18 % / +17 % [−1 ; +54] | +24 % / +43 % [+5 ; +110] | +9 % |

Réchauffement mondial en 2100 : 1,6 °C (Below 2 °C), 2,9 °C (Current policies), 1,3 °C (Net Zero 2050).

Les cartes (fichiers `*_vs_*.csv`) montrent qu'à 2 °C de réchauffement mondial, comparé à 1 °C, la hausse des
jours de chaleur dangereuse est d'environ **+44 jours dans le sud** (au sud de 15° N, où vit la majorité de la
population), contre **+21 jours dans le nord**.

## Ce que révèlent vos données (et comment la note l'exploite)

- **Chaleur :** c'est la plus grande perte évitable. Limiter le réchauffement sous 2 °C évite environ 50 jours
  de chaleur dangereuse par an en 2100.
- **Sécheresse :** l'indicateur **sature**. Environ 96 % du territoire est touché dès 2030, quel que soit le
  scénario. La note le présente comme un argument pour l'**adaptation immédiate** plutôt que de cacher le
  résultat : c'est le critère « Judgment ».
- **Pluies extrêmes :** sous les politiques actuelles, même le bas de la fourchette montre une hausse en 2100.
  La hausse est donc robuste.
- **Incertitude :** l'outil qualifie les résultats après 2060 d'« indicatifs ». La note le signale, avec les
  limites de l'indice de chaleur et de l'indicateur de sécheresse.

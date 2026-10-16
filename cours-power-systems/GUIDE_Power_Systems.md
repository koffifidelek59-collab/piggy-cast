---
title: "Power System Modeling, Simulation and Control"
subtitle: "Guide de révision complet, avec Python et PyPSA"
author: "KOUAME Koffi Fidèle, IMP-EGH, Track 6"
date: "Octobre 2026"
lang: fr
geometry: margin=2.2cm
fontsize: 11pt
mainfont: "Liberation Serif"
colorlinks: true
toc: true
toc-depth: 2
---

# Comment utiliser ce guide

**Le module** : 2 semaines, examen écrit de **60 minutes** qui compte pour **100 %** de la note. Le livre de
référence est Glover, Sarma et Overbye, *Power System Analysis and Design*, 5^e^ édition.

| Jour | Thème | Chapitre | Script Python |
|---|---|---|---|
| S1 J1 | Triphasé, phaseurs, puissance, Ybus | 2 | `01_three_phase_and_ybus.py` |
| S1 J2 | Transformateurs, per-unit | 3 | `02_transformers_per_unit.py` |
| S1 J3-J4 | Paramètres et modèles de lignes | 4, 5 | `03_lines.py` |
| S1 J5 | Écoulement de puissance (power flow) | 6 | `04_...newton_raphson.py`, `05_...pypsa.py` |
| S1 J3 (doc) | Réglage de tension par le réactif | 12 | `06_voltage_control_pypsa.py` |
| S2 J1-J3 | Courts-circuits, composantes symétriques | 7, 8, 9 | `07_faults.py` |
| S2 J4 | Stabilité, réglage fréquence | 11, 12 | `09_stability_and_frequency.py` |
| Leçon 5 | Scénario Power-to-X avec PyPSA | 6 | `08_pypsa_ptx_electrolysers.py` |

**Méthode de travail conseillée, pour chaque chapitre :**

1. Lire la section de ce guide (formules et méthode).
2. Refaire l'exemple **à la main**, sur papier, comme à l'examen.
3. Lancer le script et comparer : chaque script affiche son résultat **et** la valeur du livre ou des
   diapositives. Tous les scripts ont été vérifiés : les résultats concordent à l'arrondi près.
4. Changer une donnée dans le script et prédire le résultat avant de relancer.

**Installer l'environnement** (sur votre PC ou dans Google Colab) :

```
pip install pypsa highspy numpy scipy pandas
python 01_three_phase_and_ybus.py
```

# 1. Triphasé, puissance et matrice d'admittance (Ch. 2)

## Phaseurs et puissance

- $v(t) = \sqrt{2}\,V_{rms}\cos(\omega t + \delta)$ est représenté par le phaseur $V = V_{rms}\angle\delta$.
- Puissance complexe : $S = V I^* = P + jQ$, avec $P = |V||I|\cos\varphi$, $Q = |V||I|\sin\varphi$,
  $\varphi = \delta - \beta$ (angle de la tension moins angle du courant).
- Facteur de puissance $pf = \cos\varphi$ : **en retard (lagging)** si le courant est en retard sur la tension
  (charge inductive, $Q > 0$ absorbé) ; **en avance (leading)** pour une charge capacitive.
- La puissance complexe se conserve : $\sum S = 0$ dans un circuit, donc P et Q se conservent séparément.

## Triphasé équilibré

- Séquence abc : $V_{ab} = \sqrt{3}\,V_{an}\angle +30^\circ$ ; en étoile, $I_{ligne} = I_{phase}$.
- Triangle vers étoile : $Z_Y = Z_\Delta / 3$.
- $S_{3\phi} = 3\,V_{an} I_a^* = \sqrt{3}\,|V_{LL}|\,|I_L|\angle\varphi$.
- **Analyse par phase (per-phase)** : tout convertir en étoile, résoudre la phase a avec un neutre parfait.

**Exercice 1, question 2** (480 V, 112 A, pf 0,85 en retard) :
$|V_{an}| = 480/\sqrt{3} = 277{,}1$ V ; $V_{ab} = 480\angle 30^\circ$ ; $I_a = 112\angle -31{,}79^\circ$ ;
$S_{3\phi} = 79{,}1$ kW $+ j\,49{,}1$ kvar. Diagramme : $V_{ab}$ en avance de 30° sur $V_{an}$, $I_a$ en retard
de 31,79° sur $V_{an}$, donc 61,79° derrière $V_{ab}$.

## Matrice d'admittance Ybus

- $I = Y_{bus} V$, avec $I$ les courants **injectés** aux nœuds.
- **Règle de construction** : $Y_{ii}$ = somme des admittances connectées au nœud $i$ ;
  $Y_{ij}$ = **moins** la somme des admittances entre $i$ et $j$.
- Ybus est symétrique (sauf déphaseurs) et **creuse** (sparse) sur les grands réseaux.
- Résolution : petits réseaux $V = Y^{-1} I = Z_{bus} I$ ; grands réseaux : élimination de Gauss ou
  factorisation **LU** (on garde L et U pour réutiliser).

**Exercice 1, question 1** (admittances données) :

$$Y = \begin{bmatrix} -j6{,}05 & j2 & j4 \\ j2 & -j7{,}10 & j5 \\ j4 & j5 & -j9 \end{bmatrix},\quad
V_1 = 1{,}0158\angle 176{,}18^\circ,\ V_2 = 1{,}0154\angle 176{,}26^\circ,\ V_3 = 1{,}0156\angle 176{,}23^\circ$$

Piège : les valeurs du schéma sont des **admittances** (énoncé : « branch admittances are given »). Une
inductance a une admittance $-jB$. Le script vérifie que le Ybus construit par PyPSA est identique.

# 2. Transformateurs et système per-unit (Ch. 3)

## Modèle

- Idéal : $V_1/V_2 = N_1/N_2$ et $N_1 I_1 = N_2 I_2$.
- Schéma équivalent approché : $R + jX$ série (enroulements) et branche parallèle $R_c \parallel jX_m$ (pertes
  fer et magnétisation), souvent négligée.
- Couplage triangle-étoile : rapport de tension $N_1/(\sqrt{3}N_2)$ et **déphasage de 30°** ; convention ANSI :
  la HT est en avance de 30° sur la BT.

## Per-unit : la méthode en 4 étapes

1. Choisir **une seule** $S_{base}$ pour tout le réseau.
2. Choisir $V_{base}$ dans une zone, puis la propager à travers chaque transformateur **dans le rapport de ses
   tensions nominales**.
3. Calculer dans chaque zone : $I_{base} = S_{base}/(\sqrt{3}V_{base,LL})$ et $Z_{base} = V_{base,LL}^2/S_{base}$.
4. Convertir chaque impédance : $Z_{pu} = Z_\Omega / Z_{base}$, ou par **changement de base** :
   $$Z_{new} = Z_{old}\,\frac{S_{new}}{S_{old}}\left(\frac{V_{old}}{V_{new}}\right)^2$$

Avantage : le transformateur idéal disparaît du schéma per-unit, et une impédance de transformateur a la même
valeur per-unit vue des deux côtés.

**Exercice 1, question 3** (500 kVA, 13,8 kV Δ / 480Y V, $Z_T = 0{,}0056 + j0{,}0355$, 300 kW à pf 0,87) :

| Grandeur | per-unit | SI |
|---|---|---|
| (1) Puissance apparente source | $0{,}6897\angle 29{,}54^\circ$ | 344,8 kVA |
| (2) Courant source | 0,6897 $\angle$−29,54° | 14,43 A |
| (3) Courant charge | 0,6897 | 414,8 A |
| (4) Tension charge | 0,9848 $\angle$−1,13° | 472,7 V |
| (5) P charge | 0,5973 | 298,7 kW |
| (6) Q charge | 0,3232 | 161,6 kvar |
| (7) S charge | 0,6791 | 339,6 kVA |
| (8) pf charge | 0,8795 en retard | |

Avec le déphasage du couplage Δ-Y, la tension côté BT vaut $0{,}9848\angle -31{,}13^\circ$.

**Exercice 2 = exemple 3.4 du livre** : bases 240 / 480 / 120 V ; $X_{T2} = 0{,}1378$, $X_{ligne} = 0{,}2604$,
$Z_{charge} = 1{,}875 + j0{,}4167$ ; $I_{charge} = 0{,}4395\angle -26{,}01^\circ$ pu $= 109{,}9$ A.

# 3. Paramètres et modèles de lignes (Ch. 4 et 5)

## Paramètres par unité de longueur

- Résistance : $R = \rho/A$ ; correction de température (aluminium) $R_2 = R_1 (T_2 + 228{,}1)/(T_1 + 228{,}1)$.
- Inductance par phase : $L = 2\times10^{-7}\ln(D_{eq}/D_s)$ H/m.
- Capacité phase-neutre : $C = 2\pi\varepsilon_0/\ln(D_{eq}/r)$ F/m.
- $D_{eq} = \sqrt[3]{D_{12}D_{23}D_{31}}$ (ligne transposée) ; $D_s$ = rayon moyen géométrique (GMR), tiré des
  tableaux du fabricant. **Pour L on utilise $D_s$, pour C le rayon réel $r$.**
- Faisceaux : $D_{sL} = \sqrt{D_s d}$ (2 conducteurs), $\sqrt[3]{D_s d^2}$ (3 conducteurs) ; même chose pour C
  avec $r$ à la place de $D_s$.

## Modèles et paramètres ABCD : $V_S = AV_R + BI_R$, $I_S = CV_R + DI_R$

| Modèle | Domaine | A = D | B | C |
|---|---|---|---|---|
| Ligne courte | < 80 km (50 mi) | 1 | $Z$ | 0 |
| π nominal | 80 à 250 km | $1 + ZY/2$ | $Z$ | $Y(1 + ZY/4)$ |
| Ligne longue | > 250 km | $\cosh\gamma l$ | $Z_c\sinh\gamma l$ | $\sinh(\gamma l)/Z_c$ |

avec $Z_c = \sqrt{z/y}$ (impédance caractéristique) et $\gamma = \sqrt{zy}$. Le π équivalent d'une ligne longue :
$Z' = Z\,\sinh(\gamma l)/(\gamma l)$, $Y'/2 = (Y/2)\tanh(\gamma l/2)/(\gamma l/2)$.

**Résultats vérifiés** : ligne courte des diapositives : $V_S = 16{,}7$ kV (28,9 kV composée, 1,26 pu), pertes
1,94 MW pour 7,33 MW. Ligne moyenne 230 kV : $V_S = 142{,}4\angle 8{,}68^\circ$ kV, $P_S = 152{,}9$ MW.
Exemple 5.2 : $A = 0{,}9313\angle 0{,}21^\circ$, $B = 97{,}0\angle 87{,}2^\circ$ Ω.

## Puissance naturelle et capacité de transport

- Ligne sans pertes : $Z_c = \sqrt{L/C}$ ; **SIL** $= V_{nom}^2/Z_c$ (profil de tension plat).
- Capacité de transport : limite thermique sur les lignes courtes, chute de tension sur les moyennes, stabilité
  ($\approx$ SIL à 300 milles) sur les longues.
- Compensation : condensateurs shunt (facteur de puissance), réactances shunt (lignes THT à faible charge),
  condensateurs série (réduire X), FACTS.

# 4. Écoulement de puissance (Ch. 6)

## Équations

$$P_i = \sum_k |V_i||V_k|\left[G_{ik}\cos\delta_{ik} + B_{ik}\sin\delta_{ik}\right],\quad
Q_i = \sum_k |V_i||V_k|\left[G_{ik}\sin\delta_{ik} - B_{ik}\cos\delta_{ik}\right]$$

| Type de nœud | Connu | Inconnu |
|---|---|---|
| Bilan (slack, swing) | $|V|$, $\delta = 0$ | P, Q (couvre les pertes) |
| PV (générateur) | P, $|V|$ | Q, $\delta$ |
| PQ (charge) | P, Q | $|V|$, $\delta$ |

Nombre d'équations : $(N-1)$ en P et $(N_{PQ})$ en Q. Exemple 6.9 : 5 nœuds, 1 PV, donc un jacobien 7 × 7.

## Méthodes

- **Gauss-Seidel** : simple, convergence lente (64 itérations sur l'exemple 6.9).
- **Newton-Raphson** : $J\,\Delta x = \Delta f$ avec $\Delta f$ = spécifié − calculé ; convergence
  **quadratique** (5 itérations). Formules du jacobien : voir la leçon 5 et `04_power_flow_newton_raphson.py`.
- **Découplé rapide** : on néglige $\partial P/\partial|V|$ et $\partial Q/\partial\delta$ ; matrices constantes
  ; plus d'itérations (22) mais chacune est moins coûteuse ; **même solution exacte**.
- **Écoulement linéarisé (DC)** : $|V| = 1$, R négligé, $P = B'\theta$ ; utile pour les études de réseau
  et les marchés (leçon 5).
- **Conséquence pour le réglage** : P dépend surtout des angles, Q surtout des modules de tension.

**Exemple 6.9 (5 nœuds), résultat vérifié** : $|V| = 1{,}000 / 0{,}834 / 1{,}050 / 1{,}019 / 0{,}974$ pu ;
angles $0 / -22{,}41 / -0{,}60 / -2{,}83 / -4{,}55$° ; $P_{G1} = 394{,}8$ MW ; pertes 34,8 MW. Identique avec
notre Newton-Raphson et avec PyPSA.

# 5. Réglage de tension par le réactif (document du jour 3)

- Chute de tension sur une ligne : $\Delta V \approx (RP + XQ)/V$.
- Avec une production décentralisée (DG) qui exporte P, la tension **monte** au point de raccordement.
- Leviers : absorber du réactif à la DG (Q < 0), compensateurs, régleur en charge (OLTC), écrêtage de P.
- En distribution, R/X est proche de 1 : P agit presque autant que Q sur la tension, contrairement au transport
  (R/X ≈ 0,1).

Le script 06 montre une hausse à 1,075 pu (limite 1,05) et calcule le réactif à absorber : 1,10 Mvar (valeur
exacte par écoulement de puissance) contre 1,55 Mvar avec la formule approchée, qui surestime.

# 6. Courts-circuits et composantes symétriques (Ch. 7 à 9)

## Défaut triphasé symétrique

- On utilise les réactances **subtransitoires** $X''_d$ des machines et la tension avant défaut $V_F$.
- Avec la matrice d'impédance : $I_F = V_F/Z_{kk}$ et, pendant le défaut, $E_i = (1 - Z_{ik}/Z_{kk})\,V_F$.
- Exemple 7.4 : $Z_{11} = j0{,}11565$, $I_{F1} = -j9{,}079$ pu ; $I_{F2} = -j7{,}558$ pu.

## Composantes symétriques (Fortescue)

$$\begin{bmatrix}V_a\\V_b\\V_c\end{bmatrix} = \begin{bmatrix}1&1&1\\1&a^2&a\\1&a&a^2\end{bmatrix}
\begin{bmatrix}V_0\\V_1\\V_2\end{bmatrix},\quad a = 1\angle 120^\circ$$

- Courant de neutre $I_n = 3I_0$. Le triangle bloque la séquence homopolaire ; une impédance de neutre $Z_n$
  apparaît comme $3Z_n$ dans le réseau homopolaire.

## Les quatre défauts (à connaître par cœur)

| Défaut | Connexion des réseaux de séquence | Courant |
|---|---|---|
| Triphasé | direct seul | $I_1 = V_F/Z_1$ |
| Phase-terre (a-g) | série : 0, 1, 2 | $I_0 = I_1 = I_2 = V_F/(Z_0 + Z_1 + Z_2 + 3Z_F)$, $I_a = 3I_1$ |
| Biphasé (b-c) | 1 et 2 en parallèle | $I_1 = -I_2 = V_F/(Z_1 + Z_2 + Z_F)$, $I_b = -j\sqrt{3}\,I_1$ |
| Biphasé-terre (b-c-g) | 1 en série avec (2 // (0 + 3Z_F)) | $I_1 = V_F/[Z_1 + Z_2 \parallel (Z_0 + 3Z_F)]$ |

**Exemples 9.2 à 9.5 vérifiés (défaut au nœud 2)** : triphasé $I_1 = -j7{,}558$ pu ; phase-terre
$I_a = 24{,}65$ kA ; biphasé $I_b = 26{,}74$ kA ; biphasé-terre $I_b = 28{,}86$ kA, $I_n = 21{,}00$ kA.

## Protection (Ch. 10, notions)

Fusibles et disjoncteurs éliminent les défauts ; relais de surintensité (temps inverse), distance (impédance
vue) et différentiels (transformateurs, jeux de barres). Sélectivité : le relais le plus proche du défaut agit en
premier ; critère n-1 pour la sécurité.

# 7. Stabilité et réglage de fréquence (Ch. 11 et 12)

## Équation d'oscillation et critère des aires égales

$$\frac{2H}{\omega_{syn}}\frac{d^2\delta}{dt^2} = p_m - p_e,\qquad p_e = P_{max}\sin\delta$$

- Stable si l'aire d'accélération $A_1$ (pendant le défaut) peut être compensée par l'aire de décélération $A_2$.
- Exemple 11.5 : angle critique $\delta_{cr} = 88{,}74^\circ$, temps critique 0,1897 s (11,38 cycles). La
  simulation du script le confirme : stable si le défaut est éliminé à 0,18 s, instable à 0,20 s.

## Réglage de fréquence

- Statisme (droop) : $\Delta p_m = \Delta p_{ref} - \Delta f/R$ ; exemple 12.3 : +0,01 Hz, R = 0,05 sur 500 MVA,
  donc −1,67 MW.
- Une zone : $\beta = D + \sum 1/R_i$ ; écart de fréquence permanent $\Delta f = -\Delta P_{charge}/\beta$ ; les
  groupes se partagent la charge au prorata de $S_{nom}/R$.
- Réglage secondaire (AGC) : annule l'erreur de zone $ACE = (p_{tie} - p_{tie,sched}) + B_f(f - f_0)$.
- Tension : régulateur d'excitation (AVR) des alternateurs, régleurs en charge, compensateurs.

# 8. PyPSA : l'essentiel

**Ce qu'il fait** : écoulement de puissance AC (`n.pf()`, Newton-Raphson), écoulement linéarisé (`n.lpf()`),
optimisation de la production et des investissements (`n.optimize()` avec HiGHS), couplage de secteurs
(électricité, hydrogène, chaleur). **Ce qu'il ne fait pas** : courts-circuits et simulations dynamiques ; pour
ceux-là, numpy (scripts 07 et 09), ou des outils comme pandapower.

| Composant PyPSA | Rôle | Unités importantes |
|---|---|---|
| `Bus` | nœud | `v_nom` en kV ; `v_mag_pu_set` pour PV et bilan |
| `Line` | ligne (modèle π) | `r`, `x` en **ohm**, `b` en **siemens**, `s_nom` en MVA |
| `Transformer` | transformateur | `r`, `x` en **per-unit sur sa propre `s_nom`** |
| `Generator` | production | `control` = `Slack`, `PV` ou `PQ` ; `p_set` en MW |
| `Load` | consommation | `p_set`, `q_set` en MW et Mvar |
| `ShuntImpedance` | élément shunt | `g`, `b` en siemens |
| `Link` | conversion (ex. électrolyseur) | `efficiency`, `p_nom` |
| `Store` | stockage (ex. réservoir H2) | `e_nom` en MWh |

**Pièges vérifiés en écrivant les scripts :**

1. Passer des données per-unit du livre à PyPSA : $Z_\Omega = Z_{pu}\,V_{nom}^2/S_{base}$ et
   $B_S = B_{pu}/Z_{base}$ pour les lignes ; garder le per-unit pour les transformateurs avec
   `s_nom` = $S_{base}$.
2. PyPSA travaille sur une base de **1 MVA** : diviser son Ybus par $S_{base}$ (100) pour retrouver celui du
   livre.
3. Dans PyPSA 1.4, donner `p_set=0` au générateur bilan, sinon sa puissance reste vide (NaN).
4. Résultats : `n.buses_t.v_mag_pu`, `n.buses_t.v_ang` (radians), `n.lines_t.p0` (puissance qui part de
   `bus0`), `n.generators_t.p`.

# 9. Questions d'entraînement (corrigés en fin de section)

1. Une charge triphasée de 50 kW à pf 0,8 en retard est alimentée sous 400 V. Calculer le courant de ligne
   et la puissance réactive.
2. Un transformateur de 100 MVA a $X = 0{,}12$ pu. Quelle est sa réactance sur une base de 200 MVA à la même
   tension ?
3. Construire le Ybus d'un réseau de 2 nœuds reliés par $Z = j0{,}1$, avec une admittance shunt $j0{,}05$ à
   chaque extrémité.
4. Pourquoi un nœud PV n'a-t-il pas d'équation en Q dans le Newton-Raphson ?
5. Quelle est la dimension du jacobien d'un réseau de 10 nœuds avec 3 générateurs PV et un nœud bilan ?
6. Une ligne de 300 km se modélise-t-elle en π nominal ? Pourquoi ?
7. Défaut phase-terre franc avec $Z_0 = j0{,}25$, $Z_1 = Z_2 = j0{,}15$, $V_F = 1$ pu : courant de défaut ?
8. Pourquoi un transformateur Δ-Y empêche-t-il le courant homopolaire de passer d'un côté à l'autre ?
9. Un groupe de 200 MVA a R = 4 %. La fréquence baisse de 0,1 Hz (réseau 50 Hz). Quelle variation de
   puissance ?
10. Une DG fait monter la tension au-dessus de 1,05 pu. Citer trois solutions.

**Corrigés** :

1. $|S| = 62{,}5$ kVA, $I = 62\,500/(\sqrt{3}\times400) = 90{,}2$ A, $Q = 37{,}5$ kvar.
2. $X = 0{,}12 \times 200/100 = 0{,}24$ pu.
3. $Y_{11} = Y_{22} = -j10 + j0{,}05 = -j9{,}95$ ; $Y_{12} = Y_{21} = +j10$.
4. Q y est libre : le générateur ajuste Q pour tenir $|V|$ ; seule l'équation en P est écrite.
5. Inconnues : 9 angles et $10 - 1 - 3 = 6$ modules, donc un jacobien 15 × 15.
6. Non : au-delà d'environ 250 km il faut le modèle de ligne longue (π équivalent) ; l'erreur sur B atteint
   environ 2 % à 300 km (exemple 5.2).
7. $I_1 = 1/(j0{,}55) = -j1{,}818$, $I_a = 3I_1 = 5{,}45$ pu.
8. Le courant homopolaire circule dans le triangle sans sortir ; le réseau homopolaire est ouvert entre les
   deux côtés.
9. $\Delta f_{pu} = -0{,}1/50 = -0{,}002$ ; $\Delta P = 0{,}002/0{,}04 \times 200 = +10$ MW.
10. Absorber du réactif à la DG, régleur en charge du poste, écrêter la production (ou compensateur shunt).

# 10. Pour aller plus loin avec PyPSA

- Modifier `05_power_flow_pypsa.py` : passer la charge du nœud 2 de 800 à 900 MW et observer $|V_2|$ ;
  ajouter un condensateur shunt au nœud 2 (`ShuntImpedance` avec `b` > 0) et voir la tension remonter.
- Modifier `08_pypsa_ptx_electrolysers.py` : doubler l'électrolyseur, ou ajouter du solaire au sud, et voir
  l'effet sur la congestion et l'écrêtement.
- Documentation officielle : <https://docs.pypsa.org> (exemples d'écoulement de puissance et de
  couplage de secteurs).

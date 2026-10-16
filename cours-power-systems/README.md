# Power System Modeling, Simulation and Control (IMP-EGH, Track 6)

Révision complète du module, avec des scripts Python et PyPSA vérifiés sur le livre
(Glover, Sarma, Overbye, *Power System Analysis and Design*, 5e éd.) et les diapositives du cours.

- `GUIDE_Power_Systems.pdf` : guide de révision (formules, méthodes, corrigés des exercices 1 et 2,
  questions d'entraînement, mémo PyPSA).
- `code/` : un script par chapitre ; chacun affiche son résultat et la valeur de référence.

| Script | Contenu |
|---|---|
| `01_three_phase_and_ybus.py` | Exercice 1 (Q1 Ybus, aussi avec PyPSA ; Q2 triphasé) |
| `02_transformers_per_unit.py` | Exercice 1 Q3 ; Exercice 2 = exemple 3.4 |
| `03_lines.py` | Lignes courte, moyenne, longue ; SIL et capacité de transport |
| `04_power_flow_newton_raphson.py` | Newton-Raphson, découplé rapide, Gauss-Seidel (exemple 6.9) |
| `05_power_flow_pypsa.py` | Même réseau dans PyPSA : `pf()` AC et `lpf()` DC |
| `06_voltage_control_pypsa.py` | Hausse de tension due à une DG et compensation réactive (PyPSA) |
| `07_faults.py` | Zbus, composantes symétriques, 4 types de défauts (exemples 7.4, 8.3, 9.1 à 9.5) |
| `08_pypsa_ptx_electrolysers.py` | Scénario Power-to-X : emplacement d'électrolyseurs, `lpf()` et `optimize()` avec HiGHS |
| `09_stability_and_frequency.py` | Équation d'oscillation, aires égales (ex. 11.5), statisme (ex. 12.3) |

## Lancer

```
pip install -r requirements.txt
cd code
python 01_three_phase_and_ybus.py
```

Fonctionne aussi dans Google Colab : `!pip install pypsa highspy`, puis copier un script dans une cellule.

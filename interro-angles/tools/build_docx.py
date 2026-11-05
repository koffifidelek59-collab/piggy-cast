"""Construit les versions Word du sujet (deux exemplaires par page) et du corrige."""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import sys

OUT = sys.argv[1]  # dossier de sortie

AFFIRMATIONS = [
    "Deux angles adjacents ont le même sommet, un côté commun et sont situés de part et d'autre de ce côté commun.",
    "Si deux angles ont seulement un sommet commun, alors ils sont adjacents.",
    "Deux angles adjacents sont situés de part et d'autre de leur côté commun.",
    "Deux angles complémentaires sont deux angles dont la somme des mesures est 90°.",
    "Deux angles supplémentaires sont deux angles dont la somme des mesures est 90°.",
    "Un angle de mesure 35° et un angle de mesure 55° sont complémentaires.",
    "Un angle de mesure 120° et un angle de mesure 70° sont supplémentaires.",
    "Deux angles complémentaires ont la même mesure.",
    "Deux angles complémentaires peuvent être tous les deux obtus.",
    "Un angle de mesure 100° et un angle de mesure 80° sont supplémentaires.",
]
REPONSES = ["VRAI", "FAUX", "VRAI", "VRAI", "FAUX", "VRAI", "FAUX", "FAUX", "FAUX", "VRAI"]
JUSTIF = [
    "C'est exactement la définition des angles adjacents (les trois conditions).",
    "Il faut aussi un côté commun et être de part et d'autre de ce côté.",
    "C'est une condition de la définition.",
    "C'est la définition d'angles complémentaires.",
    "La somme de deux angles supplémentaires est 180°, pas 90°.",
    "35° + 55° = 90°.",
    "120° + 70° = 190° ≠ 180°.",
    "Par exemple 30° et 60° sont complémentaires sans être égaux ; ils sont égaux seulement si chacun mesure 45°.",
    "Un angle obtus dépasse 90° ; deux tels angles dépasseraient 90° à eux seuls.",
    "100° + 80° = 180°.",
]

FONT = "Times New Roman"


def set_cell_bg(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def set_col_widths(table, widths):
    """Impose des largeurs fixes robustes (layout fixe + grille + largeur de chaque cellule)."""
    table.autofit = False
    table.allow_autofit = False
    tblPr = table._tbl.tblPr
    # layout fixe
    layout = OxmlElement("w:tblLayout"); layout.set(qn("w:type"), "fixed"); tblPr.append(layout)
    # largeur totale
    total = int(sum(w.twips for w in widths))
    tblW = OxmlElement("w:tblW"); tblW.set(qn("w:w"), str(total)); tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)
    # grille
    for child in table._tbl.findall(qn("w:tblGrid")):
        table._tbl.remove(child)
    grid = OxmlElement("w:tblGrid")
    for w in widths:
        gc = OxmlElement("w:gridCol"); gc.set(qn("w:w"), str(int(w.twips))); grid.append(gc)
    table._tbl.insert(list(table._tbl).index(tblPr) + 1, grid)
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w


def run(p, text, bold=False, italic=False, size=10):
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    r.font.name = FONT
    return r


def base_style(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(10)
    st.paragraph_format.space_after = Pt(2)
    st.paragraph_format.space_before = Pt(0)


# ------------------------------------------------------------------ SUJET (x2)
def add_sujet(doc):
    # En-tete
    t = doc.add_table(rows=2, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    data = [
        ("Lycée Mixte 1 de Yamoussoukro", "Année scolaire : 2026-2027"),
        ("Discipline : Mathématiques", "Classe : 5e     Durée : 15 min"),
    ]
    for i, (a, b) in enumerate(data):
        for j, txt in enumerate((a, b)):
            c = t.rows[i].cells[j]
            c.paragraphs[0].text = ""
            run(c.paragraphs[0], txt, bold=True)
    set_col_widths(t, [Cm(11.5), Cm(6.0)])

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "INTERROGATION ÉCRITE N° 2", bold=True, size=13)
    run(p, "   (Thème : Les angles)", italic=True, size=11)

    p = doc.add_paragraph()
    run(p, "Nom et prénoms : ...........................................................   ")
    run(p, "Note : ............ / 10", bold=True)

    p = doc.add_paragraph()
    run(p, "Consigne. ", bold=True)
    run(p, "Mets une croix (×) dans la case VRAI si l'affirmation est vraie, ou dans la "
            "case FAUX si elle est fausse. ")
    run(p, "(1 point par bonne réponse.)", italic=True)

    # Tableau Vrai/Faux
    t = doc.add_table(rows=1, cols=4)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = ["N°", "Affirmations", "VRAI", "FAUX"]
    for j, txt in enumerate(hdr):
        c = t.rows[0].cells[j]
        c.paragraphs[0].text = ""
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(c.paragraphs[0], txt, bold=True)
        set_cell_bg(c, "E1EBE1")
    for i, aff in enumerate(AFFIRMATIONS, start=1):
        cells = t.add_row().cells
        cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(cells[0].paragraphs[0], str(i))
        run(cells[1].paragraphs[0], aff)
    set_col_widths(t, [Cm(0.9), Cm(13.3), Cm(1.6), Cm(1.6)])


def build_sujet():
    doc = Document()
    base_style(doc)
    doc.styles["Normal"].font.size = Pt(9)
    sec = doc.sections[0]
    sec.page_height = Cm(29.7); sec.page_width = Cm(21.0)
    for m in ("top_margin", "bottom_margin"):
        setattr(sec, m, Cm(1.0))
    sec.left_margin = Cm(1.4); sec.right_margin = Cm(1.4)

    add_sujet(doc)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "- - - - - - - - - - - - - - - - - -  (découper ici)  - - - - - - - - - - - - - - - - - -",
        size=8)

    add_sujet(doc)
    doc.save(OUT + "/interro_angles_sujet.docx")


# ------------------------------------------------------------------ CORRIGE
def build_corrige():
    doc = Document()
    base_style(doc)
    sec = doc.sections[0]
    sec.page_height = Cm(29.7); sec.page_width = Cm(21.0)
    sec.top_margin = sec.bottom_margin = Cm(1.5)
    sec.left_margin = sec.right_margin = Cm(1.6)

    t = doc.add_table(rows=2, cols=2)
    t.style = "Table Grid"
    for i, (a, b) in enumerate([
        ("Lycée Mixte 1 de Yamoussoukro", "Année scolaire : 2026-2027"),
        ("Discipline : Mathématiques", "Classe : 5e"),
    ]):
        for j, txt in enumerate((a, b)):
            c = t.rows[i].cells[j]; c.paragraphs[0].text = ""
            run(c.paragraphs[0], txt, bold=True)
    set_col_widths(t, [Cm(11.3), Cm(6.0)])

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "CORRIGÉ DE L'INTERROGATION N° 2", bold=True, size=14)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "Thème : Les angles", italic=True, size=11)

    p = doc.add_paragraph(); run(p, "Rappels de cours.", bold=True)
    rappels = [
        ("Angles adjacents : ", "deux angles qui ont le même sommet, un côté commun, et qui sont "
                                 "situés de part et d'autre de ce côté commun."),
        ("Angles complémentaires : ", "deux angles dont la somme des mesures est égale à 90°."),
        ("Angles supplémentaires : ", "deux angles dont la somme des mesures est égale à 180°."),
    ]
    for head, body in rappels:
        p = doc.add_paragraph(style="List Bullet")
        run(p, head, bold=True); run(p, body)

    t = doc.add_table(rows=1, cols=4)
    t.style = "Table Grid"
    for j, txt in enumerate(["N°", "Affirmation", "Réponse", "Justification"]):
        c = t.rows[0].cells[j]; c.paragraphs[0].text = ""
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(c.paragraphs[0], txt, bold=True); set_cell_bg(c, "E1EBE1")
    for i, aff in enumerate(AFFIRMATIONS):
        cells = t.add_row().cells
        cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(cells[0].paragraphs[0], str(i + 1))
        run(cells[1].paragraphs[0], aff)
        cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(cells[2].paragraphs[0], REPONSES[i], bold=True)
        run(cells[3].paragraphs[0], JUSTIF[i])
    set_col_widths(t, [Cm(1.0), Cm(7.2), Cm(2.0), Cm(7.6)])

    p = doc.add_paragraph()
    run(p, "Barème : ", bold=True)
    run(p, "1 point par bonne réponse, soit un total de 10 points.")
    p = doc.add_paragraph()
    run(p, "Corrigé en bref : ", bold=True)
    run(p, "   ".join(f"{i+1}-{REPONSES[i][0]}" for i in range(10)))

    doc.save(OUT + "/interro_angles_corrige.docx")


build_sujet()
build_corrige()
print("OK")

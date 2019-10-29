import json


from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus import Spacer, Image
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_WIDTH, PAGE_HEIGHT = A4

pageinfo = "Υπεύθυνη Δήλωση"

pdfmetrics.registerFont(TTFont(
    'Roboto-Regular', '/usr/share/fonts/truetype/roboto/hinted/Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Roboto-Bold', '/usr/share/fonts/truetype/roboto/hinted/Roboto-Bold.ttf'))

info = {}


def load_results(declaration_id):
    info['to'] = 'doi'
    info['name'] = 'name'
    info['surname'] = 'surname'
    info['father_name'] = 'father name'
    info['mother_name'] = 'mother name'
    info['date_of_birth'] = 'date-of-birth'
    info['birth_place'] = 'Birthplace'
    info['id_number'] = 'ID #'
    info['tax_id'] = 'TAX ID'
    info['place_of_residence'] = 'Athens'
    info['street'] = 'Street'
    info['street_number'] = 'St. #'
    info['postal_code'] = 'PC'
    info['email'] = 'mariosmenexes@gmail.com'
    info['telephone'] = '69XXXXXXXX'
    return info


def make_first_page_hf(canvas, doc):
    canvas.saveState()
    canvas.drawImage('logo.jpg',
                     x=PAGE_WIDTH - 12 * cm,
                     y=PAGE_HEIGHT - 3 * cm,
                     width=PAGE_WIDTH / 8,
                     height=2.5 * cm)
    canvas.restoreState()


def make_later_pages_hf(canvas, doc):
    canvas.saveState()
    canvas.setFont('Roboto-Regular', 9)
    canvas.drawString(PAGE_WIDTH - 7 * cm, PAGE_HEIGHT - 2 * cm,
                      "%s %d" % (pageinfo, doc.page))
    canvas.restoreState()


def make_heading(element, contents):
    for x in range(0, 2):
        elements.append(Spacer(1, 12))
    for pcontent in contents:
        elements.append(Paragraph(pcontent, styles["DilosiHeading"]))


def make_intro(elements, contents):
    elements.append(Paragraph(contents, styles["Dilosi"]))
    elements.append(Spacer(1, 12))


def make_totals(elements, info):
    fields = [
        [Paragraph('Πρός: ', styles['DilosiBold']),
         Paragraph(info['to'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Όνομα: ', styles['DilosiBold']),
         Paragraph(info['name'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Επώνυμο: ', styles['DilosiBold']), Paragraph(
            info['surname'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Όνομα και Επώνυμο Πατέρα:',  styles['DilosiBold']),
         Paragraph(info['father_name'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Όνομα και Επώνυμο Μητέρας: ', styles['DilosiBold']),
         Paragraph(info['mother_name'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Ημερομηνία Γέννησης: ', styles['DilosiBold']),
         Paragraph(info['date_of_birth'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Τόπος Γέννησης: ', styles['DilosiBold']),
         Paragraph(info['birth_place'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Α.Δ.Τ: ', styles['DilosiBold']), Paragraph(
            info['id_number'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Α.Φ.Μ: ', styles['DilosiBold']), Paragraph(
            info['tax_id'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Τόπος Κατοικίας: ', styles['DilosiBold']), Paragraph(
            info['place_of_residence'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Οδός:', styles['DilosiBold']), Paragraph(
            info['street'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Αριθμός: ', styles['DilosiBold']), Paragraph(
            info['street_number'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Τ.Κ: ', styles['DilosiBold']), Paragraph(
            info['postal_code'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Email: ', styles['DilosiBold']), Paragraph(
            info['email'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph('Τηλέφωνο: ', styles['DilosiBold']), Paragraph(
            info['telephone'], styles['Dilosi'])],
        [Spacer(1, 5), Spacer(1, 5)],
    ]

    fields = Table(fields)
    elements.append(fields)


def make_results(elements):

    make_totals(elements, info)
    make_intro(elements, subtitle2)
    make_intro(elements, subtitle3)
    make_intro(elements, subtitle4)
    signature = [
        [Spacer(5, 10), Paragraph(
            'Ο/Η Δηλ.', styles['DilosiSignature'])],
        [Spacer(5, 10), Paragraph('%s %s' % (info['name'], info['surname']),
                                  styles['DilosiSignature'])],
        [Spacer(5, 10), Paragraph(
            '15 Οκτωβρίου 2019, 15:30', styles['DilosiSignature'])],
        [Spacer(5, 10), Paragraph(
            'Κωδικός: 123456ΑΣ123459998', styles['DilosiSignature'])],
    ]

    signature = [
        [Image('qr.png', 95, 95, hAlign='LEFT'), signature]
    ]

    signature = Table(signature)
    elements.append(signature)


doc = SimpleDocTemplate("Υπεύθυνη Δήλωση.pdf", pagesize=A4)

elements = []

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Dilosi',
                          fontName='Roboto-Regular',
                          fontSize=12,
                          leading=16,
                          alignment=TA_JUSTIFY))

styles.add(ParagraphStyle(name='DilosiBold',
                          fontName='Roboto-Bold',
                          fontSize=12,
                          leading=16,
                          alignment=TA_JUSTIFY))

styles.add(ParagraphStyle(name='DilosiHeading',
                          fontName='Roboto-Bold',
                          fontSize=16,
                          alignment=TA_CENTER,
                          spaceAfter=16))

styles.add(ParagraphStyle(name='DilosiSignature',
                          fontName='Roboto-Regular',
                          fontSize=12,
                          alignment=TA_RIGHT))
info = load_results(1)

title = 'Υπεύθυνη Δήλωση'
subtitle = 'Η ακρίβεια των στοιχείων που υποβάλλονται με αυτή τη δήλωση μπορεί να ελεγχθεί με βάση το αρχείο άλλων υπηρεσιών (άρθρο 8 παρ. 4 Ν. 1599/1986)'
subtitle2 = 'Με ατομική μου ευθύνη και γνωρίζοντας τις κυρώσεις, που προβλέπονται από τις διατάξεις της παρ. 6 του άρθρου 22 του Ν. 1599/1986, δηλώνω ότι:'
subtitle3 = 'blablablablabla'
subtitle4 = 'Γνωρίζω ότι: Όποιος εν γνώσει του δηλώνει ψευδή γεγονότα ή αρνείται ή αποκρύπτει τα αληθινά με έγγραφη υπεύθυνη δήλωση του άρθρου 8 τιμωρείται με φυλάκιση τουλάχιστον τριών μηνών. Εάν ο υπαίτιος αυτών των πράξεων σκόπευε να προσπορίσει στον εαυτόν του ή σε άλλον περιουσιακό όφελος βλάπτοντας τρίτον ή σκόπευε να βλάψει άλλον, τιμωρείται με κάθειρξη μέχρι 10 ετών.'

dilosi_contents = [
    title,
    subtitle,
]

make_heading(elements, [title])

make_intro(elements, subtitle)

make_results(elements)

doc.build(elements, onFirstPage=make_first_page_hf,
          onLaterPages=make_later_pages_hf)

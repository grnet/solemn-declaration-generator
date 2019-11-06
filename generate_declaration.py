import json
import os.path

from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.platypus import Spacer, Image
from reportlab.platypus import PageBreak
from reportlab.platypus import KeepInFrame
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth


PAGE_WIDTH, PAGE_HEIGHT = A4

pageinfo = "Υπεύθυνη Δήλωση"

if(os.path.exists('/usr/share/fonts/truetype/roboto/hinted/'
                  'Roboto-Regular.ttf')):
    pdfmetrics.registerFont(TTFont(
        'Roboto-Regular', '/usr/share/fonts/truetype/roboto/hinted/'
        'Roboto-Regular.ttf'))
    pdfmetrics.registerFont(TTFont(
        'Roboto-Bold', '/usr/share/fonts/truetype/roboto/hinted/'
        'Roboto-Bold.ttf'))
else:
    pdfmetrics.registerFont(TTFont(
        'Roboto-Regular', '/System/Library/Fonts/Supplemental/Arial.ttf'))
    pdfmetrics.registerFont(TTFont(
        'Roboto-Bold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))

info = {}


def load_results(filename):
    with open(filename, 'r') as jsonfile:
        jsondata = json.load(jsonfile)
        for result in jsondata:
            info[result] = jsondata[result]
    return info

def shrink_to_fit(paragraph, style, assigned_width, assigned_height):
    w, h = paragraph.wrap(assigned_width, assigned_height)
    if assigned_width < w or assigned_height < h:
        style = style.clone('default')
    while assigned_width < w or assigned_height < h:
        style.fontSize -= 1
        paragraph = Paragraph(paragraph.text, style)
        w, h = paragraph.wrap(assigned_width, assigned_height)
    return paragraph, style

def draw_field(canvas, contents, origin_x, origin_y, width, height):
    style = ParagraphStyle('default', fontName='Roboto-Regular')
    paragraph = Paragraph(contents, style)
    paragraph, _ = shrink_to_fit(paragraph, style, width, height)
    paragraph.drawOn(canvas, origin_x, origin_y)    

def make_first_page_hf(canvas, doc):
    canvas.saveState()
    canvas.drawImage('logo.jpg',
                     x=PAGE_WIDTH - 12 * cm,
                     y=PAGE_HEIGHT - 2.7 * cm,
                     width=PAGE_WIDTH / 8,
                     height=2.5 * cm)
    # Subtitle
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 6.1 * cm,
                     17 * cm, 1.5 * cm, 4, stroke=1, fill=0)
    # Frame Rectangle
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 15.85 * cm,
                     17 * cm, 9 * cm, 3, stroke=1, fill=0)

    # To Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 7.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.4 * cm, PAGE_HEIGHT - 7.80 * cm)
    # Set font face and size
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Προς:')
    canvas.drawText(textobject)
    
    # To value
    canvas.roundRect(4.5 * cm, PAGE_HEIGHT - 7.85 * cm,
                     14.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_field(canvas, info['to'],
               5 * cm, PAGE_HEIGHT - 7.80 * cm,
               13 * cm, 1 * cm)

    # Name box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 8.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 8.79 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Ο - Η Όνομα:')
    canvas.drawText(textobject)

    # Name value
    canvas.roundRect(4.5 * cm, PAGE_HEIGHT - 8.85 * cm, 6 * cm, 1 * cm, 0,
                     stroke=1, fill=0)
    draw_field(canvas, info['name'],
               5 * cm, PAGE_HEIGHT - 8.80 * cm,
               5 * cm, 1 * cm)

    # Surname box
    canvas.roundRect(10.5 * cm, PAGE_HEIGHT - 8.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(11 * cm, PAGE_HEIGHT - 8.79 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Επώνυμο:')
    canvas.drawText(textobject)

    # Surname value
    canvas.roundRect(13 * cm, PAGE_HEIGHT - 8.85 * cm,
                     6 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_field(canvas, info['surname'],
               13.5 * cm, PAGE_HEIGHT - 8.80 * cm,
               5 * cm, 1 * cm)

    # Father's name box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 9.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 9.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Όνομα και Επώνυμο Πατέρα:')
    canvas.drawText(textobject)

    # Father's name value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 9.85 * cm,
                     12.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(7 * cm, PAGE_HEIGHT - 9.80 * cm)
    font_size = calculate_font_size(10, 12.5, info['father_name'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['father_name'])
    canvas.drawText(textobject)
    # Mother Name Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 10.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.05 * cm, PAGE_HEIGHT - 10.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Όνομα και Επώνυμο Μητέρας:')
    canvas.drawText(textobject)
    # Mother Name Value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 10.85 * cm,
                     12.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(7 * cm, PAGE_HEIGHT - 10.80 * cm)
    font_size = calculate_font_size(10, 12.5, info['mother_name'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['mother_name'])
    canvas.drawText(textobject)
    # Birth Date Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 11.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 11.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Ημερομηνία Γέννησης:')
    canvas.drawText(textobject)
    # Birth Date Value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 11.85 * cm,
                     12.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(7 * cm, PAGE_HEIGHT - 11.80 * cm)
    font_size = calculate_font_size(10, 12.5, info['date_of_birth'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['date_of_birth'])
    canvas.drawText(textobject)
    # Birthplace Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 12.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 12.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Τόπος Γέννησης:')
    canvas.drawText(textobject)
    # Birthplace Value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 12.85 * cm,
                     12.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(7 * cm, PAGE_HEIGHT - 12.80 * cm)
    font_size = calculate_font_size(10, 12.5, info['birth_place'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['birth_place'])
    canvas.drawText(textobject)
    # ID Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 13.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.05 * cm, PAGE_HEIGHT - 13.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Αριθμός Δελτίου Ταυτότητας:')
    canvas.drawText(textobject)
    # ID Value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 13.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(7 * cm, PAGE_HEIGHT - 13.80 * cm)
    font_size = calculate_font_size(10, 4.5, info['id_number'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['id_number'])
    canvas.drawText(textobject)
    # TEL Box
    canvas.roundRect(11 * cm, PAGE_HEIGHT - 13.85 * cm,
                     1.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(11.3 * cm, PAGE_HEIGHT - 13.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Τηλ:')
    canvas.drawText(textobject)
    # TEL Value
    canvas.roundRect(12.5 * cm, PAGE_HEIGHT - 13.85 * cm,
                     6.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(13 * cm, PAGE_HEIGHT - 13.80 * cm)
    font_size = calculate_font_size(10, 6.5, info['telephone'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['telephone'])
    canvas.drawText(textobject)
    # Residence Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 14.85 * cm,
                     3 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 14.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Τόπος Κατοικίας:')
    canvas.drawText(textobject)
    # Residence Value
    canvas.roundRect(5 * cm, PAGE_HEIGHT - 14.85 * cm,
                     3.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(5.5 * cm, PAGE_HEIGHT - 14.80 * cm)
    font_size = calculate_font_size(10, 3.5,
                                    info['place_of_residence'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['place_of_residence'])
    canvas.drawText(textobject)
    # Street Box
    canvas.roundRect(8.5 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.7 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(8.8 * cm, PAGE_HEIGHT - 14.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Οδός:')
    canvas.drawText(textobject)
    # Street Value
    canvas.roundRect(10.2 * cm, PAGE_HEIGHT - 14.85 * cm,
                     3.1 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(10.7 * cm, PAGE_HEIGHT - 14.80 * cm)
    font_size = calculate_font_size(10, 3.1, info['street'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['street'])
    canvas.drawText(textobject)
    # Street Number Box
    canvas.roundRect(13.3 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(13.6 * cm, PAGE_HEIGHT - 14.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Αριθ:')
    canvas.drawText(textobject)
    # Street Number Value
    canvas.roundRect(14.8 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.1 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(14.95 * cm, PAGE_HEIGHT - 14.80 * cm)
    font_size = calculate_font_size(10, 1.1, info['street_number'], 0.15, 0.15)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['street_number'])
    canvas.drawText(textobject)
    # Postal Code Box
    canvas.roundRect(15.9 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.1 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(16.2 * cm, PAGE_HEIGHT - 14.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Τ.Κ:')
    canvas.drawText(textobject)
    # Postal Code Value
    canvas.roundRect(17 * cm, PAGE_HEIGHT - 14.85 * cm,
                     2 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(17.5 * cm, PAGE_HEIGHT - 14.80 * cm)
    font_size = calculate_font_size(10, 2, info['postal_code'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['postal_code'])
    canvas.drawText(textobject)
    # TAX ID Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 15.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(3.5 * cm, PAGE_HEIGHT - 15.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Α.Φ.Μ:')
    canvas.drawText(textobject)
    # TAX ID Value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 15.85 * cm,
                     4 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(7 * cm, PAGE_HEIGHT - 15.80 * cm)
    font_size = calculate_font_size(10, 4, info['tax_id'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['tax_id'])
    canvas.drawText(textobject)
    # EMAIL Box
    canvas.roundRect(10.5 * cm, PAGE_HEIGHT - 15.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(11.3 * cm, PAGE_HEIGHT - 15.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='E-mail:')
    canvas.drawText(textobject)
    # EMAIL Value
    canvas.roundRect(13 * cm, PAGE_HEIGHT - 15.85 * cm,
                     6 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(13.5 * cm, PAGE_HEIGHT - 15.75 * cm)
    font_size = calculate_font_size(10, 6, info['email'], 0.5, 0.5)
    textobject.setFont('Roboto-Regular', font_size)
    textobject.textLine(text=info['email'])
    canvas.drawText(textobject)
    # RESPONSIBILITY TEXT
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 18 * cm, 17 * cm,
                     1 * cm, 2, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.15 * cm, PAGE_HEIGHT - 17.4 * cm)
    textobject.setFont('Roboto-Regular', 9)
    wrap_text = "\n".join(wrap(responsibility_text, 110))
    textobject.textLines(wrap_text)
    canvas.drawText(textobject)
    
    # Declaration text
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 24 * cm, 17 * cm,
                     5 * cm, 2, stroke=1, fill=0)
    draw_field(canvas, info['declaration_text'],
               2.2 * cm, PAGE_HEIGHT - 23 * cm,
               16 * cm, 10 * cm)
    
    # AKNOWLEDGMENT TEXT
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 27.2 * cm, 17 * cm,
                     2.2 * cm, 2, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 25.5 * cm)
    textobject.setFont('Roboto-Regular', 9)
    wrap_text = "\n".join(wrap(aknowledgment_text, 100))
    textobject.textLines(wrap_text)
    canvas.drawText(textobject)
    canvas.restoreState()


# Convert points to centimeters
def pt_to_cm(pt):
    return "%.05f" % (pt / 28.346)


# Calculate Recursively the appropriate font size
def calculate_font_size(font_size, avail_space, text, start_margin,
                        end_margin):
    textWidth = stringWidth(text, 'Roboto-Regular', font_size)
    margins = start_margin + end_margin
    if(float(pt_to_cm(textWidth)) < avail_space - margins):
        return float("%.01f" % font_size)
    else:
        return calculate_font_size(font_size - 0.1, avail_space, text,
                                   start_margin, end_margin)


def make_later_pages_hf(canvas, doc):
    canvas.saveState()
    canvas.setFont('Roboto-Regular', 9)
    canvas.drawString(PAGE_WIDTH - 7 * cm, PAGE_HEIGHT - 2 * cm,
                      "%s %d" % (pageinfo, doc.page))
    canvas.restoreState()


def make_heading(element, contents):
    for pcontent in contents:
        elements.append(Paragraph(pcontent, styles["DilosiHeading"]))


def make_intro(elements, contents):
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(contents, styles["Dilosi"]))


def make_signature(elements):
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


doc = SimpleDocTemplate("solemn_declaration.pdf", pagesize=A4)

elements = []

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Dilosi',
                          fontName='Roboto-Regular',
                          fontSize=12,
                          leading=16,
                          alignment=TA_JUSTIFY))

styles.add(ParagraphStyle(name='DilosiBold',
                          fontName='Roboto-Bold',
                          fontSize=9,
                          leading=16,
                          alignment=TA_JUSTIFY))

styles.add(ParagraphStyle(name='DilosiHeading',
                          fontName='Roboto-Bold',
                          fontSize=16,
                          alignment=TA_CENTER,
                          spaceAfter=5))

styles.add(ParagraphStyle(name='DilosiSignature',
                          fontName='Roboto-Regular',
                          fontSize=12,
                          alignment=TA_RIGHT))
info = load_results('data.json')

title = 'Υπεύθυνη Δήλωση'
article = '(άρθρο 8 Ν.1599/1986)'
subtitle = 'Η ακρίβεια των στοιχείων που υποβάλλονται με αυτή τη δήλωση μπορεί'
' να ελεγχθεί με βάση το αρχείο άλλων υπηρεσιών (άρθρο 8 παρ. 4 Ν. 1599/1986)'
responsibility_text = 'Με ατομική μου ευθύνη και γνωρίζοντας τις κυρώσεις, που'
' προβλέπονται από τις διατάξεις της παρ. 6 του άρθρου 22 του Ν. 1599/1986,'
'δηλώνω ότι:'
aknowledgment_text = 'Γνωρίζω ότι: Όποιος εν γνώσει του δηλώνει ψευδή γεγονότα'
' ή αρνείται ή αποκρύπτει τα αληθινά με έγγραφη υπεύθυνη δήλωση του άρθρου 8 '
'τιμωρείται με φυλάκιση τουλάχιστον τριών μηνών. Εάν ο υπαίτιος αυτών των '
'πράξεων σκόπευε να προσπορίσει στον εαυτόν του ή σε άλλον περιουσιακό όφελος '
'βλάπτοντας τρίτον ή σκόπευε να βλάψει άλλον, τιμωρείται με κάθειρξη μέχρι 10 '
'ετών.'

make_heading(elements, [title])
make_heading(elements, [article])
elements.append(Spacer(1, 12))
make_intro(elements, subtitle)
elements.append(PageBreak())
make_signature(elements)

doc.build(elements, onFirstPage=make_first_page_hf,
          onLaterPages=make_later_pages_hf)
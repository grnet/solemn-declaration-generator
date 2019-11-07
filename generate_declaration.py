import json
import os.path

from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Frame
from reportlab.platypus import Spacer, Image
from reportlab.platypus import PageBreak
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

def create_para(contents, width, height,
                font_name='Roboto-Regular',
                font_size=10):
    style = ParagraphStyle('default',
                           fontName=font_name,
                           fontSize=font_size)
    paragraph = Paragraph(contents, style)
    paragraph, _ = shrink_to_fit(paragraph, style, width, height)
    return paragraph

def draw_para(canvas, contents, origin_x, origin_y, width, height,
              font_name='Roboto-Regular',
              font_size=10):
    paragraph = create_para(contents, 
                            width, height,
                            font_name=font_name,
                            font_size=font_size)
    paragraph.drawOn(canvas, origin_x, origin_y)    

def make_first_page_hf(canvas, doc):
    canvas.saveState()
    canvas.drawImage('coat_of_arms_of_greece.png',
                     x=PAGE_WIDTH - PAGE_WIDTH/2 - 1.75 * cm / 2,
                     y=PAGE_HEIGHT - 2.7 * cm,
                     width=1.75 * cm,
                     height=1.75 * cm)
    # Subtitle
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 6.1 * cm,
                     17 * cm, 1.5 * cm, 4, stroke=1, fill=0)
    # Frame Rectangle
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 15.85 * cm,
                     17 * cm, 9 * cm, 3, stroke=1, fill=0)

    # Recipient box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 7.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Προς:<super>(1)</super>',
              2.1 * cm, PAGE_HEIGHT - 7.8 * cm,
              2.5 * cm, 1* cm,
              font_name='Roboto-Bold',
              font_size=9)

    # Recipient value
    canvas.roundRect(4.5 * cm, PAGE_HEIGHT - 7.85 * cm,
                     14.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, info['to'],
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
    draw_para(canvas, info['name'],
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
    draw_para(canvas, info['surname'],
               13.5 * cm, PAGE_HEIGHT - 8.80 * cm,
               5 * cm, 1 * cm)

    # Father's name box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 9.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 9.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Όνομα και Επώνυμο Πατέρα:')
    canvas.drawText(textobject)

    # Father's name value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 9.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, info['father_name'],
               7.5 * cm, PAGE_HEIGHT - 9.80 * cm,
               11 * cm, 1 * cm)
    # Mother Name Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 10.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.05 * cm, PAGE_HEIGHT - 10.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Όνομα και Επώνυμο Μητέρας:')
    canvas.drawText(textobject)
    # Mother Name Value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 10.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, info['mother_name'],
               7.5 * cm, PAGE_HEIGHT - 10.80 * cm,
               11 * cm, 1 * cm)
    
    # Birthday box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 11.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Ημερομηνία Γέννησης:<super>(2)</super>',
              2.1 * cm, PAGE_HEIGHT - 11.8 * cm,
              5 * cm, 1* cm,
              font_name='Roboto-Bold',
              font_size=9)
    

    # Birth Date Value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 11.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, info['date_of_birth'],
               7.5 * cm, PAGE_HEIGHT - 11.80 * cm,
               11 * cm, 1 * cm)
    # Birthplace Box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 12.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    textobject = canvas.beginText()
    textobject.setTextOrigin(2.1 * cm, PAGE_HEIGHT - 12.80 * cm)
    textobject.setFont('Roboto-Bold', 9)
    textobject.textLine(text='Τόπος Γέννησης:')
    canvas.drawText(textobject)
    # Birthplace Value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 12.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, info['birth_place'],
               7.5 * cm, PAGE_HEIGHT - 12.80 * cm,
               11 * cm, 1 * cm)
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
    draw_para(canvas, info['id_number'],
               7 * cm, PAGE_HEIGHT - 13.80 * cm,
               3.5 * cm, 1 * cm)
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
    draw_para(canvas, info['telephone'],
               13 * cm, PAGE_HEIGHT - 13.80 * cm,
               5.5 * cm, 1 * cm)
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
    draw_para(canvas, info['place_of_residence'],
               5.5 * cm, PAGE_HEIGHT - 14.80 * cm,
               2.5 * cm, 1 * cm)
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
    draw_para(canvas, info['street'],
               10.7 * cm, PAGE_HEIGHT - 14.80 * cm,
               2.1 * cm, 1 * cm)
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
    draw_para(canvas, info['street_number'],
               14.9 * cm, PAGE_HEIGHT - 14.80 * cm,
               0.9 * cm, 1 * cm)
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
    draw_para(canvas, info['postal_code'],
               17.5 * cm, PAGE_HEIGHT - 14.80 * cm,
               1 * cm, 1 * cm)
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
    draw_para(canvas, info['tax_id'],
               7 * cm, PAGE_HEIGHT - 15.80 * cm,
               3 * cm, 1 * cm)
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
    
    # Preamble text
    # canvas.roundRect(2 * cm, PAGE_HEIGHT - 18 * cm, 17 * cm,
    #                  1 * cm, 2, stroke=1, fill=0)
    draw_para(canvas, PREAMBLE,
               2.2 * cm, PAGE_HEIGHT - 17.40 * cm,
               16 * cm, 2 * cm)
    
    # Declaration text
    draw_para(canvas, info['declaration_text'],
               2.2 * cm, PAGE_HEIGHT - 21.5 * cm,
               16 * cm, 10 * cm)

    # Footnotes
    fn_frame = Frame(2.2 * cm,
                     PAGE_HEIGHT - 28 * cm,
                     16 * cm, 3 * cm)
    footnotes = []
    recipient = create_para(RECIPIENT_FN,
                           16 * cm, 1 * cm,
                           font_size=8)
    footnotes.append(recipient)        
    numerals = create_para(NUMERALS_FN,
                           16 * cm, 1 * cm,
                           font_size=8)
    footnotes.append(numerals)    
    sanctions = create_para(SANCTIONS_FN,
                            16 * cm, 3 * cm,
                            font_size=8)
    footnotes.append(sanctions)
    fn_frame.addFromList(footnotes, canvas)

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
    elements.append(Paragraph(contents, styles["Warning"]))


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
styles.add(ParagraphStyle(name='Warning',
                          fontName='Roboto-Regular',
                          fontSize=8,
                          leading=16,
                          alignment=TA_CENTER))

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

WARNING = ('Η ακρίβεια των στοιχείων που υποβάλλονται με αυτή τη δήλωση '
           'μπορεί να ελεγχθεί με βάση το αρχείο άλλων υπηρεσιών '
           '(άρθρο 8 παρ. 4 Ν. 1599/1986).')

PREAMBLE = ('Με ατομική μου ευθύνη και γνωρίζοντας τις κυρώσεις,'
            '<super>(3)</super> '
            'που προβλέπονται από τις διατάξεις της παρ. 6 του '
            'άρθρου 22 του Ν. 1599/1986, δηλώνω ότι:')

RECIPIENT_FN= ('(1) Αναγράφεται από τον ενδιαφερόμενο πολίτη ή αρχή ή '
               'υπηρεσία του δημόσιου τομέα όπου απευθύνεται η αίτηση.')

NUMERALS_FN = '(2) Αναγράφεται ολογράφως.'

SANCTIONS_FN = ('(3) Γνωρίζω ότι: Όποιος εν γνώσει του δηλώνει ψευδή γεγονότα '
                'ή αρνείται ή αποκρύπτει τα αληθινά με έγγραφη υπεύθυνη '
                'δήλωση του άρθρου 8 τιμωρείται με φυλάκιση τουλάχιστον τριών '
                'μηνών. Εάν ο υπαίτιος αυτών των πράξεων σκόπευε να '
                'προσπορίσει στον εαυτόν του ή σε άλλον περιουσιακό όφελος '
                'βλάπτοντας τρίτον ή σκόπευε να βλάψει άλλον, τιμωρείται με '
                'κάθειρξη μέχρι 10 ετών.')

make_heading(elements, [title])
make_heading(elements, [article])
elements.append(Spacer(1, 12))
make_intro(elements, WARNING)
elements.append(PageBreak())
make_signature(elements)

doc.build(elements, onFirstPage=make_first_page_hf,
          onLaterPages=make_later_pages_hf)

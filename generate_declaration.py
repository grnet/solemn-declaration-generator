import json
import os.path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Frame
from reportlab.platypus import Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from birthday_to_numeral import num_to_text_hundreds, num_to_text_thousands

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization.pkcs12 import (
    load_key_and_certificates
)
from endesive import pdf as endesivepdf

import datetime
import argparse
import uuid

import qrcode

PAGE_WIDTH, PAGE_HEIGHT = A4

MONTHS = [
    'Ιανουαρίου',
    'Φεβρουαρίου',
    'Μαρτίου',
    'Απριλίου',
    'Μαΐου',
    'Ιουνίου',
    'Ιουλίου',
    'Αυγούστου',
    'Σεπτεμβρίου',
    'Οκτωβρίου',
    'Νοεμβρίου',
    'Δεκεμβρίου'
]

GENDER_ARTICLE = {
    'm' : 'Ο',
    'f' : 'Η',
    'n' : 'Το',
    'mf' : 'Ο - Η'
}

GENDER_BYLINE = {
    'm' : 'Ο Δηλών',
    'f' : 'Η Δηλούσα',
    'n' : 'Το Δηλούν',
    'mf' : 'Ο - Η Δηλ.'
}


TITLE = 'Υπεύθυνη Δήλωση'
LAW = '(άρθρο 8 Ν.1599/1986)'

WARNING = ('Η ακρίβεια των στοιχείων που υποβάλλονται με αυτή τη δήλωση '
           'μπορεί να ελεγχθεί με βάση το αρχείο άλλων υπηρεσιών '
           '(άρθρο 8 παρ. 4 Ν. 1599/1986).')

PREAMBLE = ('Με ατομική μου ευθύνη και γνωρίζοντας τις κυρώσεις,'
            '<super>(3)</super> '
            'που προβλέπονται από τις διατάξεις της παρ. 6 του '
            'άρθρου 22 του Ν. 1599/1986, δηλώνω ότι:')

RECIPIENT_FN = ('(1) Αναγράφεται από τον ενδιαφερόμενο πολίτη ή αρχή ή '
                'υπηρεσία του δημόσιου τομέα όπου απευθύνεται η αίτηση.')

NUMERALS_FN = '(2) Αναγράφεται ολογράφως.'

SANCTIONS_FN = ('(3) Γνωρίζω ότι: Όποιος εν γνώσει του δηλώνει ψευδή γεγονότα '
                'ή αρνείται ή αποκρύπτει τα αληθινά με έγγραφη υπεύθυνη '
                'δήλωση του άρθρου 8 τιμωρείται με φυλάκιση τουλάχιστον τριών '
                'μηνών. Εάν ο υπαίτιος αυτών των πράξεων σκόπευε να '
                'προσπορίσει στον εαυτόν του ή σε άλλον περιουσιακό όφελος '
                'βλάπτοντας τρίτον ή σκόπευε να βλάψει άλλον, τιμωρείται με '
                'κάθειρξη μέχρι 10 ετών.')

PAGE_DESCR = "Υπεύθυνη Δήλωση"

DEFAULT_OUTPUT_FILE = 'solemn_declaration.pdf'

STYLES = getSampleStyleSheet()

def setup(config_filename, styles):
    
    with open(config_filename, 'r') as config_file:
        config_data = json.load(config_file)
    
    for path_font_regular, path_font_bold in zip(config_data['font-regular'],
                                                 config_data['font-bold']):
        if os.path.exists(path_font_regular) and os.path.exists(path_font_bold):
            pdfmetrics.registerFont(TTFont('Font-Regular', path_font_regular))
            pdfmetrics.registerFont(TTFont('Font-Bold', path_font_bold))
            break
                       
    styles.add(ParagraphStyle(name='Warning',
                            fontName='Font-Regular',
                            fontSize=8,
                            leading=16,
                            alignment=TA_CENTER))

    styles.add(ParagraphStyle(name='DeclBold',
                            fontName='Font-Bold',
                            fontSize=9,
                            leading=16,
                            alignment=TA_JUSTIFY))

    styles.add(ParagraphStyle(name='DeclHeading',
                            fontName='Font-Bold',
                            fontSize=16,
                            alignment=TA_CENTER,
                            spaceAfter=5))

    styles.add(ParagraphStyle(name='DeclSubHeading',
                            fontName='Font-Bold',
                            fontSize=9,
                            alignment=TA_CENTER,
                            spaceAfter=5))

    styles.add(ParagraphStyle(name='NameSignature',
                            fontName='Font-Regular',
                            fontSize=10,
                            alignment=TA_CENTER))


def load_payload(payload_filename):
    with open(payload_filename, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data


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
                font_name='Font-Regular',
                font_size=10):
    style = ParagraphStyle('default',
                           fontName=font_name,
                           fontSize=font_size)
    paragraph = Paragraph(contents, style)
    paragraph, _ = shrink_to_fit(paragraph, style, width, height)
    return paragraph


def draw_para(canvas, contents, origin_x, origin_y, width, height,
              font_name='Font-Regular',
              font_size=10):
    paragraph = create_para(contents,
                            width, height,
                            font_name=font_name,
                            font_size=font_size)
    paragraph.drawOn(canvas, origin_x, origin_y)


def make_first_page(canvas, doc, qr, payload):

    canvas.saveState()

    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    payload['uuid'] = uuid.uuid4().hex
    digest.update(json.dumps(payload).encode('utf-8'))
    digest_hex = digest.finalize().hex()
    payload['digest'] = digest_hex

    if args.qr_code:
        # QR code
        qr = qrcode.make(digest_hex)
        canvas.drawInlineImage(qr,
                            x=PAGE_WIDTH - 5 * cm,
                            y=PAGE_HEIGHT - 3.5 * cm,
                            width=2.5 * cm,
                            height=2.5 * cm)

        draw_para(canvas, f'Κωδικός: {digest_hex}',
                0.5 * cm, PAGE_HEIGHT - 0.75 * cm,
                15 * cm, 0.5 * cm,
                font_name='Font-Regular',
                font_size=9)

    # Coat of arms
    canvas.drawImage('coat_of_arms_of_greece.png',
                     x=PAGE_WIDTH - PAGE_WIDTH / 2 - 1.75 * cm / 2,
                     y=PAGE_HEIGHT - 2.7 * cm,
                     width=1.75 * cm,
                     height=1.75 * cm)
    # Subtitle
    canvas.setLineWidth(0.5)
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 6.1 * cm,
                     17 * cm, 1.5 * cm, 4, stroke=1, fill=0)
    canvas.setLineWidth(1)
    # Frame Rectangle
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 15.85 * cm,
                     17 * cm, 9 * cm, 3, stroke=1, fill=0)

    # Recipient box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 7.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Προς:<super>(1)</super>',
              2.1 * cm, PAGE_HEIGHT - 7.8 * cm,
              2.5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Recipient value
    canvas.roundRect(4.5 * cm, PAGE_HEIGHT - 7.85 * cm,
                     14.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['to'],
              5 * cm, PAGE_HEIGHT - 7.80 * cm,
              13 * cm, 1 * cm)

    # Name box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 8.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, f'{GENDER_ARTICLE[payload["gender"]]} Όνομα:',
              2.1 * cm, PAGE_HEIGHT - 8.85 * cm,
              2.5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Name value
    canvas.roundRect(4.5 * cm, PAGE_HEIGHT - 8.85 * cm, 6 * cm, 1 * cm, 0,
                     stroke=1, fill=0)
    draw_para(canvas, payload['name'],
              5 * cm, PAGE_HEIGHT - 8.80 * cm,
              5 * cm, 1 * cm)

    # Surname box
    canvas.roundRect(10.5 * cm, PAGE_HEIGHT - 8.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Επώνυμο:',
              11 * cm, PAGE_HEIGHT - 8.85 * cm,
              2.5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Surname value
    canvas.roundRect(13 * cm, PAGE_HEIGHT - 8.85 * cm,
                     6 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['surname'],
              13.5 * cm, PAGE_HEIGHT - 8.80 * cm,
              5 * cm, 1 * cm)

    # Father's name box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 9.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Όνομα και Επώνυμο Πατέρα:',
              2.1 * cm, PAGE_HEIGHT - 9.80 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Father's name value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 9.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['father_name'],
              7.5 * cm, PAGE_HEIGHT - 9.80 * cm,
              11 * cm, 1 * cm)

    # Mother's name box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 10.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Όνομα και Επώνυμο Μητέρας:',
              2.1 * cm, PAGE_HEIGHT - 10.80 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Mother's name value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 10.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['mother_name'],
              7.5 * cm, PAGE_HEIGHT - 10.80 * cm,
              11 * cm, 1 * cm)

    # Birthday box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 11.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Ημερομηνία Γέννησης:<super>(2)</super>',
              2.1 * cm, PAGE_HEIGHT - 11.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Birth Date val
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 11.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    year, month, day = (int(x) for x in payload['date_of_birth'].split('-'))
    day_str = (num_to_text_hundreds(day, True).capitalise()
               if day != 1 else "Πρώτη")
    month_str = MONTHS[month - 1]
    year_str = num_to_text_thousands(year)
    birthday_w = f'{day_str} {month_str} {year_str}'
    draw_para(canvas, birthday_w,
              7.5 * cm, PAGE_HEIGHT - 11.80 * cm,
              11 * cm, 1 * cm)

    # Birthplace box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 12.85 * cm,
                     5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Τόπος Γέννησης:',
              2.1 * cm, PAGE_HEIGHT - 12.8 * cm,
              11 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Birthplace value
    canvas.roundRect(7 * cm, PAGE_HEIGHT - 12.85 * cm,
                     12 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['birth_place'],
              7.5 * cm, PAGE_HEIGHT - 12.80 * cm,
              11 * cm, 1 * cm)

    # ID box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 13.85 * cm,
                     4.7 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Αριθμός Δελτίου Ταυτότητας:',
              2.1 * cm, PAGE_HEIGHT - 13.8 * cm,
              11 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # ID value
    canvas.roundRect(6.7 * cm, PAGE_HEIGHT - 13.85 * cm,
                     4.4 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['id_number'],
              7 * cm, PAGE_HEIGHT - 13.80 * cm,
              3.5 * cm, 1 * cm)

    # Tel box
    canvas.roundRect(11.1 * cm, PAGE_HEIGHT - 13.85 * cm,
                     1.4 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Τηλ.:',
              11.3 * cm, PAGE_HEIGHT - 13.8 * cm,
              3 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Tel value
    canvas.roundRect(12.5 * cm, PAGE_HEIGHT - 13.85 * cm,
                     6.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['telephone'],
              13 * cm, PAGE_HEIGHT - 13.80 * cm,
              5.5 * cm, 1 * cm)

    # Residence box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 14.85 * cm,
                     3 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Τόπος Κατοικίας:',
              2.1 * cm, PAGE_HEIGHT - 14.8 * cm,
              3 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Residence value
    canvas.roundRect(5 * cm, PAGE_HEIGHT - 14.85 * cm,
                     3.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['place_of_residence'],
              5.5 * cm, PAGE_HEIGHT - 14.80 * cm,
              2.5 * cm, 1 * cm)

    # Street box
    canvas.roundRect(8.5 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.7 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Οδός:',
              8.8 * cm, PAGE_HEIGHT - 14.8 * cm,
              3 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Street Value
    canvas.roundRect(10.2 * cm, PAGE_HEIGHT - 14.85 * cm,
                     3.1 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['street'],
              10.7 * cm, PAGE_HEIGHT - 14.80 * cm,
              2.1 * cm, 1 * cm)

    # Street Number box
    canvas.roundRect(13.3 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Αριθ.:',
              13.6 * cm, PAGE_HEIGHT - 14.8 * cm,
              2 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Street Number Value
    canvas.roundRect(14.8 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.1 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['street_number'],
              14.9 * cm, PAGE_HEIGHT - 14.80 * cm,
              0.9 * cm, 1 * cm)

    # Postal Code box
    canvas.roundRect(15.9 * cm, PAGE_HEIGHT - 14.85 * cm,
                     1.1 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Τ.Κ.:',
              16.1 * cm, PAGE_HEIGHT - 14.8 * cm,
              2 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # Postal Code Value
    canvas.roundRect(17 * cm, PAGE_HEIGHT - 14.85 * cm,
                     2 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['postal_code'],
              17.5 * cm, PAGE_HEIGHT - 14.80 * cm,
              1 * cm, 1 * cm)

    # ΤΙΝ box
    canvas.roundRect(2 * cm, PAGE_HEIGHT - 15.85 * cm,
                     4.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Α.Φ.Μ.:',
              3.5 * cm, PAGE_HEIGHT - 15.8 * cm,
              3 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # TIN Value
    canvas.roundRect(6.5 * cm, PAGE_HEIGHT - 15.85 * cm,
                     4 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['tax_id'],
              7 * cm, PAGE_HEIGHT - 15.80 * cm,
              3 * cm, 1 * cm)

    # email box
    canvas.roundRect(10.5 * cm, PAGE_HEIGHT - 15.85 * cm,
                     2.5 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, 'Ηλ. Ταχ.:',
              11.15 * cm, PAGE_HEIGHT - 15.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Bold',
              font_size=9)

    # email value
    canvas.roundRect(13 * cm, PAGE_HEIGHT - 15.85 * cm,
                     6 * cm, 1 * cm, 0, stroke=1, fill=0)
    draw_para(canvas, payload['email'],
              13.5 * cm, PAGE_HEIGHT - 15.75 * cm,
              5.5 * cm, 1 * cm)

    # Preamble text
    draw_para(canvas, PREAMBLE,
              2.2 * cm, PAGE_HEIGHT - 17.40 * cm,
              16 * cm, 2 * cm)

    # Declaration text
    draw_para(canvas, payload['declaration_text'],
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


def make_later_pages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Font-Regular', 9)
    canvas.drawString(PAGE_WIDTH - 7 * cm, PAGE_HEIGHT - 2 * cm,
                      "%s %d" % (PAGE_DESCR, doc.page))
    canvas.restoreState()


def make_heading(element, contents):
    for pcontent in contents:
        elements.append(Paragraph(pcontent, STYLES["DeclHeading"]))


def make_subheading(element, contents):
    for pcontent in contents:
        elements.append(Paragraph(pcontent, STYLES["DeclSubHeading"]))


def make_intro(elements, contents):
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(contents, STYLES["Warning"]))


def make_human_signature(elements, payload):
    signature = [
        [
            Spacer(0 * cm, 17 * cm),
            Paragraph(payload['date'], STYLES['NameSignature'])
        ],
        [
            Spacer(0 * cm, 0 * cm),
            Paragraph(GENDER_BYLINE[payload['gender']],
                      STYLES['NameSignature'])
        ],
        [
            Spacer(0 * cm, 1 * cm),
            Paragraph(f'{payload["name"]} {payload["surname"]}',
                      STYLES['NameSignature'])
        ]
    ]

    signature = Table(signature)

    elements.append(signature)


def crypto_sign(certificate_filename, password, pdf_filename):

    backend = default_backend()

    with open(certificate_filename, 'rb') as cert_in:
        cert_data = cert_in.read()
    cert = load_key_and_certificates(cert_data, password.encode('utf-8'), 
                                     backend)

    with open(pdf_filename, 'rb') as decl_file:
        decl_pdf = decl_file.read()

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S+02'00'")

    dct = {
        b'sigflags': 3,
        b'sigpage': 0,
        b'sigbutton': True,
        b'contact': b'support@grnet.gr',
        b'location': b'Athens',
        b'signingdate': timestamp.encode('utf-8'),
        b'reason': b'GRNET Signing Service',
        b'signature': f'Verified by GRNET S.A. {timestamp}'.encode('utf-8'),
        b'signaturebox': (450, 0, 600, 100),
    }

    decl_signed = endesivepdf.cms.sign(decl_pdf,
                                       dct,
                                       cert[0],
                                       cert[1],
                                       cert[2],
                                       'sha256'
                                       )

    filename, file_extension = os.path.splitext(pdf_filename)
    signed_pdf_filename = f'{filename}-signed{file_extension}'
    with open(signed_pdf_filename, 'wb') as decl_signed_file:
        decl_signed_file.write(decl_pdf)
        decl_signed_file.write(decl_signed)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output',
                        help='PDF output file',
                        default=DEFAULT_OUTPUT_FILE)
    parser.add_argument('-c', '--certificate', help='certificate file')
    parser.add_argument('-p', '--password', help='certificate password',
                        default=None)
    parser.add_argument('-q', '--qr_code', 
                        action='store_true',
                        help='embed reference and QR code')
    parser.add_argument('-s', '--setup',
                        default='setup.json',
                        help='setup configuration file')
    args = parser.parse_args()

    setup(args.setup, STYLES)

    doc = SimpleDocTemplate(args.output, pagesize=A4)

    elements = []

    payload = load_payload('data.json')
    if 'gender' not in payload:
        payload['gender'] = 'mf'

    make_heading(elements, [TITLE])
    make_subheading(elements, [LAW])
    elements.append(Spacer(1, 12))
    make_intro(elements, WARNING)
    make_human_signature(elements, payload)

    def make_first_page_ld(canvas, doc): return make_first_page(canvas, doc,
                                                                args.qr_code,
                                                                payload)

    decl = doc.build(elements,
                     onFirstPage=make_first_page_ld,
                     onLaterPages=make_later_pages)

    if args.certificate and args.password:
        crypto_sign(args.certificate, args.password, args.output)
    print(payload['digest'])

import json
import os.path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table
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
    'm': 'Ο',
    'f': 'Η',
    'n': 'Το',
    'mf': 'Ο - Η'
}

GENDER_SUFFIX = {
    'm': 'ος',
    'f': 'η',
    'n': 'ο'
}

TITLE = 'ΒΕΒΑΙΩΣΗ'

INFO = ['ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ', 'ΥΠΟΥΡΓΕΙΟ ΕΣΩΤΕΡΙΚΩΝ',
        'ΓΕΝ. Δ/ΝΣΗ ΕΣΩΤΕΡΙΚΩΝ & ΗΛΕΚΤΡΟΝΙΚΗΣ ΔΙΑΚΥΒΕΡΝΗΣΗΣ',
        'ΔΙΕΥΘΥΝΣΗ ΑΣΤΙΚΗΣ & ΔΗΜΟΤΙΚΗΣ ΚΑΤ/ΣΗΣ',
        'ΤΜΗΜΑ ΑΣΤΙΚΗΣ ΚΑΙ ΔΗΜΟΤΙΚΗΣ ΚΑΤ/ΣΗΣ']

SUBTITLE = ['Τα στοιχεία που περιλαμβάνονται στην παρούσα βεβαίωση προκύπτουν \
από το  Πληροφοριακό Σύστημα του Μητρώου Πολιτών και είναι ίδια με αυτά που \
περιέχονται στο πιστοποιητικό <b>Γέννησης.</b>',
            '%s κάτωθι δημότης είναι εγγεγραμμέν%s στο Δημοτολόγιο του Δήμου \
%s, στην %s (πρώην %s της Δημοτικής Ενότητας %s)<super>1</super> οικογενειακή \
μερίδα του Δημοτολογίου και σειρά %s (πρώην Α/Α μέλους) με τα κάτωθι στοιχεία:']


PAGE_DESCR = "Βεβαίωση Γέννησης"


DEFAULT_OUTPUT_FILE = 'birth_affir.pdf'

STYLES = getSampleStyleSheet()


def setup(config_filename, styles):

    with open(config_filename, 'r') as config_file:
        config_data = json.load(config_file)

    for path_font_regular, path_font_bold, path_font_bold_italic \
        in zip(config_data['font-regular'],
               config_data['font-bold'],
               config_data['font-bold-italic']):
        if os.path.exists(path_font_regular) and os.path.exists(path_font_bold):
            pdfmetrics.registerFont(
                TTFont('Font-Regular', path_font_regular))
            pdfmetrics.registerFont(TTFont('Font-Bold', path_font_bold))
            pdfmetrics.registerFont(
                TTFont('Font-Bold-Italic', path_font_bold_italic))
            break

    styles.add(ParagraphStyle(name='Bold',
                              fontName='Font-Bold',
                              fontSize=9,
                              leading=16,
                              alignment=TA_JUSTIFY))

    styles.add(ParagraphStyle(name='Heading',
                              fontName='Font-Bold',
                              fontSize=15,
                              alignment=TA_CENTER,
                              spaceAfter=5))

    styles.add(ParagraphStyle(name='Info',
                              fontName='Font-Bold',
                              fontSize=9,
                              alignment=TA_JUSTIFY,
                              spaceAfter=0,
                              leading=9))

    styles.add(ParagraphStyle(name='Subtitle',
                              fontName='Font-Regular',
                              fontSize=9,
                              alignment=TA_JUSTIFY,
                              spaceAfter=0,
                              leading=9))


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

    # heading line
    canvas.line(9.05 * cm, PAGE_HEIGHT - 7.5 * cm,
                PAGE_WIDTH - 9.05 * cm, PAGE_HEIGHT - 7.5 * cm)

    draw_para(canvas, 'Επώνυμο',
              3.2 * cm, PAGE_HEIGHT - 11.7 * cm, 2 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['surname'],
              10 * cm, PAGE_HEIGHT - 11.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if payload['secondsurname'] is not None:
        draw_para(canvas, payload['secondsurname'],
                  15 * cm, PAGE_HEIGHT - 11.7 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Όνομα',
              3.2 * cm, PAGE_HEIGHT - 12.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['firstname'],
              10 * cm, PAGE_HEIGHT - 12.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if payload['secondname'] is not None:
        draw_para(canvas, payload['secondname'],
                  14 * cm, PAGE_HEIGHT - 12.2 * cm, 4 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)
    if payload['thirdname'] is not None:
        draw_para(canvas, payload['thirdname'],
                  18 * cm, PAGE_HEIGHT - 12.2 * cm, 4 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Φύλο',
              3.2 * cm, PAGE_HEIGHT - 12.7 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['gender'],
              10 * cm, PAGE_HEIGHT - 12.7 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Όνομα Πατέρα',
              3.2 * cm, PAGE_HEIGHT - 13.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['fatherfirstname'],
              10 * cm, PAGE_HEIGHT - 13.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if payload['fathersecondname'] is not None:
        draw_para(canvas, payload['fathersecondname'],
                  15 * cm, PAGE_HEIGHT - 13.2 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Επώνυμο Πατέρα',
              3.2 * cm, PAGE_HEIGHT - 13.7 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['fathersurname'],
              10 * cm, PAGE_HEIGHT - 13.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if payload['fathersecondsurname'] is not None:
        draw_para(canvas, payload['fathersecondsurname'],
                  15 * cm, PAGE_HEIGHT - 13.7 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Όνομα Μητέρας',
              3.2 * cm, PAGE_HEIGHT - 14.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['motherfirstname'],
              10 * cm, PAGE_HEIGHT - 14.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if payload['mothersecondname'] is not None:
        draw_para(canvas, payload['mothersecondname'],
                  15 * cm, PAGE_HEIGHT - 14.2 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Επώνυμο Μητέρας',
              3.2 * cm, PAGE_HEIGHT - 14.7 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['mothersurname'],
              10 * cm, PAGE_HEIGHT - 14.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if payload['mothersecondsurname'] is not None:
        draw_para(canvas, payload['mothersecondsurname'],
                  15 * cm, PAGE_HEIGHT - 14.7 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Γένος Μητέρας',
              3.2 * cm, PAGE_HEIGHT - 15.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['mothergenos'] is not None:
        draw_para(canvas, payload['mothergenos'],
                  10 * cm, PAGE_HEIGHT - 15.2 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ειδικός Εκλογικός αριθμός',
              3.2 * cm, PAGE_HEIGHT - 15.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['eklspecialno'],
              10 * cm, PAGE_HEIGHT - 15.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ημερομηνία γέννησης',
              3.2 * cm, PAGE_HEIGHT - 16.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['birthdate'],
              10 * cm, PAGE_HEIGHT - 16.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ημερομηνία γέννησης ολογράφως',
              3.2 * cm, PAGE_HEIGHT - 16.7 * cm, 6 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    day, month, year = (int(x)
                        for x in payload['birthdate'].split('-')[0].replace('/', '-').split('-'))
    day_str = (num_to_text_hundreds(day, True).capitalize()
               if day != 1 else "Πρώτη")
    month_str = MONTHS[month - 1]
    year_str = num_to_text_thousands(year)
    birthday_w = f'{day_str} {month_str} {year_str}'
    draw_para(canvas, birthday_w,
              10 * cm, PAGE_HEIGHT - 16.7 * cm, 10 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Οικισμός γέννησης',
              3.2 * cm, PAGE_HEIGHT - 17.2 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['birthoikismos'] is not None:
        draw_para(canvas, payload['birthoikismos'],
                  10 * cm, PAGE_HEIGHT - 17.2 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Τοπ./Δημ. Κοινότητα ή Κοινότητα γέννησης',
              3.2 * cm, PAGE_HEIGHT - 18.1 * cm, 5 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['birthmuniccomm'] is not None:
        draw_para(canvas, payload['birthmuniccomm'],
                  10 * cm, PAGE_HEIGHT - 18.1 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Δημοτική Ενότητα γέννησης',
              3.2 * cm, PAGE_HEIGHT - 18.6 * cm, 5 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['birthmunicipalunit'] is not None:
        draw_para(canvas, payload['birthmunicipalunit'],
                  10 * cm, PAGE_HEIGHT - 18.6 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Δήμος γέννησης',
              3.2 * cm, PAGE_HEIGHT - 19.1 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['birthmunicipal'],
              10 * cm, PAGE_HEIGHT - 19.1 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Πόλη γέννησης',
              3.2 * cm, PAGE_HEIGHT - 19.6 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['birthcountry'] != 'Ελλάδα':
        draw_para(canvas, payload['birthregion'],
                  10 * cm, PAGE_HEIGHT - 19.6 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Νομός γέννησης',
              3.2 * cm, PAGE_HEIGHT - 20.1 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['birthregion'],
              10 * cm, PAGE_HEIGHT - 20.1 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Χώρα γέννησης',
              3.2 * cm, PAGE_HEIGHT - 20.6 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['birthcountry'],
              10 * cm, PAGE_HEIGHT - 20.6 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ιθαγένεια',
              3.2 * cm, PAGE_HEIGHT - 21.1 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['mainnationality'],
              10 * cm, PAGE_HEIGHT - 21.1 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ημ/νία Κτήσης Ιθαγένειας<super>3</super>',
              3.2 * cm, PAGE_HEIGHT - 21.6 * cm, 4 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['grnatgaindate'],
              10 * cm, PAGE_HEIGHT - 21.6 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ημ/νία Κτήσης Δημοτικότητας',
              3.2 * cm, PAGE_HEIGHT - 22.1 * cm, 5 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, payload['gainmunrecdate'],
              10 * cm, PAGE_HEIGHT - 22.1 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'ΑΜΚΑ',
              3.2 * cm, PAGE_HEIGHT - 22.6 * cm, 1 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    draw_para(canvas, 'Μητρώο Αρρένων',
              3.2 * cm, PAGE_HEIGHT - 23.1 * cm, 3 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['gender'] == 'Άρρεν':
        if payload['mansdecentraladmin'] is not None:
            draw_para(canvas, payload['mansdecentraladmin'],
                      10 * cm, PAGE_HEIGHT - 23.1 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)
        if payload['mansmunicipalityname'] is not None:
            draw_para(canvas, payload['mansmunicipalityname'],
                      13 * cm, PAGE_HEIGHT - 23.1 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)
        if payload['mansmunicipalunitname'] is not None:
            draw_para(canvas, payload['mansmunicipalunitname'],
                      16 * cm, PAGE_HEIGHT - 23.1 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)
        if payload['mansmuniccommname'] is not None:
            draw_para(canvas, payload['mansmuniccommname'],
                      19 * cm, PAGE_HEIGHT - 23.1 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Αριθμός - Έτος Μ.Α',
              3.2 * cm, PAGE_HEIGHT - 23.6 * cm, 3 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['gender'] == 'Άρρεν':
        if payload['mansdecentraladmin'] is not None:
            draw_para(canvas, payload['mansrecordaa'],
                      10 * cm, PAGE_HEIGHT - 23.6 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)
        if payload['mansdecentraladmin'] is not None:
            draw_para(canvas, payload['mansrecordyear'],
                      10 * cm, PAGE_HEIGHT - 23.6 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Εγγραφή Μ.Α',
              3.2 * cm, PAGE_HEIGHT - 24.1 * cm, 3 * cm, 1 * cm,
              font_name='Font-Bold-Italic', font_size=9)

    if payload['gender'] == 'Άρρεν':
        if payload['mansreckind'] is not None:
            draw_para(canvas, payload['mansrecordaa'],
                      10 * cm, PAGE_HEIGHT - 24.1 * cm, 3 * cm, 1 * cm,
                      font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ο/Η Προϊστάμενος του Τμήματος Αστικής & Δημοτικής Κατάστασης',
              14 * cm, PAGE_HEIGHT - 27.5 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=10)

    canvas.restoreState()


def make_later_pages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Font-Regular', 9)
    canvas.drawString(PAGE_WIDTH - 7 * cm, PAGE_HEIGHT - 2 * cm,
                      "%s %d" % (PAGE_DESCR, doc.page))

    canvas.restoreState()


def make_heading(element, contents):
    for pcontent in contents:
        elements.append(Paragraph(pcontent, STYLES["Heading"]))


def make_info(element, contents):
    for pcontent in contents:
        elements.append(Paragraph(pcontent, STYLES["Info"]))


def make_subtitle(element, contents):
    elements.append(Paragraph(contents, STYLES["Subtitle"]))


def make_sub(element, contents, payload):
    contents = contents % (1, 2, 3, 4, 5, 6, 7)
    elements.append(Paragraph(contents, STYLES["Subtitle"]))


def make_text_intro(element, payload):
    content = 'Η παρούσα εκδόθηκε από αίτηση του ενδιαφέρομενου %s %s για :' \
        % (1, 2)
    element.append(Paragraph(content, STYLES["Subtitle"]))


def make_text(element, payload):
    Spacer(0 * cm, 1 * cm),
    content = 'djnskdjndskjcndskjcndskcjdnskcjdncksjncdksjnkjcnskcdjnckjsnck'
    element.append(Paragraph(content, STYLES["Subtitle"]))


def make_signature(element, payload):
    signature = [
        [
            Spacer(5.5 * cm, 3 * cm),
            Paragraph('<Ο/Η> αρμόδι<ος/α> υπάλληλος του <ΚΕΠ>',
                      STYLES['Subtitle'])
        ]
    ]

    signature = Table(signature)
    element.append(signature)


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

    payload = load_payload('birth_affir.json')
    elements.append(Spacer(0, 1 * cm))
    make_info(elements, INFO)
    elements.append(Spacer(0, 1.5 * cm))
    make_heading(elements, [TITLE])
    elements.append(Spacer(0, 1 * cm))
    make_subtitle(elements, SUBTITLE[0])
    elements.append(Spacer(0, 0.5 * cm))
    make_sub(elements, SUBTITLE[1], payload)
    elements.append(PageBreak())
    make_text_intro(elements, payload)
    make_text(elements, payload)
    make_signature(elements, payload)

    def make_first_page_ld(canvas, doc): return make_first_page(canvas, doc,
                                                                args.qr_code,
                                                                payload)

    decl = doc.build(elements,
                     onFirstPage=make_first_page_ld,
                     onLaterPages=make_later_pages)

    if args.certificate and args.password:
        crypto_sign(args.certificate, args.password, args.output)
    print(payload['digest'])

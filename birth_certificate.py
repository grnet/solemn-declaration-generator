import json
import os.path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph
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


TITLE = 'Απόσπασμα Ληξιαρχικής Πράξης Γέννησης'

INFO = ['ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ', 'ΝΟΜΟΣ:',
        'ΔΗΜΟΣ:', 'ΛΗΞΙΑΡΧΕΙΟ:', 'ΟΔΟΣ:', 'Τηλέφωνο:']


PAGE_DESCR = "Απόσπασμα Ληξιαρχικής Πράξης Γέννησης"


DEFAULT_OUTPUT_FILE = 'birth_cert.pdf'

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

    styles.add(ParagraphStyle(name='Bold',
                              fontName='Font-Bold',
                              fontSize=9,
                              leading=16,
                              alignment=TA_JUSTIFY))

    styles.add(ParagraphStyle(name='Heading',
                              fontName='Font-Bold',
                              fontSize=13,
                              alignment=TA_CENTER,
                              spaceAfter=5))

    styles.add(ParagraphStyle(name='Info',
                              fontName='Font-Regular',
                              fontSize=9,
                              alignment=TA_JUSTIFY,
                              spaceAfter=0,
                              leading=9))

    styles.add(ParagraphStyle(name='Notes',
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

    draw_para(canvas, payload['district'],
              4.5 * cm, PAGE_HEIGHT - 3.5 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['municipality'],
              4.5 * cm, PAGE_HEIGHT - 3.8 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['registry_office'],
              5 * cm, PAGE_HEIGHT - 4.1 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['street'],
              4 * cm, PAGE_HEIGHT - 4.4 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['telephone'],
              4.5 * cm, PAGE_HEIGHT - 4.7 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    # heading line
    canvas.line(2 * cm, PAGE_HEIGHT - 5.3 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 5.3 * cm)

    draw_para(canvas, 'ΣΤΟΙΧΕΙΑ ΛΗΞ.ΠΡΑΞΗΣ',
              2.1 * cm, PAGE_HEIGHT - 6 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=10)

    canvas.line(2.1 * cm, PAGE_HEIGHT - 6.05 * cm,
                PAGE_WIDTH - 14.9 * cm, PAGE_HEIGHT - 6.05 * cm)

    draw_para(canvas, 'Χαρακτηριστικά Ασφαλείας:',
              2.1 * cm, PAGE_HEIGHT - 6.5 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['insurance_attr'],
              6.3 * cm, PAGE_HEIGHT - 6.5 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Στοιχεία Ληξ. Πράξης Γέννησης (Αριθμός/τόμος/έτος):',
              2.1 * cm, PAGE_HEIGHT - 7 * cm, 8 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['birth_cert_info'],
              10 * cm, PAGE_HEIGHT - 7 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ημερομηνία δήλωσης:',
              2.1 * cm, PAGE_HEIGHT - 7.5 * cm, 8 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['decl_date'],
              5.5 * cm, PAGE_HEIGHT - 7.5 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'ΣΤΟΙΧΕΙΑ ΝΕΟΓΝΟΥ',
              2.1 * cm, PAGE_HEIGHT - 8 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=10)

    canvas.line(2.1 * cm, PAGE_HEIGHT - 8.05 * cm,
                PAGE_WIDTH - 15.45 * cm, PAGE_HEIGHT - 8.05 * cm)

    draw_para(canvas, 'Επώνυμο:',
              2.1 * cm, PAGE_HEIGHT - 8.5 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['newborn_surname'],
              3.8 * cm, PAGE_HEIGHT - 8.5 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Όνομα:',
              2.1 * cm, PAGE_HEIGHT - 9 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['newborn_name'],
              3.5 * cm, PAGE_HEIGHT - 9 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Φύλλο:',
              2.1 * cm, PAGE_HEIGHT - 9.5 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['newborn_gender'],
              3.5 * cm, PAGE_HEIGHT - 9.5 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ημερομηνία:',
              2.1 * cm, PAGE_HEIGHT - 10 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['newborn_date'],
              4.2 * cm, PAGE_HEIGHT - 10 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'ΑΜΚΑ:',
              2.1 * cm, PAGE_HEIGHT - 10.5 * cm, 1 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['newborn_amka'],
              3.5 * cm, PAGE_HEIGHT - 10.5 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Τόπος Γέννησης (Οδός, Αρ., ΤΚ, Δημ./Τοπ. Κοιν. , Δημ. Ενότ, Δήμος, Νομός Χώρα):',
              2.1 * cm, PAGE_HEIGHT - 12.7 * cm, 3 * cm, 5 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['newborn_birth_place'],
              4.5 * cm, PAGE_HEIGHT - 12.7 * cm, 2.5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Πατέρας',
              9 * cm, PAGE_HEIGHT - 13.2 * cm, 2 * cm, 1 * cm,
              font_name='Font-Bold', font_size=9)

    draw_para(canvas, 'Μητέρα',
              16 * cm, PAGE_HEIGHT - 13.2 * cm, 2 * cm, 1 * cm,
              font_name='Font-Bold', font_size=9)

    draw_para(canvas, 'ΣΤΟΙΧΕΙΑ ΓΟΝΕΩΝ',
              2.1 * cm, PAGE_HEIGHT - 13.7 * cm, 4 * cm, 1 * cm,
              font_name='Font-Regular', font_size=10)

    canvas.line(2.1 * cm, PAGE_HEIGHT - 13.75 * cm,
                PAGE_WIDTH - 15.6 * cm, PAGE_HEIGHT - 13.75 * cm)

    draw_para(canvas, 'Επώνυμο:',
              2.1 * cm, PAGE_HEIGHT - 14.2 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_surname'],
              8 * cm, PAGE_HEIGHT - 14.2 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_surname'],
              15 * cm, PAGE_HEIGHT - 14.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Όνομα:',
              2.1 * cm, PAGE_HEIGHT - 14.7 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_name'],
              8 * cm, PAGE_HEIGHT - 14.7 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_name'],
              15 * cm, PAGE_HEIGHT - 14.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ιθαγένεια:',
              2.1 * cm, PAGE_HEIGHT - 15.4 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_nationality'],
              8 * cm, PAGE_HEIGHT - 15.4 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_nationality'],
              15 * cm, PAGE_HEIGHT - 15.4 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Τόπος Κατοικίας (Οδός, Αρ., ΤΚ, Δημ/Τοπ. Κοιν.,Δημ. Ενότ, Δήμος, Νομός, Χώρα):',
              2.1 * cm, PAGE_HEIGHT - 16.7 * cm, 4.5 * cm, 5 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_nationality'],
              8 * cm, PAGE_HEIGHT - 16.7 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_nationality'],
              15 * cm, PAGE_HEIGHT - 16.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Πόλη Εξωτερικού:',
              2.1 * cm, PAGE_HEIGHT - 17.2 * cm, 3 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_foreign_city'],
              8 * cm, PAGE_HEIGHT - 17.2 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_foreign_city'],
              15 * cm, PAGE_HEIGHT - 17.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Δημοτολόγιο:',
              2.1 * cm, PAGE_HEIGHT - 17.7 * cm, 2 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_municipality_logs'],
              8 * cm, PAGE_HEIGHT - 17.7 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_municipality_logs'],
              15 * cm, PAGE_HEIGHT - 17.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Αρ. Δημοτολογίου:',
              2.1 * cm, PAGE_HEIGHT - 18.2 * cm, 3 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_municipality_logs'],
              8 * cm, PAGE_HEIGHT - 18.2 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_municipality_logs'],
              15 * cm, PAGE_HEIGHT - 18.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'ΑΦΜ:',
              2.1 * cm, PAGE_HEIGHT - 18.7 * cm, 1 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_afm'],
              8 * cm, PAGE_HEIGHT - 18.7 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_afm'],
              15 * cm, PAGE_HEIGHT - 18.7 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'ΑΜΚΑ:',
              2.1 * cm, PAGE_HEIGHT - 19.2 * cm, 1 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['father_amka'],
              8 * cm, PAGE_HEIGHT - 19.2 * cm, 7 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_amka'],
              15 * cm, PAGE_HEIGHT - 19.2 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Φορείς Ασφάλισης:',
              2.1 * cm, PAGE_HEIGHT - 19.7 * cm, 3 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, '1)',
              5 * cm, PAGE_HEIGHT - 19.7 * cm, 1 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if '1' in payload['father_insurance']:
        draw_para(canvas, payload['father_insurance']['1'],
                  8 * cm, PAGE_HEIGHT - 19.7 * cm, 7 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)
    if '1' in payload['mother_insurance']:
        draw_para(canvas, payload['mother_insurance']['1'],
                  15 * cm, PAGE_HEIGHT - 19.7 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, '2)',
              5 * cm, PAGE_HEIGHT - 20.15 * cm, 1 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if '2' in payload['father_insurance']:
        draw_para(canvas, payload['father_insurance']['2'],
                  8 * cm, PAGE_HEIGHT - 20.15 * cm, 7 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)
    if '2' in payload['mother_insurance']:
        draw_para(canvas, payload['mother_insurance']['2'],
                  15 * cm, PAGE_HEIGHT - 20.15 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, '3)',
              5 * cm, PAGE_HEIGHT - 20.55 * cm, 1 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    if '3' in payload['father_insurance']:
        draw_para(canvas, payload['father_insurance']['3'],
                  8 * cm, PAGE_HEIGHT - 20.55 * cm, 7 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)
    if '3' in payload['mother_insurance']:
        draw_para(canvas, payload['mother_insurance']['3'],
                  15 * cm, PAGE_HEIGHT - 20.55 * cm, 5 * cm, 1 * cm,
                  font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Επών. Πατρός (μόνο μητέρα):',
              2.1 * cm, PAGE_HEIGHT - 21.05 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, payload['mother_father_surname'],
              15 * cm, PAGE_HEIGHT - 21.05 * cm, 5 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'ΠΑΡΑΤΗΡΗΣΕΙΣ',
              2.1 * cm, PAGE_HEIGHT - 21.55 * cm, 3 * cm, 1 * cm,
              font_name='Font-Regular', font_size=10)

    canvas.line(2.1 * cm, PAGE_HEIGHT - 21.6 * cm,
                PAGE_WIDTH - 16.2 * cm, PAGE_HEIGHT - 21.6 * cm)

    draw_para(canvas, payload['notes'],
              2.1 * cm, PAGE_HEIGHT - 22.3 * cm, 10 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

    draw_para(canvas, 'Ο/Η Ληξίαρχος',
              15 * cm, PAGE_HEIGHT - 22.5 * cm, 3 * cm, 1 * cm,
              font_name='Font-Regular', font_size=9)

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


def make_subtitle(element, contents):
    for pcontent in contents:
        elements.append(Paragraph(pcontent, STYLES["Info"]))


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

    payload = load_payload('birth_data.json')

    make_subtitle(elements, INFO)
    make_heading(elements, [TITLE])

    def make_first_page_ld(canvas, doc): return make_first_page(canvas, doc,
                                                                args.qr_code,
                                                                payload)

    decl = doc.build(elements,
                     onFirstPage=make_first_page_ld,
                     onLaterPages=make_later_pages)

    if args.certificate and args.password:
        crypto_sign(args.certificate, args.password, args.output)
    print(payload['digest'])

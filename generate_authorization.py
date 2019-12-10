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
    'm': 'Ο',
    'f': 'Η',
    'n': 'Το',
    'mf': 'Ο - Η'
}

GENDER_BYLINE = {
    'm': 'Ο Εξουσιοδοτών',
    'f': 'Η Εξουσιοδοτούσα',
    'n': 'Το Εξουσιοδοτούν',
    'mf': 'Ο - Η Εξoυσιοδοτ.'
}


TITLE = 'ΕΞΟΥΣΙΟΔΟΤΗΣΗ'
IAUTHORIZE = 'Ε ξ ο υ σ ι ο δ ο τ ώ'

PAGE_DESCR = "Εξουσιοδότηση"

DEFAULT_OUTPUT_FILE = 'authorization.pdf'

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

    styles.add(ParagraphStyle(name='DeclHeading',
                              fontName='Font-Bold',
                              fontSize=16,
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

    draw_para(canvas, 'Ο/Η κάτωθι υπογεγραμμένος/η',
              2.1 * cm, PAGE_HEIGHT - 4.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)

    # undersigned line
    canvas.line(6.5 * cm, PAGE_HEIGHT - 4.8 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 4.8 * cm)
    draw_para(canvas, payload['undersigned'],
              7.5 * cm, PAGE_HEIGHT - 4.8 * cm,
              13 * cm, 1 * cm)

    draw_para(canvas, 'του',
              2.1 * cm, PAGE_HEIGHT - 5.85 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)

    # father_name line
    canvas.line(2.6 * cm, PAGE_HEIGHT - 5.8 * cm,
                PAGE_WIDTH - 11 * cm, PAGE_HEIGHT - 5.8 * cm)
    draw_para(canvas, payload['father_name'],
              4.5 * cm, PAGE_HEIGHT - 5.80 * cm,
              5 * cm, 1 * cm)

    draw_para(canvas, 'και της',
              10 * cm, PAGE_HEIGHT - 5.85 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)

    # mother_name line
    canvas.line(11 * cm, PAGE_HEIGHT - 5.8 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 5.8 * cm)
    draw_para(canvas, payload['mother_name'],
              13 * cm, PAGE_HEIGHT - 5.8 * cm,
              5 * cm, 1 * cm)

    draw_para(canvas, 'γεννηθείς την',
              2.1 * cm, PAGE_HEIGHT - 6.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # date of birth line
    canvas.line(4 * cm, PAGE_HEIGHT - 6.8 * cm,
                PAGE_WIDTH - 12 * cm, PAGE_HEIGHT - 6.8 * cm)
    draw_para(canvas, payload['date_of_birth'],
              5 * cm, PAGE_HEIGHT - 6.8 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, ', στην',
              9 * cm, PAGE_HEIGHT - 6.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # birth place line
    canvas.line(10 * cm, PAGE_HEIGHT - 6.8 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 6.8 * cm)
    draw_para(canvas, payload['birth_place'],
              12 * cm, PAGE_HEIGHT - 6.8 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, 'κάτοικος',
              2.1 * cm, PAGE_HEIGHT - 7.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # place of residence line
    canvas.line(3.3 * cm, PAGE_HEIGHT - 7.8 * cm,
                PAGE_WIDTH - 12 * cm, PAGE_HEIGHT - 7.8 * cm)
    draw_para(canvas, payload['place_of_residence'],
              5 * cm, PAGE_HEIGHT - 7.8 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, ', οδός',
              9 * cm, PAGE_HEIGHT - 7.8 * cm,
              11 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # street line
    canvas.line(10 * cm, PAGE_HEIGHT - 7.8 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 7.8 * cm)
    draw_para(canvas, payload['street'],
              12 * cm, PAGE_HEIGHT - 7.8 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, 'αρ',
              2.1 * cm, PAGE_HEIGHT - 8.8 * cm,
              11 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # street number line
    canvas.line(2.5 * cm, PAGE_HEIGHT - 8.8 * cm,
                PAGE_WIDTH - 15 * cm, PAGE_HEIGHT - 8.8 * cm)
    draw_para(canvas, payload['street_number'],
              3 * cm, PAGE_HEIGHT - 8.8 * cm,
              3.5 * cm, 1 * cm)

    draw_para(canvas, ', με ΑΔΤ/Διαβατηρίου',
              6 * cm, PAGE_HEIGHT - 8.8 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # id number line
    canvas.line(9 * cm, PAGE_HEIGHT - 8.8 * cm,
                PAGE_WIDTH - 4.5 * cm, PAGE_HEIGHT - 8.8 * cm)
    draw_para(canvas, payload['id_number'],
              10 * cm, PAGE_HEIGHT - 8.80 * cm,
              5.5 * cm, 1 * cm)

    draw_para(canvas, 'που εκδόθηκε την',
              16.5 * cm, PAGE_HEIGHT - 8.8 * cm,
              4 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # id number line
    canvas.line(2.1 * cm, PAGE_HEIGHT - 9.8 * cm,
                PAGE_WIDTH - 14 * cm, PAGE_HEIGHT - 9.8 * cm)
    draw_para(canvas, payload['id_issue_date'],
              3 * cm, PAGE_HEIGHT - 9.8 * cm,
              2.5 * cm, 1 * cm)
    draw_para(canvas, 'από το',
              7 * cm, PAGE_HEIGHT - 9.8 * cm,
              3 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # place of issuance line
    canvas.line(8 * cm, PAGE_HEIGHT - 9.8 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 9.8 * cm)
    draw_para(canvas, payload['place_of_issuance'],
              10.7 * cm, PAGE_HEIGHT - 9.8 * cm,
              5 * cm, 1 * cm)

# AUTHORIZED

    draw_para(canvas, 'Τον/Την',
              2.1 * cm, PAGE_HEIGHT - 13 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)

    # undersigned line
    canvas.line(3.2 * cm, PAGE_HEIGHT - 13 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 13 * cm)
    draw_para(canvas, payload['authorized'],
              5 * cm, PAGE_HEIGHT - 13 * cm,
              13 * cm, 1 * cm)

    draw_para(canvas, 'του',
              2.1 * cm, PAGE_HEIGHT - 14.05 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)

    # father_name line
    canvas.line(2.6 * cm, PAGE_HEIGHT - 14.05 * cm,
                PAGE_WIDTH - 11 * cm, PAGE_HEIGHT - 14.05 * cm)
    draw_para(canvas, payload['authorized_father_name'],
              4.5 * cm, PAGE_HEIGHT - 14.05 * cm,
              5 * cm, 1 * cm)

    draw_para(canvas, 'και της',
              10 * cm, PAGE_HEIGHT - 14.05 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)

    # mother_name line
    canvas.line(11 * cm, PAGE_HEIGHT - 14.05 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 14.05 * cm)
    draw_para(canvas, payload['authorized_mother_name'],
              13 * cm, PAGE_HEIGHT - 14.05 * cm,
              5 * cm, 1 * cm)

    draw_para(canvas, 'γεννηθείς την',
              2.1 * cm, PAGE_HEIGHT - 15 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # date of birth line
    canvas.line(4 * cm, PAGE_HEIGHT - 15 * cm,
                PAGE_WIDTH - 12 * cm, PAGE_HEIGHT - 15 * cm)
    draw_para(canvas, payload['authorized_date_of_birth'],
              5 * cm, PAGE_HEIGHT - 15 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, ', στην',
              9 * cm, PAGE_HEIGHT - 15 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # birth place line
    canvas.line(10 * cm, PAGE_HEIGHT - 15 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 15 * cm)
    draw_para(canvas, payload['authorized_birth_place'],
              12 * cm, PAGE_HEIGHT - 15 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, 'κάτοικος',
              2.1 * cm, PAGE_HEIGHT - 16 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # place of residence line
    canvas.line(3.3 * cm, PAGE_HEIGHT - 16 * cm,
                PAGE_WIDTH - 12 * cm, PAGE_HEIGHT - 16 * cm)
    draw_para(canvas, payload['authorized_place_of_residence'],
              5 * cm, PAGE_HEIGHT - 16 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, ', οδός',
              9 * cm, PAGE_HEIGHT - 16 * cm,
              11 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # street line
    canvas.line(10 * cm, PAGE_HEIGHT - 16 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 16 * cm)
    draw_para(canvas, payload['authorized_street'],
              12 * cm, PAGE_HEIGHT - 16 * cm,
              11 * cm, 1 * cm)

    draw_para(canvas, 'αρ',
              2.1 * cm, PAGE_HEIGHT - 17 * cm,
              11 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # street number line
    canvas.line(2.5 * cm, PAGE_HEIGHT - 17 * cm,
                PAGE_WIDTH - 15 * cm, PAGE_HEIGHT - 17 * cm)
    draw_para(canvas, payload['authorized_street_number'],
              3 * cm, PAGE_HEIGHT - 17 * cm,
              3.5 * cm, 1 * cm)

    draw_para(canvas, ', με ΑΔΤ/Διαβατηρίου',
              6 * cm, PAGE_HEIGHT - 17 * cm,
              5 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # id number line
    canvas.line(9 * cm, PAGE_HEIGHT - 17 * cm,
                PAGE_WIDTH - 4.5 * cm, PAGE_HEIGHT - 17 * cm)
    draw_para(canvas, payload['authorized_id_number'],
              10 * cm, PAGE_HEIGHT - 17 * cm,
              5.5 * cm, 1 * cm)

    draw_para(canvas, 'που εκδόθηκε την',
              16.5 * cm, PAGE_HEIGHT - 17 * cm,
              4 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # issue date line
    canvas.line(2.1 * cm, PAGE_HEIGHT - 18 * cm,
                PAGE_WIDTH - 14 * cm, PAGE_HEIGHT - 18 * cm)
    draw_para(canvas, payload['authorized_id_issue_date'],
              3 * cm, PAGE_HEIGHT - 18 * cm,
              2.5 * cm, 1 * cm)
    draw_para(canvas, 'από το',
              7 * cm, PAGE_HEIGHT - 18 * cm,
              3 * cm, 1 * cm,
              font_name='Font-Regular',
              font_size=9)
    # place of issuance line
    canvas.line(8 * cm, PAGE_HEIGHT - 18 * cm,
                PAGE_WIDTH - 2 * cm, PAGE_HEIGHT - 18 * cm)
    draw_para(canvas, payload['authorized_place_of_issuance'],
              10.7 * cm, PAGE_HEIGHT - 18 * cm,
              5 * cm, 1 * cm)

    # Declaration text
    draw_para(canvas, payload['authorization_text'],
              2.2 * cm, PAGE_HEIGHT - 22 * cm,
              16 * cm, 10 * cm)

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


def make_human_signature(elements, payload):
    signature = [
        [
            Spacer(0 * cm, 12 * cm),
            Paragraph(payload['date'], STYLES['NameSignature'])
        ],
        [
            Spacer(0 * cm, 0 * cm),
            Paragraph(GENDER_BYLINE[payload['gender']],
                      STYLES['NameSignature'])
        ],
        [
            Spacer(0 * cm, 1 * cm),
            Paragraph(f'{payload["undersigned"]}',
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

    payload = load_payload('auth_data.json')
    if 'gender' not in payload:
        payload['gender'] = 'mf'

    make_heading(elements, [TITLE])
    elements.append(Spacer(0 * cm, 8 * cm))
    make_heading(elements, [IAUTHORIZE])

    def make_first_page_ld(canvas, doc): return make_first_page(canvas, doc,
                                                                args.qr_code,
                                                                payload)
    make_human_signature(elements, payload)

    decl = doc.build(elements,
                     onFirstPage=make_first_page_ld,
                     onLaterPages=make_later_pages)

    if args.certificate and args.password:
        crypto_sign(args.certificate, args.password, args.output)
    print(payload['digest'])

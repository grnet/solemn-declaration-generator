import json
import os.path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
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


TITLE = 'Αίτηση'

PAGE_DESCR = "Αίτηση"

GENDER_BYLINE = {
    'm': 'Ο Αιτών',
    'f': 'Η Αιτούσα',
    'n': 'Το Αιτούν',
    'mf': 'Ο - Η Αιτ.'
}

DEFAULT_OUTPUT_FILE = 'application.pdf'

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

    styles.add(ParagraphStyle(name='NameSignature',
                              fontName='Font-Regular',
                              fontSize=10,
                              alignment=TA_CENTER)),

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

    # Frame Rectangle
    canvas.roundRect(1 * cm, PAGE_HEIGHT - 13.5 * cm,
                     19 * cm, 8.5 * cm, 3, stroke=1, fill=0)

    draw_para(canvas, 'Όνομα: ',
              1.5 * cm, PAGE_HEIGHT - 6 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['firstname'],
              3 * cm, PAGE_HEIGHT - 6 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'Επώνυμο: ',
              1.5 * cm, PAGE_HEIGHT - 7 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['surname'],
              3.5 * cm, PAGE_HEIGHT - 7 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'ΑΦΜ: ',
              1.5 * cm, PAGE_HEIGHT - 8 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['afm'],
              3 * cm, PAGE_HEIGHT - 8 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'ΑΜΚΑ: ',
              1.5 * cm, PAGE_HEIGHT - 9 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['amka'],
              3 * cm, PAGE_HEIGHT - 9 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'Αριθμός Δελτίου Ταυτότητας: ',
              1.5 * cm, PAGE_HEIGHT - 10 * cm,
              5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['adt'],
              6 * cm, PAGE_HEIGHT - 10 * cm,
              11.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'Email: ',
              1.5 * cm, PAGE_HEIGHT - 11 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['email'],
              3 * cm, PAGE_HEIGHT - 11 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'Τηλέφωνο: ',
              1.5 * cm, PAGE_HEIGHT - 12 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['tel'],
              3.5 * cm, PAGE_HEIGHT - 12 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, 'IBAN: ',
              1.5 * cm, PAGE_HEIGHT - 13 * cm,
              2 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

    draw_para(canvas, payload['iban'],
              3 * cm, PAGE_HEIGHT - 13 * cm,
              14.5 * cm, 0.5 * cm,
              font_name='Font-Regular',
              font_size=9)

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


def make_human_signature(elements, payload):
    signature = [
        [
            Spacer(0 * cm, 3 * cm),
            Paragraph(payload['date'], STYLES['NameSignature'])
        ],
        [
            Spacer(0 * cm, 0 * cm),
            Paragraph(GENDER_BYLINE[payload['gender']],
                      STYLES['NameSignature'])
        ],
        [
            Spacer(0 * cm, 1 * cm),
            Paragraph(f'{payload["firstname"]} \
                      {payload["surname"]}',
                      STYLES['NameSignature'])
        ]
    ]

    signature = Table(signature)

    elements.append(signature)


def make_application_text(elements, payload):
    # this were the text starts
    spacer = Spacer(0, 10 * cm)
    paragraph = Paragraph(payload['application_text'], STYLES['Notes'])
    elements.append(spacer)
    elements.append(paragraph)


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

    payload = load_payload('application.json')
    elements.append(Spacer(0, 1 * cm))
    make_heading(elements, [payload['title']])
    make_application_text(elements, payload)
    make_human_signature(elements, payload)

    doc.leftMargin = 29
    doc.rightMargin = 29

    def make_first_page_ld(canvas, doc): return make_first_page(canvas, doc,
                                                                args.qr_code,
                                                                payload)

    decl = doc.build(elements,
                     onFirstPage=make_first_page_ld,
                     onLaterPages=make_later_pages)

    if args.certificate and args.password:
        crypto_sign(args.certificate, args.password, args.output)
    print(payload['digest'])

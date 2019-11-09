# Solemn Declarations Generator

## What Is It?

One of the most touching (groping, rather) characteristics of the Greek state 
is that in many transactions the citizen has to vouchsafe (solemny declare)
that something is the case. That is a written declaration that you don't lie
about something; and if it transpires that you do lie, you will be sanctioned.

Of course one could argue that this whole ritual should be redundant and 
citizens should just tick boxes in forms and sign them, with the assumption
that people are honest and what they say is true, but the solemn declaration
is an established ritual of Greek public life.

These solemn declarations must follow a prescribed format. Unfortunately, 
there is no satisfactory digital version of them. Most people take a printed 
form and fill it out manually. That results in mountains of cacography amassed
in Greek public services.

Hoping that such documents will one day disappear from the face of the earth,
this program generates automatically digital Greek Government solemn 
declarations:

* It reads the form data from a JSON file and produces a filled 
  PDF form. 

* It can sign the form it generates if provided a valid P12 certificate.

* It can generate a unique code and embed it in the PDF; this code could
  be used to cross-reference and verify a signature by some service.

## Usage

```
generate_declaration.py [-h] [-o OUTPUT] [-c CERTIFICATE] [-p PASSWORD]
                               [-q]

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        PDF output file (default: solemn_declaration.pdf)
  -c CERTIFICATE, --certificate CERTIFICATE
                        certificate file (default: None)
  -p PASSWORD, --password PASSWORD
                        certificate password (default: None)
  -q, --qr_code         embed reference and QR code (default: False)
  ```

If `-c` and `-p` are given, the basename of the signed document is 
`<output>-signed`, where `<output>` is the name of the generated form
given by the user. 

When it finishes the program outputs a reference code (the same one that
is embedded in the document if run with `-q`).

## Examples.

* [solemn_declaration.pdf](solemn_declaration.pdf): an example PDF solemn
  declaration.

* [solemn_declaration-signed.pdf](solemn_declaration-signed.pdf): an example
  PDF solemn declaration signed, with an embedded QR reference code.

## Configure

The contents of the form are read from `data.json`. See the provided
example.

## Requirements


* [ReportLab](https://www.reportlab.com/opensource/)

* [Cryptography](https://cryptography.io/en/latest/)

* [qrcode](https://github.com/lincolnloop/python-qrcode)

* [endesive](https://github.com/m32/endesive/)

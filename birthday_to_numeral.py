one_to_twenty_n = [
    'ένα',
    'δύο',
    'τρία',
    'τέσσερα',
    'πέντε',
    'έξι',
    'επτά',
    'οκτώ',
    'εννέα',
    'δέκα',
    'έντεκα',
    'δώδεκα',
    'δεκατρία',
    'δεκατέσσερα',
    'δεκαπέντε',
    'δεκαέξι',
    'δεκαεπτά',
    'δεκαοκτώ',
    'δεκαεννέα'
    ]

one_to_twenty_f = [
    'μία',
    'δύο',
    'τρεις',
    'τέσσερεις',
    'πέντε',
    'έξι',
    'επτά',
    'οκτώ',
    'εννέα',
    'δέκα',
    'έντεκα',
    'δώδεκα',
    'δεκατρείς',
    'δεκατέσσερεις',
    'δεκαπέντε',
    'δεκαέξι',
    'δεκαεπτά',
    'δεκαοκτώ',
    'δεκαεννέα'
    ]

one_to_twenty_en = [
    'one',
    'two',
    'three',
    'four',
    'five',
    'six',
    'seven',
    'eight',
    'nine',
    'ten',
    'eleven',
    'twelve',
    'thirteen',
    'fourteen',
    'fifteen',
    'sixteen',
    'seventeen',
    'eighteen',
    'nineteen'
    ]

tens = [
    'δέκα',
    'είκοσι',
    'τριάντα',
    'σαράντα',
    'πενήντα',
    'εξήντα',
    'εβδομήντα',
    'ογδόντα',
    'ενενήντα'
    ]

tens_en = [
    'ten',
    'twenty',
    'thirty',
    'forty',
    'fifty',
    'sixty',
    'seventy',
    'eighty',
    'ninety'
    ]

hundreds_n = [
    'εκατό',
    'διακόσια',
    'τριακόσια',
    'τετρακόσια',
    'πεντακόσια',
    'εξακόσια',
    'επτακόσια',
    'οκτακόσια',
    'εννιακόσια'
    ]

hundreds_f = [
    'εκατό',
    'διακόσιες',
    'τριακόσιες',
    'τετρακόσιες',
    'πεντακόσιες',
    'εξακόσιες',
    'επτακόσιες',
    'οκτακόσιες',
    'εννιακόσιες'
    ]

hundreds_en = [ x + ' hundred' for x in one_to_twenty_en[0:10]]

thousands = [
    'χίλια',
    'χιλιάδες'
    ]

thousands_en = [
    'one thousand',
    'thousand'
]

millions = [
    'εκατομμύριο',
    'εκατομμύρια'
    ]

millions_en = [
    'one million',
    'million'
]

billions = [
    'δισεκατομμύριο',
    'δισεκατομμύρια'
    ]

billions_en = [
    'one billion',
    'billion'
]

def num_to_text_hundreds(number, f, english=False):
    parts = []
    h, mod100 = divmod(number, 100)
    t, mod10 = divmod(mod100, 10)
    if english:
        one_to_twenty_arr_f = one_to_twenty_en
        one_to_twenty_arr_n = one_to_twenty_en
        hundreds_arr_f = hundreds_en
        hundreds_arr_n = hundreds_en
        tens_arr = tens_en
    else:
        one_to_twenty_arr_f = one_to_twenty_f
        one_to_twenty_arr_n = one_to_twenty_n
        hundreds_arr_f = hundreds_f
        hundreds_arr_n = hundreds_n
        tens_arr = tens
    if h > 0:
        if h == 1 and mod100 > 0 and english:
            parts.append(hundreds_arr_n[h - 1] + 'ν')
        else:
            if f == True:
                parts.append(hundreds_arr_f[h - 1])
            else:
                parts.append(hundreds_arr_n[h - 1])
    if t > 1:
        parts.append(tens_arr[t - 1])
        if mod10 > 0:
            if english:
                parts[-1] = parts[-1] + '-' + one_to_twenty_arr_f[mod10 - 1]
            elif f == True:
                parts.append(one_to_twenty_arr_f[mod10 - 1])
            else:
                parts.append(one_to_twenty_arr_n[mod10 - 1])
    elif t == 1:
        parts.append(one_to_twenty_arr_n[10 + mod10 - 1])
    elif mod10 > 0:
        if f == True:
            parts.append(one_to_twenty_arr_f[mod10 - 1])
        else:
            parts.append(one_to_twenty_arr_n[mod10 - 1])
    return ' '.join(parts)

def num_to_text_thousands(number, english=False):
    th, r = divmod(number, 1000)
    if english:
        thousands_arr = thousands_en
    else:
        thousands_arr = thousands        
    if th > 1:
        return "{0} {1} {2}".format(num_to_text_hundreds(th, True, english),
                                    thousands_arr[1],
                                    num_to_text_hundreds(r, False, english))
    elif th == 1:
        return "{0} {1}".format(thousands_arr[0],
                                num_to_text_hundreds(r, False, english))
    else:
        return num_to_text_hundreds(r, False, english)

def num_to_text_millions(number, english=False):
    m, r = divmod(number, 1000000)
    if english:
        millions_arr = millions_en
    else:
        millions_arr = millions    
    if m > 1:
        return "{0} {1} {2}".format(num_to_text_hundreds(m, False),
                                    millions_arr[1],
                                    num_to_text_thousands(r, english))
    elif m == 1:
        return "{0} {1} {2}".format(one_to_twenty_n[0],
                                    millions_arr[0],
                                    num_to_text_thousands(r, english))
    else:
        return num_to_text_thousands(number, english)

def num_to_text_billions(number, english=False):
    m, r = divmod(number, 1000000000)
    if english:
        billions_arr = billions_en
    else:
        billions_arr = billions
    if m > 1:
        return "{0} {1} {2}".format(num_to_text_hundreds(m, False),
                                    billions_arr[1],
                                    num_to_text_millions(r, english))
    elif m == 1:
        return "{0} {1} {2}".format(one_to_twenty_n[0],
                                    billions_arr[0],
                                    num_to_text_millions(r, english))
    else:
        return num_to_text_millions(number, english)
    
def num_to_text(number, english=False):
    return num_to_text_billions(number, english)


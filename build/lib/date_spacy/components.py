import re
from spacy.tokens import Span
from spacy.language import Language
from spacy.util import filter_spans
import dateparser

ordinal_to_number = {
        "primeiro": "1", "segundo": "2", "terceiro": "3", "quarto": "4", "quinto": "5",
        "sexto": "6", "sétimo": "7", "oitavo": "8", "nono": "9", "décimo": "10",
        "décimo primeiro": "11", "décimo segundo": "12", "décimo terceiro": "13", "décimo quarto": "14",
        "décimo quinto": "15", "décimo sexto": "16", "décimo sétimo": "17", "décimo oitavo": "18",
        "décimo nono": "19", "vigésimo": "20", "vigésimo primeiro": "21", "vigésimo segundo": "22",
        "vigésimo terceiro": "23", "vigésimo quarto": "24", "vigésimo quinto": "25", "vigésimo sexto": "26",
        "vigésimo sétimo": "27", "vigésimo oitavo": "28", "vigésimo nono": "29", "trigésimo": "30",
        "trigésimo primeiro": "31"

}


@Language.component("find_dates")
def find_dates(doc):
    # Set up a date extension on the span
    Span.set_extension("date", default=None, force=True)

    # Ordinals
    ordinals = list(ordinal_to_number.keys())
    # ordinals = [
    #     "first", "second", "third", "fourth", "fifth",
    #     "sixth", "seventh", "eighth", "ninth", "tenth",
    #     "eleventh", "twelfth", "thirteenth", "fourteenth",
    #     "fifteenth", "sixteenth", "seventeenth", "eighteenth",
    #     "nineteenth", "twentieth", "twenty-first", "twenty-second",
    #     "twenty-third", "twenty-fourth", "twenty-fifth", "twenty-sixth",
    #     "twenty-seventh", "twenty-eighth", "twenty-ninth", "thirtieth", "thirty-first"
    # ]
    
    ordinal_pattern = r"\b(?:" + "|".join(ordinals) + r")\b"

    # A regex pattern to capture a variety of date formats
    date_pattern = r"""
        # Day-Month-Year
        (?:
            \d{1,2}(?:st|nd|rd|th)?     # Day with optional st, nd, rd, th suffix
            \s+
            (?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]* # Month name
            
            (?:                         # Year is optional
                \s+
                \d{4}                   # Year
            )?
        )
        |
        # Day/Month/Year
        (?:
            \d{1,2}                     # Day
            [/-]
            \d{1,2}                     # Month
            (?:                         # Year is optional
                [/-]
                \d{2,4}                 # Year
            )?
        )
        |
        # Year-Month-Day
        (?:
            \d{4}                       # Year
            [-/]
            \d{1,2}                     # Month
            [-/]
            \d{1,2}                     # Day
        )
        |
        # Month-Day-Year
        (?:
            (?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]* # Month name
            \s+
            \d{1,2}(?:st|nd|rd|th)?     # Day with optional st, nd, rd, th suffix
            (?:                         # Year is optional
                ,?
                \s+
                \d{4}                   # Year
            )?
        )
        |
        # Month-Year
        (?:
            (?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]* # Month name
            \s+
            \d{4}                       # Year
        )
        |
        # Ordinal-Day-Month-Year
        (?:
            """ + ordinal_pattern + """
            \s+
            (?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]* # Month name
            (?:                         # Year is optional
                \s+
                \d{4}                   # Year
            )?
        )
        |
        (?:
            """ + ordinal_pattern + """
            \s+
            of
            \s+
            (?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*  # Month name
            (?:                         # Year is optional
                \s+
                \d{4}                   # Year
            )?
        )
        |
        # Month Ordinal
        (?:
            (?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*  # Month name
            \s+
            """ + ordinal_pattern + """
            (?:                         # Year is optional
                \s+
                \d{4}                   # Year
            )?
        )
    """
    matches = list(re.finditer(date_pattern, doc.text, re.VERBOSE))
    new_ents = []
    for match in matches:
        start_char, end_char = match.span()
        # Convert character offsets to token offsets
        start_token = None
        end_token = None
        for token in doc:
            if token.idx == start_char:
                start_token = token.i
            if token.idx + len(token.text) == end_char:
                end_token = token.i
        if start_token is not None and end_token is not None:
            hit_text = doc.text[start_char:end_char]
            parsed_date = dateparser.parse(hit_text)
            if parsed_date:  # Ensure the matched string is a valid date
                ent = Span(doc, start_token, end_token + 1, label="DATE")
                ent._.date = parsed_date
                new_ents.append(ent)
            else:
                # Replace each ordinal in hit_text with its numeric representation
                for ordinal, number in ordinal_to_number.items():
                    hit_text = hit_text.replace(ordinal, number)

                # Remove the word "of" from hit_text
                new_date = hit_text.replace(" of ", " ")

                parsed_date = dateparser.parse(new_date)
                ent = Span(doc, start_token, end_token + 1, label="DATE")
                ent._.date = parsed_date
                new_ents.append(ent)
    # Combine the new entities with existing entities, ensuring no overlap
    doc.ents = list(doc.ents) + new_ents
    
    return doc

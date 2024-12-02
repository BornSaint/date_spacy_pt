import re
from spacy.tokens import Span
from spacy.language import Language
from spacy.util import filter_spans

import dateparser
from collections import OrderedDict

ordinal_to_number = {
        "primeiro": "1", "segundo": "2", "terceiro": "3", "quarto": "4", "quinto": "5",
        "sexto": "6", "sétimo": "7", "oitavo": "8", "nono": "9", "décimo": "10",
        "décimo[-\s]primeiro": "11", "décimo[-\s]segundo": "12", "décimo[-\s]terceiro": "13", "décimo[-\s]quarto": "14",
        "décimo[-\s]quinto": "15", "décimo[-\s]sexto": "16", "décimo[-\s]sétimo": "17", "décimo[-\s]oitavo": "18",
        "décimo[-\s]nono": "19", "vigésimo": "20", "vigésimo[-\s]primeiro": "21", "vigésimo[-\s]segundo": "22",
        "vigésimo[-\s]terceiro": "23", "vigésimo[-\s]quarto": "24", "vigésimo[-\s]quinto": "25", "vigésimo[-\s]sexto": "26",
        "vigésimo[-\s]sétimo": "27", "vigésimo[-\s]oitavo": "28", "vigésimo[-\s]nono": "29", "trigésimo": "30",
        "trigésimo[-\s]primeiro": "31"

}

reversed_ordinal_to_number = OrderedDict(reversed(list(ordinal_to_number.items())))
# ordinal_to_number = {
#         "primeiro": "1", "segundo": "2", "terceiro": "3", "quarto": "4", "quinto": "5",
#         "sexto": "6", "sétimo": "7", "oitavo": "8", "nono": "9", "décimo": "10",
#         "décimo primeiro": "11", "décimo segundo": "12", "décimo terceiro": "13", "décimo quarto": "14",
#         "décimo quinto": "15", "décimo sexto": "16", "décimo sétimo": "17", "décimo oitavo": "18",
#         "décimo nono": "19", "vigésimo": "20", "vigésimo primeiro": "21", "vigésimo segundo": "22",
#         "vigésimo terceiro": "23", "vigésimo quarto": "24", "vigésimo quinto": "25", "vigésimo sexto": "26",
#         "vigésimo sétimo": "27", "vigésimo oitavo": "28", "vigésimo nono": "29", "trigésimo": "30",
#         "trigésimo primeiro": "31"

# }
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
    
    ordinal_pattern = r"\b(?:" + "(\s*dia\s*)?|".join(ordinals) + r")\b"

    # A regex pattern to capture a variety of date formats
    date_pattern = r"""
        # Day-Month-Year
        (?:
            \d{1,2}(?:º)?     # Day with optional st, nd, rd, th suffix
            (\s+de\s+)?
            (?:[Jj]an|[Ff]ev|[Mm]ar|[Aa]br|[Mm]ai|[Jj]un|[Jj]ul|[Aa]go|[Ss]et|[Oo]ut|[Nn]ov|[Dd]ez)[a-z]* # Month name
            (\s+de\s+)?
            (?:                         # Year is optional
                \s*
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
            (?:[Jj]an|[Ff]ev|[Mm]ar|[Aa]br|[Mm]ai|[Jj]un|[Jj]ul|[Aa]go|[Ss]et|[Oo]ut|[Nn]ov|[Dd]ez)[a-z]* # Month name
            \d{1,2}(?:º)?     # Day with optional st, nd, rd, th suffix
            
            (?:                         # Year is optional
                ,?
                \s+
                \d{4}                   # Year
            )?
        )
        |
        # Month-Year
        (?:
            (?:[Jj]an|[Ff]ev|[Mm]ar|[Aa]br|[Mm]ai|[Jj]un|[Jj]ul|[Aa]go|[Ss]et|[Oo]ut|[Nn]ov|[Dd]ez)[a-z]* # Month name
            (\s+de\s+)?
            \d{4}                       # Year
        )
        |
        # Ordinal-Day-Month-Year
        (?:
            """ + ordinal_pattern + """
            (\s+de\s+)?
            (?:[Jj]an|[Ff]ev|[Mm]ar|[Aa]br|[Mm]ai|[Jj]un|[Jj]ul|[Aa]go|[Ss]et|[Oo]ut|[Nn]ov|[Dd]ez)[a-z]* # Month name
            (\s+de\s+)?
            (?:                         # Year is optional
                \d{4}                   # Year
            )?
        )
        |
        (?:
            """ + ordinal_pattern + """
            (\s+de\s+)?
            (?:[Jj]an|[Ff]ev|[Mm]ar|[Aa]br|[Mm]ai|[Jj]un|[Jj]ul|[Aa]go|[Ss]et|[Oo]ut|[Nn]ov|[Dd]ez)[a-z]*  # Month name
            (\s+de\s+)?
            (?:                         # Year is optional
                \d{4}                   # Year
            )?
        )

    """
    matches = list(re.finditer(date_pattern, doc.text, re.VERBOSE))
    new_ents = []
    for match in matches:
        # print(match)
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
            # print(hit_text)
            for k, v in reversed_ordinal_to_number.items():
                hit_text = re.sub(k, v, hit_text)
            hit_text = re.sub('\s*dia\s*', '', hit_text)
            # print(hit_text)
            
            parsed_date = dateparser.parse(hit_text, languages=['en', 'pt'])
            # print(parsed_date)
            if parsed_date:  # Ensure the matched string is a valid date
                ent = Span(doc, start_token, end_token + 1, label="DATE")
                ent._.date = parsed_date
                new_ents.append(ent)
                # print(ent)
            else:
                # Replace each ordinal in hit_text with its numeric representation
                for ordinal, number in ordinal_to_number.items():
                    hit_text = hit_text.replace(ordinal, number)

                # Remove the word "of" from hit_text
                new_date = hit_text.replace(" de ", " ")

                parsed_date = dateparser.parse(new_date)
                ent = Span(doc, start_token, end_token + 1, label="DATE")
                ent._.date = parsed_date
                new_ents.append(ent)
    # Combine the new entities with existing entities, ensuring no overlap
    doc.ents = list(doc.ents) + new_ents
    
    return doc

if __name__ == '__main__':
    import spacy
    from date_spacy import find_dates
    nlp = spacy.blank('pt')
    nlp.add_pipe('find_dates')

    doc = nlp('''o evento está agendado pro dia 25 de Agosto de 2023.
            Nós também temos uma reunião para 10 de setembro e uma outra no décimo segundo dia de outubro de 2024
            décimo-segundo dia de outubro de 2024
            e finaliza no dia 4 de Jan''')
    # doc = nlp('''no vigésimo-segundo dia de outubro de 2024''')
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            print(f'Text: {ent.text} -> Parsed Date: {ent._.date}')

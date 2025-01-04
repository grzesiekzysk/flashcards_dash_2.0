import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import eng_to_ipa

def fix_string(text):
    pattern = r"(\S)\("
    return re.sub(pattern, r"\1 (", text)

class Diki:
    def __init__(self, lang='ENG'):
        self.lang = lang
        self.dict_pop = {
            '*****': 'TOP 1000',
            '****': 'TOP 2000',
            '***': 'TOP 3000',
            '**': 'TOP 4000',
            '*': 'TOP 5000',
        }
        self.data = pd.DataFrame(
            columns=[
                'english_word',
                'pronunciation',
                'part_of_speech',
                'polish_word',
                'eng_example',
                'pol_example',
                'synonyms',
                'opposites'
            ]
        ),
        self.popularity = None
        self.soup = None

    def _bs4_info(self, word):
        langs = {
            'ENG': 'angielskiego',
            'GER': 'niemieckiego',
            'ESP': 'hiszpanskiego',
            'ITA': 'wloskiego',
            'FRA': 'francuskiego'
        }
        
        result = requests.get(f'https://www.diki.pl/slownik-{langs[self.lang]}?q={word}')
        soup = BeautifulSoup(result.text, 'html.parser')
        self.soup = soup

    def extract_data(self, word):
        self._bs4_info(word)
        data_list = []

        try:
            popularity_element = self.soup.find('a', class_='starsForNumOccurrences')
            self.popularity = self.dict_pop[popularity_element.text.strip()] if popularity_element else None
        except AttributeError:
            self.popularity = None

        div_class = self.soup.find_all('div', class_='dictionaryEntity')

        for div in div_class:
            # span_hw = div.find("span", class_="hw")
            # TODO Pomysleć na casem draw/ draw out

            try:
                span_hws = div.find("div", class_="hws").find_all("span", class_="hw")
                english_words = [span.text.strip().lower() for span in span_hws]
            except:
                span_hws = div.find("span", class_="hw")
                english_words = [span_hws.text.strip().lower()]

            if span_hws and word.lower() in english_words:


                for m in div.find_all('li', id=re.compile('^meaning\d+')):

                    # polish_words = [span.get_text(strip=True) for span in m.find_all('span', class_='hw')]
                    polish_words = [span.get_text() for span in m.find_all('span', class_='hw')]
                    polish_word = ', '.join(polish_words)

                    ol_parent = m.find_parent('ol')
                    if ol_parent:
                        part_of_speech_element = ol_parent.find_previous_sibling('div', class_='partOfSpeechSectionHeader')
                        part_of_speech = part_of_speech_element.get_text(strip=True) if part_of_speech_element else None
                        
                        if part_of_speech_element:
                            next_div = part_of_speech_element.find_next_sibling('div')
                            if next_div and ('af' in next_div.get('class', []) or 'vf' in next_div.get('class', [])):
                                other_forms = [span.get_text(strip=True) for span in next_div.find_all('span', class_='foreignTermText')]
                            else:
                                other_forms = []

                    else:
                        part_of_speech = None

                    example_div = m.find('div', class_='exampleSentence')
                    if example_div:
                        example_text = ' '.join(example_div.stripped_strings)
                        eng_example, pol_example = [w.rstrip(')') for w in example_text.split(' (')]
                    else:
                        eng_example, pol_example = None, None

                    synonyms = set()
                    opposites = set()

                    refs = m.find_all('div', class_='ref')
                    for ref in refs:
                        for child_div in ref.find_all('div', recursive=False):
                            text_content = child_div.get_text(strip=True)
                            if text_content.startswith('synon'):
                                links = child_div.find_all('a')
                                synonyms.update([link.get_text() for link in links])
                            elif text_content.startswith('przeciw'):
                                links = child_div.find_all('a')
                                opposites.update([link.get_text() for link in links])
                    
                    synonyms = None if len(list(synonyms)) == 0 else ', '.join(list(synonyms))

                    data_list.append({
                        'english_word': ' - '.join([', '.join(english_words)] + other_forms) + ('' if synonyms == None else f' [{synonyms}]'),
                        # Dodać liste do engipa
                        'pronunciation': ' - '.join([eng_to_ipa.convert(i) for i in [word] + other_forms]) + ('' if synonyms == None else f' [{eng_to_ipa.convert(synonyms)}]'),
                        'part_of_speech': part_of_speech,
                        'polish_word': fix_string(polish_word),
                        'eng_example': eng_example,
                        'pol_example': pol_example
                    })

        self.data = pd.DataFrame(data_list)
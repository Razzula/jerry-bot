# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
'''An interface to the BibleGateway API for retrieving Bible passages.'''
import re
import json
import urllib.parse
import os
import requests
from typing import Final
from bs4 import BeautifulSoup, Tag

class BibleAPI:
    """TODO"""

    def __init__(self, staticDataPath: str):

        try:
            with open(os.path.join(staticDataPath, 'usfms.json'), 'r', encoding='utf-8') as file:
                self.MANIFEST = json.load(file)
        except FileNotFoundError:
            print('Error loading USFM manifest')
            self.MANIFEST = []

    def getBibleReferences(self, text: str) -> list[list[str]] | None:
        """TODO"""

        text = text.upper()

        # get list of references
        references = self.extractReferences(text)
        if (not references):
            return None

        # get translation to use
        encoodedVersion = urllib.parse.quote('NKJV') # TODO: get from user settings
        for translation in ['NKJV', 'KJV', 'ESV', 'NIV', 'NLT']:
            if translation in text:
                encoodedVersion = urllib.parse.quote(translation)
                continue

        results = []
        for reference in references:

            # encode reference
            encodedQuery = urllib.parse.quote(reference)
            url = f'https://www.biblegateway.com/passage?search={encodedQuery}&version={encoodedVersion}'

            try:
                response = requests.get(url, timeout=15)

                if (response.status_code == 200):

                    soup = BeautifulSoup(response.text, 'html.parser')

                    verseElement = soup.select_one('.bcv')
                    if verseElement:
                        verse = verseElement.get_text()
                    else:
                        verse = reference

                    passage = soup.select_one('div.passage-col')

                    elements = passage.select('.text')
                    content: list[str] = []
                    for element in elements:
                        for child in element.children:

                            # extract / format
                            if (isinstance(child, Tag)):
                                if (child.has_attr('class')):
                                    # VERSE NUMBERS
                                    if ('versenum' in child['class']):
                                        text = f'**{child.get_text()}**'
                                    # CHAPTER NUMBERS
                                    elif ('chapternum' in child['class']):
                                        text = f'**{1}**'
                                    # HEADINGS
                                    elif ('heading' in child['class']):
                                        text = f'__**{child.get_text()}**__'
                                    # CONTENT
                                    else:
                                        text = child.get_text()
                                else:
                                    text = child.get_text()

                                content.append(text)

                            else:  # direct text
                                content.append(child)

                    # further formatting
                    contentStr = ' '.join(content)
                    contentStr = re.sub(r'(\(|\[)[a-zA-Z]+(\)|\])', '', contentStr)  # exclude footnotes
                    contentStr = re.sub(r'\s\s+', ' ', contentStr)  # remove extra spaces

                    contents = []
                    # split into chunks
                    while (len(contentStr) >= 1950): # TODO: handle better
                        i = 1950
                        while contentStr[i] != ' ': # ensure no words are split
                            i -= 1
                        contents.append(contentStr[: i + 1])
                        contentStr = contentStr[i + 1 :]
                    contents.append(contentStr)

                    results.append([f'**{verse}** ({encoodedVersion})', contents])

                else:
                    print(f'Request failed with status code: {response.status_code} - {response.reason}')
            except requests.exceptions.RequestException as e:
                print(f'An error occurred: {e}')

        return results

    def getUSFMsFromString(self, reference: str, currentBook: str | None = None, currentChapter: str | None = None) -> dict[str, str | None] | None:
        """Return a compartmenalised 'USFM' object of a Bible reference string."""

        match = re.search(
            r'(I+|[123]+)?\s*([A-Za-z]+)\.? *(\d+)(?::\s*(\d+)(?:\s*-\s*(\d+))?|-(\d+))?(?:.*?([;,].*))?',
            reference.upper(),
        )
        # 1: book number (optional)             III
        # 2: book name                          John    Genesis
        # 3: initial chapter                    3       1
        #                                       :
        # 4: initial verse (optional)           16
        #                                       -       -
        # 5: final verse (optional)             17      2
        # 6: final chapter (optional)
        # 7: additional references (optional)

        usfm: dict[str, str | None] = {}

        if (match):
            if (match.group(2) in ['V', 'VERSE']):  # VERSE REFERENCE
                if ((currentBook is None) or (currentChapter is None)):  # insufficient context
                    return None

                usfm['book'] = currentBook
                usfm['initialChapter'] = currentChapter
                usfm['initialVerse'] = match.group(3)
                usfm['finalVerse'] = match.group(6) if (match.group(6)) else None

            else:
                if (match.group(2) in ['CH', 'CHAPTER']):  # CHAPTER REFERENCE
                    if (currentBook is None):  # insufficient context
                        return None

                    usfm['book'] = currentBook

                else:  # FULL REFERENCE
                    # book name
                    bookNumber: str = ''
                    if (match.group(1) is not None):
                        # account for Roman numerals
                        if (match.group(1).startswith('I')):
                            bookNumber = str(len(match.group(1)))
                        else:
                            bookNumber = match.group(1)

                    bookName: str = bookNumber + match.group(2)

                    for book in self.MANIFEST:
                        if (bookName in book):
                            usfm['book'] = book[0]
                            break

                # chapters, verses
                usfm['initialChapter'] = match.group(3)
                usfm['initialVerse'] = match.group(4) if (match.group(4)) else None
                usfm['finalVerse'] = match.group(5) if (match.group(5)) else None
                usfm['finalChapter'] = match.group(6) if (match.group(6)) else None

        else:  # invalid format (may be shorthand reference)
            if (currentBook is None):  # insufficient context
                return None

            match = re.search(r'(?:(\d+):)?(\d+)(?:-(\d+))?', reference.upper())
            if (not match):  # invalid format
                return None

            usfm['book'] = currentBook

            # chapters, verses
            usfm['initialChapter'] = match.group(1) if (match.group(1)) else currentChapter
            usfm['initialVerse'] = match.group(2) if (match.group(2)) else None
            usfm['finalVerse'] = match.group(3) if (match.group(3)) else None

        return usfm

    def extractReferences(self, text: str, currentBook: str | None = None, currentChapter: str | None = None) -> list[str]:
        """Extracts a list of Bible references from within a string of text."""

        if (text == ''):
            return []
        text = text.upper()

        # detect references
        pattern = re.compile(r'(?:(?:(?:I+|[123]+?)?\s*)(?:[A-Za-z]+)\.? *|(?<=[;,])) ?\d+(?::\s*\d+(?:\s*-\s*\d+)?|-\d+)?')
        matches = re.findall(pattern, text)

        if (not matches): # no references found
            return []

        references: list[str] = []
        for match in matches:
            usfm: dict[str, str | None] | None = self.getUSFMsFromString(match, currentBook, currentChapter)

            if (usfm):
                if (((currentBook := usfm.get('book')) is not None) and ((currentChapter := usfm.get('initialChapter')) is not None)):

                    # format reference into string
                    reference = f'{currentBook} {currentChapter}'
                    if (usfm.get('initialVerse') is not None):
                        reference += f':{usfm.get("initialVerse")}'
                    if (usfm.get('finalVerse') is not None):
                        reference += f'-{usfm.get("finalVerse")}'
                    if (usfm.get('finalChapter') is not None):
                        reference += f'-{usfm.get("finalChapter")}'

                    references.append(reference)

        return references

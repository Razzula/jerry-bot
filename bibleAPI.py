import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup, Tag


try:
    with open('usfms.json', 'r') as file:
        usfmManifest = json.load(file)
except:
    print("Error loading USFM manifest")
    usfmManifest = []


def getUSFMsFromString(reference: str, current_book = None, current_chapter = None):
    
    match = re.search(r'(I+|[123]+)?\s*([A-Za-z]+)\.? *(\d+)(?::\s*(\d+)(?:\s*-\s*(\d+))?|-(\d+))?(?:.*?([;,].*))?', reference.upper())
    """
    1: book number (optional)               III     
    2: book name                            John    Genesis
    3: initial chapter                      3       1
                                           :
    4: initial verse (optional)             16
                                           -       -
    5: final verse (optional)               17      2
    6: final chapter (optional)
    7: additional references (optional)
    """

    usfm = {}

    if (match):
        if ((match.group(2) == 'V') or (match.group(2) == 'VERSE')):  # VERSE REFERENCE
            if ((current_book is None) or (current_chapter is None)):  # insufficient context
                return []
            
            usfm['book'] = current_book
            usfm['initialChapter'] = current_chapter
            usfm['initialVerse'] = int(match.group(3))
            usfm['finalVerse'] = int(match.group(6)) if match.group(6) else None
        else:
            if ((match.group(2) == 'CH') or (match.group(2) == 'CHAPTER')):  # CHAPTER REFERENCE
                if (current_book is None):  # insufficient context
                    return []
                
                usfm['book'] = current_book
            else:  # FULL REFERENCE
                # book name
                if (match.group(1) is None):
                    match_group_1 = ''
                else:
                    # account for Roman numerals
                    if (match.group(1).startswith('I')):
                        match_group_1 = str(len(match.group(1)))
                    else:
                        match_group_1 = match.group(1)
                
                book_name = match_group_1 + match.group(2)

                for book in usfmManifest:
                    if (book_name in book):
                        usfm['book'] = book[0]
                        break

            # chapters, verses
            usfm['initialChapter'] = int(match.group(3))
            usfm['initialVerse'] = int(match.group(4)) if match.group(4) else None
            usfm['finalVerse'] = int(match.group(5)) if match.group(5) else None
            usfm['finalChapter'] = int(match.group(6)) if match.group(6) else None

    else:  # invalid format (may be shorthand reference)
        if (current_book is None):  # insufficient context
            return []
        
        match = re.search(r'(?:(\d+):)?(\d+)(?:-(\d+))?', reference.upper())
        if (not match):  # invalid format
            return []
        
        usfm['book'] = current_book

        # chapters, verses
        usfm['initialChapter'] = int(match.group(1)) if match.group(1) else current_chapter
        usfm['initialVerse'] = int(match.group(2)) if match.group(2) else None
        usfm['finalVerse'] = int(match.group(3)) if match.group(3) else None

    return usfm
    

def extractReferences(text, currentBook=None, currentChapter=None):
    if text == '':
        return []
    text = text.upper()

    # detect references
    pattern = re.compile(r"(?:(?:(?:I+|[123]+?)?\s*)(?:[A-Za-z]+)\.? *|(?<=[;,])) ?\d+(?::\s*\d+(?:\s*-\s*\d+)?|-\d+)?")
    matches = re.findall(pattern, text)

    if (not matches):
        return []

    references = []

    for match in matches:
        usfm = getUSFMsFromString(match, currentBook, currentChapter)

        if ((usfm.get("book") is None) or (usfm.get("initialChapter") is None)):
            continue

        currentBook = usfm.get("book")
        currentChapter = usfm.get("initialChapter")

        reference = f'{usfm.get("book")} {usfm.get("initialChapter")}'
        if (usfm.get("initialVerse") is not None):
            reference += f':{usfm.get("initialVerse")}'
        if (usfm.get("finalVerse") is not None):
            reference += f'-{usfm.get("finalVerse")}'
        if (usfm.get("finalChapter") is not None):
            reference += f'-{usfm.get("finalChapter")}'

        references.append(reference)

    return references


def getBibleReferences(text):

    text = text.upper()

    references = extractReferences(text)
    if (references == []):
        return None
    
    encoodedVersion = urllib.parse.quote('NKJV')
    for translation in ['NKJV','KJV', 'ESV', 'NIV', 'NLT']:
        if (translation in text):
            encoodedVersion = urllib.parse.quote(translation)
            continue
    
    results = []
    for reference in references:

        encodedQuery = urllib.parse.quote(reference)

        url = f'https://www.biblegateway.com/passage?search={encodedQuery}&version={encoodedVersion}'

        try:
            response = requests.get(url)

            if response.status_code == 200:
                
                soup = BeautifulSoup(response.text, "html.parser")

                verseElement = soup.select_one(".bcv")
                if verseElement:
                    verse = verseElement.get_text()
                else:
                    verse = reference

                passage = soup.select_one("div.passage-col")

                elements = passage.select(".text")
                content = []
                for element in elements:
                    for child in element.children:

                        # extract / format
                        if (isinstance(child, Tag)):
                            if (child.has_attr("class")):
                                # VERSE NUMBERS
                                if ("versenum" in child["class"]):
                                    text = f'**{child.get_text()}**'
                                # CHAPTER NUMBERS
                                elif ("chapternum" in child["class"]):
                                    text = f'**{1}**'
                                # HEADINGS
                                elif ("heading" in child["class"]):
                                    text = f'__**{child.get_text()}**__'
                                else:
                                    text = child.get_text()
                            else:
                                text = child.get_text()

                            content.append(text)

                        else:  # direct text
                            content.append(child)

                # further formatting
                content = " ".join(content)
                content = re.sub(r'(\(|\[)[a-zA-Z]+(\)|\])', '', content) # exclude footnotes
                content = re.sub(r'\s\s+', ' ', content) # remove extra spaces

                contents = []
                while (len(content) >= 1950):
                    i = 1950
                    while (content[i] != ' '):
                        i -= 1
                    contents.append(content[:i+1])
                    content = content[i+1:]
                contents.append(content)

                results.append([f'**{verse}** ({encoodedVersion})', contents])

            else:
                print(f"Request failed with status code: {response.status_code} - {response.reason}")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    return results
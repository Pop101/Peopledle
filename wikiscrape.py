import re
from shutil import rmtree
from os import makedirs
from modules.mongrel_db import MongrelDB
from modules import config
from anyascii import anyascii
from modules import wikipedia

# Page layout:
# h2: category title (note that there are 2 h2s that are not category titles: Contents and Navigation menu)
# h3: subsection title (note there are h3s that are not section titles)
# link: hidden anchor element
# div: section content
#   h3 (optional): microsection title
#   h4 (optional): nanosection title
#   ol: list of links (note: there are anchors with class="image". Ignore these)

wikipedia.set_delay(config.get("scrape_delay", 1))
db = MongrelDB(config.get("db_path", "./data"))

 

def splitmatch(pattern, string, flags=0):
    """Splits a string into a list of matches and the text between them
    If there's no match, returns None, `string`

    Args:
        pattern (Regex String): Regex pattern to match
        string (str): Type to match
        flags (int, optional): Regex Flags to apply. Defaults to 0.

    Yields:
        re.Match: Match object
        str: Text between matches
    """
    matches = re.finditer(pattern, string, flags)
    last_match = next(matches, None)

    if last_match == None: return None, string   

    for match in matches:
        yield last_match, string[last_match.end():match.start()]
        last_match = match

    yield last_match, string[last_match.end():]

 
def fetch_people_list_level3() -> list:
    page_body = wikipedia.get_full_page("Wikipedia:Vital Articles")
    page_body = next(filter(
        lambda x: x[0].groups()[0] == 'People',
        splitmatch(r'^==\s?([A-Za-z]+).*==$', page_body, re.M)
    ))[1]
    
    for category, ppl_list in splitmatch(r'^===\s?([A-Za-z]+).*===$', page_body, re.M):
        category = category.groups()[0]
        for person in re.finditer(r'^[#*] ({{Icon\|(\w*)}} )+\[\[((\w|\s)+)\|?((\w|\s)*)\]\] ?$', ppl_list, re.M):
            href = person.groups()[-4]
            name = person.groups()[-2] or href

            db[re.sub(r"[.\\]", "", href)] = {
                "name": name,
                "url": f"https://en.wikipedia.org/wiki/{href.replace(' ', '_')}", # pray this is right (if not, we can burn a request to fix)
                "categories": [category],
                "difficulty": 3,
            }
             
    
def fetch_people_list_level4() -> list:
    page_body = wikipedia.get_full_page("Wikipedia:Vital articles/Level/4/People")

    current_category = []
    for header, body in splitmatch(r'^(=*)\s?([A-Za-z]+).*\1$', page_body, re.M):
        # Update category
        idx = header.groups()[0].count('=') - 2
        current_category = current_category[:idx]
        current_category.append(header.groups()[1])

        # Add people from body text
        for person in re.finditer(r'^[#*] ({{Icon\|(\w*)}} )+\[\[((\w|\s)+)\|?((\w|\s)*)\]\] ?$', body, re.M):
                href = person.groups()[-4].replace(' ', '_')
                name = person.groups()[-2] or href

                print([re.sub(r"[.\\]", "", href)], {
                    "name": name,
                    "url": f"https://en.wikipedia.org/wiki/{href}",
                    "categories": current_category,
                    "difficulty": 3,
                })


def populate_person_details(name: str) -> str:
    """Given a person's name,
    fetches their details off wikipedia and stores them in the db.
    """
    summary_markup = wikipedia.get_page_html_summary(name)
    content = wikipedia.get_page_text(name)
    
    # Remove references and bibliography sections from the content        
    content = re.sub(r'==.*bibliography(.|\s)*', "", content, flags=re.IGNORECASE)
    content = re.sub(r'==.*References(.|\s)*', "", content, flags=re.IGNORECASE)
    content = re.sub(r'==.*See also(.|\s)*', "", content, flags=re.IGNORECASE)
    content = re.sub(r'==.*Further reading(.|\s)*', "", content, flags=re.IGNORECASE)
    content = re.sub(r'==.*External links(.|\s)*', "", content, flags=re.IGNORECASE)
    content = re.sub(r'== Notes ==(.|\s)*', "", content, flags=re.IGNORECASE)
        
    # Remove all other headers
    content = re.sub(r"=+\s+.*?\s+=+", "", content)
    content = re.sub(r"\s+", " ", content.replace("\n", ". "))
    content = re.sub(r"\.(?=[A-Z])", ". ", content) # Add weirdly missing spaces back

    # Get all sentences that contain the person's name
    # (this is used to generate the questions later)
    sentences_with_name = list()
    for sentence in re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", content):
        name_part_list = name.split()
        for name_part in name_part_list:
            if len(name_part) >= 3 and name_part in sentence:

                # Clean up the sentence
                # 1. Remove everything inside parentheses, including the parentheses
                sentence = re.sub(r'\([^)]*\)', '', sentence)

                # 2. Remove everything past a comma, including the comma
                # sentence = re.sub(r',.*', '', sentence)

                # 3. Split name into Name-Components, 1 through ??? (probably no more than 5)
                # 4. Redact each of these per sentence by replacing it with [NAME COMPONENT X] where X is the number of the component.
                for name_number, name_part in enumerate(name_part_list):
                    if len(name_part) < 3:
                        continue
                    #sentence = re.sub(name_part,'[NAME COMPONENT ' + str(name_number + 1) + ']',sentence)
                    sentence = re.sub(name_part, '█'*len(name_part), sentence)

                sentences_with_name.append(sentence)
                break

    # Get the page image, if it exists
    # This takes an extra web request
    img = wikipedia.get_image_url(name)

    # Dump anything we've found into the db
    db_name = re.sub(r"[.\\]", "", name)
    if db_name not in db: db[db_name] = dict()
    db[db_name] = {
        "name": name,
        "url": f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}",
        "difficulty": 5,
        "categories": list(), # would be cool to get this to work, just in general. Good hint system
        **db[db_name], # overwrite the above with any existing data
        "img": img,
        "summary": summary_markup,
        "content": content,
        "sentences": sentences_with_name,
    }


def main() -> None:
    rmtree(config.get("db_path", "./data"), ignore_errors=True)
    makedirs(config.get("db_path", "./data"))
    
    if int(config.get("difficulty", 3)) >= 4:
        fetch_people_list_level4()
    if int(config.get("difficulty", 3)) >= 3:
        fetch_people_list_level3()
    
        for name in db:
            print(f"Fetching {name}...")
            populate_person_details(db[name]["name"])
    
    for name in config.get("additional_people", []):
        print(f"Fetching {name}...")
        populate_person_details(anyascii(name))

if __name__ == "__main__":
    main()
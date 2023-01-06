import requests
import re
import time
from parsel import Selector
from modules.mongrel_db import MongrelDB
import wikipedia

# Page layout:
# h2: category title (note that there are 2 h2s that are not category titles: Contents and Navigation menu)
# h3: subsection title (note there are h3s that are not section titles)
# link: hidden anchor element
# div: section content
#   h3 (optional): microsection title
#   h4 (optional): nanosection title
#   ol: list of links (note: there are anchors with class="image". Ignore these)

REQUEST_DELAY = 0.5  # seconds

db = MongrelDB("./data")
time_of_last_request = 0


def ensure_request_delay():
    global time_of_last_request

    if time.time() - time_of_last_request < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - (time.time() - time_of_last_request))


def get_page(url) -> str:
    """Gets the page at the given url"""
    ensure_request_delay()

    response = requests.get(url)
    time_of_last_request = time.time()
    response.raise_for_status()
    return response.text

def fetch_people_list_level3() -> list[dict]:
    page = get_page("https://en.wikipedia.org/wiki/Wikipedia:Vital_articles")
    page = Selector(page)
    
    current_category = (None, None, None, None)
    people_div = page.xpath('//*[@id="mw-content-text"]/div[1]/div[4]/div/h2[2]/following-sibling::*[1]')[0]
    h_a_selector = """.//h3 | .//a[not(@class="image")]"""
    
    for elem in people_div.xpath(h_a_selector):
        elem_type = elem.xpath("name()").get()
        if re.match(r"h\d", elem_type):
            # header
            text = elem.css("::text").get()
            text = re.sub(r"\s+", " ", text)
            text = re.sub(r"\(.*\)", "", text).strip()
            
            current_category = [text, None, None, None]
        elif elem_type == "a":
            # Link
            person = elem.css("::text").get()
            href = elem.xpath("@href").get()
            if "Wikipedia:" in href:
                continue

            print(person)
            db[re.sub(r"[.\\]", "", person)] = {
                "name": person,
                "url": f"https://en.wikipedia.org{href}",
                "categories": current_category,
                "difficulty": 3,
            }
            
    
def fetch_people_list_level4() -> list[dict]:
    page = get_page("https://en.wikipedia.org/wiki/Wikipedia:Vital_articles/Level/4/People")
    page = Selector(page)

    # Iterate through all relevant headers and links in the page
    current_category = (None, None, None, None)
    h_a_selector = """//h2[not(contains(., "Navigation") or contains(., "Contents") or contains(.,"ext-"))] |
                      //h3[not(contains(@id, "p-"))] | //h4 | //h5 |
                      //div[@class="div-col"]//ol//a[not(@class="image")]"""

    for elem in page.xpath(h_a_selector):
        elem_type = elem.xpath("name()").get()
        if re.match(r"h\d", elem_type):
            text = elem.css("::text").get()
            text = re.sub(r"\s+", " ", text)
            text = re.sub(r"\(.*\)", "", text).strip()

            # Use headers to set category details
            if elem_type == "h2":
                current_category = (text, None, None, None)
            elif elem_type == "h3":
                current_category = (current_category[0], text, None, None)
            elif elem_type == "h4":
                current_category = (current_category[0], current_category[1], text, None)
            elif elem_type == "h5":
                current_category = (
                    current_category[0],
                    current_category[1],
                    current_category[2],
                    text,
                )
            print(current_category)

        # If the element is a link, store it in the db
        elif elem_type == "a":
            person = elem.css("::text").get()
            href = elem.xpath("@href").get()
            if "Wikipedia:" in href:
                continue

            print(person)
            db[re.sub(r"[.\\]", "", person)] = {
                "name": person,
                "url": f"https://en.wikipedia.org{href}",
                "categories": current_category,
                "difficulty": 4,
            }


def populate_person_details(name: str) -> str:
    """Given a person's name,
    fetches their details off wikipedia and stores them in the db.
    """
    ensure_request_delay()

    page = wikipedia.page(title=name, auto_suggest=False, redirect=True)
    
    summary = page.summary
    content = page.content
    
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
    for sentence in re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", summary + ". " + content):
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
    img = "/static/img/question.svg"
    parsel = Selector(get_page(page.url))  # very slow, but necessary to get the correct image
    if html_img := parsel.xpath('//tbody/tr/td[contains(@class, "photo") or contains(@class, "infobox-image")]/a/img'):
        img = html_img.xpath("./@src").get()

    # Dump anything we've found into the db
    db_name = re.sub(r"[.\\]", "", name)
    db[db_name] = {
        **db[db_name],
        "img": img,
        "summary": summary,
        "content": content,
        "sentences": sentences_with_name,
    }


if __name__ == "__main__":
    # fetch_people_list_level4()
    fetch_people_list_level3()
    for name in db:
        print(f"Fetching {name}...")
        populate_person_details(db[name]["name"])

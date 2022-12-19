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


def fetch_people_list_level4() -> list[dict]:
    page = get_page("https://en.wikipedia.org/wiki/Wikipedia:Vital_articles/Level/4/People")
    page = Selector(page)

    # Iterate through all relevant headers and links in the page
    current_category = (None, None, None, None)
    h_a_selector = """//h2[not(contains(., "Navigation") or contains(., "Contents") or contains(.,"ext-"))] |
                      //h3[not(contains(@id, "p-"))] | //h4 | //h5 |
                      //div[@class="div-col"]//ol/li/a[not(@class="image")]"""

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
    
    # Remove references and bibliography sections from the content
    # Also remove all headers
    content = page.content
    if "== References ==" in content:
        content = content[: content.find("== References ==")]
    if "== Bibliography ==" in content:
        content = content[: content.find("== Bibliography ==")]
    content = re.sub(r"=+\s+.*?\s+=+", "", content)
    content = re.sub(r"\s+", " ", content.replace("\n", " "))

    # Get all sentences that contain the person's name
    # (this is used to generate the questions later)
    sentences_with_name = set()
    for sentence in re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", summary + " " + content):
        for name_part in name.split():
            if len(name_part) >= 3 and name_part in sentence:
                sentences_with_name.add(sentence)
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
        "sentences": list(sentences_with_name),
    }


if __name__ == "__main__":
    fetch_people_list_level4()
    for name in db:
        print(f"Fetching {name}...")
        populate_person_details(db[name]["name"])

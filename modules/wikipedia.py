import requests
import time
from .simplecache import FixedSizeDict, cache, MB

USER_AGENT = "Peopledle WikiBot/1.0 (https://github.com/Pop101/Peopledle)"
REQUEST_DELAY = 0.05
time_of_last_request = 0


def set_delay(delay):
    global REQUEST_DELAY
    REQUEST_DELAY = delay


def ensure_request_delay():
    global time_of_last_request

    if time.time() - time_of_last_request < REQUEST_DELAY:
        time.sleep(max(0, REQUEST_DELAY - (time.time() - time_of_last_request)))
    time_of_last_request = time.time()


@cache(0.25 * MB)
def search_page(query: str) -> str:
    """Searches for the given query and returns the correct page title"""
    ensure_request_delay()

    res = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srprop": "",
            "srlimit": 1,
            "limit": 1,
            "srsearch": query,
            "format": "json",
        },
        headers={"User-Agent": USER_AGENT},
    )

    res.raise_for_status()
    res = res.json()
    if "error" in res:
        raise Exception(res["error"]["info"])

    return res["query"]["search"][0]["title"]


@cache(0.75 * MB)
def wiki_request(page: str, page_params: dict):
    """Makes a request to the Wikipedia API"""

    # First, do a search for the page
    title = search_page(page)

    # Then, make the request
    ensure_request_delay()

    for banned in ("pageids", "titles"):
        if banned in page_params:
            del page_params[banned]

    page_params["action"] = page_params.get("action", "query")
    page_params["format"] = "json"
    page_params["titles"] = title
    page_params["redirects"] = "" # requires additional handling, ignore for now
    res = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params=page_params,
        headers={"User-Agent": USER_AGENT},
    )

    res.raise_for_status()
    res = res.json()
    if "error" in res:
        raise Exception(res["error"]["info"])

    # Return this (the first page)'s data
    return res["query"]["pages"][list(res["query"]["pages"].keys())[0]]


def get_image_url(page: str) -> str:
    """Gets the image URL for the given page"""
    try:
        return wiki_request(page, {"prop": "pageimages", "piprop": "original"})["original"]["source"]
    except KeyError:
        return "/static/img/question.svg"


def get_page_url(page: str) -> str:
    """Gets the page URL for the given page. Returns a placeholder if the image doesn't exist"""
    return wiki_request(page, {"prop": "info", "inprop": "url"})["fullurl"]


def get_page_html_summary(page: str) -> str:
    """Gets the summary, in html markup, for the given page"""
    return wiki_request(page, {"prop": "extracts", "exintro": "", "exsentences": 10})["extract"]

def get_page_summary(page: str) -> str:
    """Gets the summary, in plaintext, for the given page"""
    return wiki_request(page, {"prop": "extracts", "explaintext": "", "exintro": "", "exsentences": 10})["extract"]

def get_page_text(page: str) -> str:
    """Gets the full page plaintext for the given page"""
    return wiki_request(page, {"prop": "extracts", "explaintext": ""})["extract"]


def get_full_page(page: str) -> str:
    """Gets the full page data for the given page"""
    return wiki_request(page, {"prop": "revisions", "rvprop": "content", "rvlimit": 1, "rvslots": "main"})["revisions"][0]["slots"]["main"]["*"]


if __name__ == "__main__":
    print(get_image_url("India"))
    print(get_page_url("India"))
    print(get_page_summary("Pakistan"))
    print(get_full_page("Wikipedia:Vital Articles"))

import sys
import json
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://anixl.to"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Helper Functions ---
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {e}", file=sys.stderr)
        return None

def get_resolved_qwik_json(soup, required_key):
    """
    Parses the Qwik JSON and recursively resolves the object references to create
    a clean, easy-to-use data object. This version is more robust.
    """
    script_tag = soup.find('script', {'type': 'qwik/json'})
    if not script_tag:
        return None
    
    try:
        qwik_data = json.loads(script_tag.string)
        refs = qwik_data.get('refs', {})
        objs = qwik_data.get('objs', [])
        
        # Memoization cache to avoid re-resolving the same reference and prevent infinite loops.
        memo = {}

        def resolve(value):
            """Recursively resolves reference IDs to their actual data."""
            if isinstance(value, str) and value in refs:
                # If we've already resolved this reference, return the cached result.
                if value in memo:
                    return memo[value]
                
                obj_index_str = refs[value].split(' ')[0].replace('!', '')
                try:
                    # IMPORTANT: Add a placeholder to the cache BEFORE the recursive call
                    # to handle potential circular references.
                    memo[value] = None 
                    result = resolve(objs[int(obj_index_str, 36)])
                    memo[value] = result # Update cache with the actual result
                    return result
                except (ValueError, IndexError):
                    return value # Return the ref ID if lookup fails
            elif isinstance(value, list):
                return [resolve(v) for v in value]
            elif isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            return value

        # Find the specific object that contains our required key
        initial_object = None
        for obj in objs:
            if isinstance(obj, dict) and required_key in obj:
                initial_object = obj
                break
        
        if initial_object:
            # Resolve all references starting from our initial object.
            return resolve(initial_object)

    except Exception as e:
        print(f"Error resolving Qwik JSON: {e}", file=sys.stderr)
        return None
    return None


# --- Scraper Functions ---

def scrape_recent_episodes():
    """Scrapes the homepage for the latest episode releases."""
    soup = make_request(BASE_URL)
    if not soup: return []
    recent_episodes = []
    for item in soup.select('div[q\\:key="3m_3"] .flex.border-b'):
        title_element = item.select_one('h3 a')
        episode_element = item.select_one('span a')
        img_element = item.select_one('img')
        if title_element and episode_element and img_element:
            recent_episodes.append({
                'id': title_element['href'].split('/')[2],
                'title': title_element.text.strip(),
                'image': BASE_URL + img_element['src'],
                'episode_title': episode_element.text.strip()
            })
    return recent_episodes

def scrape_search(query):
    """Scrapes the website for a given search query."""
    search_url = f"{BASE_URL}/search?word={query}"
    soup = make_request(search_url)
    if not soup: return []
    search_results = []
    for item in soup.select('.grid > .flex.border-b'):
        title_element = item.select_one('h3 a')
        img_element = item.select_one('img')
        if title_element and img_element:
            search_results.append({
                'id': title_element['href'].split('/')[2],
                'title': title_element.text.strip(),
                'image': BASE_URL + img_element['src']
            })
    return search_results

def scrape_anime_details(anime_id):
    """Scrapes the detail page of a specific anime."""
    anime_url = f"{BASE_URL}/title/{anime_id}"
    soup = make_request(anime_url)
    if not soup: return None

    data = get_resolved_qwik_json(soup, 'info_title')
    if not data or not isinstance(data, dict):
        return {"error": "Could not parse page data."}

    title = data.get('info_title', 'Title not found')
    description = data.get('info_filmdesc', 'No description available.')
    image = BASE_URL + data.get('urlCover600', '')
    
    episodes = []
    if 'episodesNodes_last' in data and isinstance(data['episodesNodes_last'], list):
        for ep_data in data['episodesNodes_last']:
            if isinstance(ep_data, dict):
                episodes.append({
                    'id': ep_data.get('ep_id'),
                    'number': ep_data.get('ep_index'),
                    'title': ep_data.get('ep_title')
                })
    episodes.sort(key=lambda x: int(x.get('number', 0)))

    return {
        'title': title,
        'description': description,
        'image': image,
        'episodes': episodes
    }

def scrape_stream_link(episode_id):
    """Scrapes an episode page to find the video stream URL."""
    try:
        anime_id, ep_id_simple = episode_id.split(',')
        watch_url = f"{BASE_URL}/title/{anime_id}/{ep_id_simple}"
    except ValueError:
        return {"error": "Invalid episodeId format. Expected 'animeId,episodeId'."}

    soup = make_request(watch_url)
    if not soup: return None

    data = get_resolved_qwik_json(soup, 'sourcesNode_list')
    if not data or not isinstance(data, dict):
        return {"error": "Could not parse stream data."}

    sources_list = data.get('sourcesNode_list', [])
    if not sources_list:
        return {"error": "No sources list found on the watch page."}

    stream_url = None
    for source in sources_list:
        if source.get('src_name') == 'sub' and source.get('m3u8_lists'):
            stream_url = source['m3u8_lists'].get('url')
            if stream_url: break
    
    if not stream_url:
        for source in sources_list:
            if source.get('m3u8_lists'):
                stream_url = source['m3u8_lists'].get('url')
                if stream_url: break

    return { 'stream_url': stream_url }

# --- Main Execution Block ---
if __name__ == "__main__":
    command = sys.argv[1]
    result = {}
    
    try:
        if command == 'recent':
            result = scrape_recent_episodes()
        elif command == 'search':
            query = sys.argv[2]
            result = scrape_search(query)
        elif command == 'details':
            anime_id = sys.argv[2]
            result = scrape_anime_details(anime_id)
        elif command == 'stream':
            episode_id = sys.argv[2]
            result = scrape_stream_link(episode_id)
        else:
            result = {"error": "Unknown command"}
    except Exception as e:
        result = {"error": f"An unexpected error occurred in the bot: {str(e)}"}
        print(result, file=sys.stderr)

    print(json.dumps(result))

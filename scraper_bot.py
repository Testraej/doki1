import sys
import json
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://anixl.to"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {e}", file=sys.stderr)
        return None

def get_data_from_qwik_json(soup):
    script_tag = soup.find('script', {'type': 'qwik/json'})
    if not script_tag:
        return None
    
    try:
        qwik_json = json.loads(script_tag.string)
        if 'objs' in qwik_json and qwik_json['objs']:
            main_data = max(qwik_json['objs'], key=lambda x: len(json.dumps(x)) if isinstance(x, (dict, list)) else 0)
            return main_data
    except (json.JSONDecodeError, IndexError, TypeError):
        return None
    return None

def scrape_recent_episodes():
    soup = make_request(BASE_URL)
    if not soup:
        return []

    recent_episodes = []
    for item in soup.select('div[q\\:key="3m_3"] .flex.border-b'):
        title_element = item.select_one('h3 a')
        episode_element = item.select_one('span a')
        img_element = item.select_one('img')
        
        if title_element and episode_element and img_element:
            title = title_element.text.strip()
            anime_id = title_element['href'].split('/')[2]
            image = BASE_URL + img_element['src']
            episode_title = episode_element.text.strip()

            recent_episodes.append({
                'id': anime_id,
                'title': title,
                'image': image,
                'episode_title': episode_title
            })
    return recent_episodes

def scrape_search(query):
    search_url = f"{BASE_URL}/search?word={query}"
    soup = make_request(search_url)
    if not soup:
        return []

    search_results = []
    for item in soup.select('.grid > .flex.border-b'):
        title_element = item.select_one('h3 a')
        img_element = item.select_one('img')

        if title_element and img_element:
            title = title_element.text.strip()
            anime_id = title_element['href'].split('/')[2]
            image = BASE_URL + img_element['src']
            
            search_results.append({
                'id': anime_id,
                'title': title,
                'image': image
            })
    return search_results

def scrape_anime_details(anime_id):
    anime_url = f"{BASE_URL}/title/{anime_id}"
    soup = make_request(anime_url)
    if not soup:
        return None

    data = get_data_from_qwik_json(soup)
    if not data or not isinstance(data, dict):
        return {"error": "Could not parse page data."}

    title = data.get('info_title', 'Title not found')
    description = data.get('info_filmdesc', 'No description available.')
    image = BASE_URL + data.get('urlCover600', '')
    
    episodes = []
    if 'episodesNodes_last' in data and isinstance(data['episodesNodes_last'], dict):
        for ep_key, ep_data in data['episodesNodes_last'].items():
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
    try:
        anime_id, ep_id_simple = episode_id.split(',')
        watch_url = f"{BASE_URL}/title/{anime_id}/{ep_id_simple}"
    except ValueError:
        return {"error": "Invalid episodeId format. Expected 'animeId,episodeId'."}

    soup = make_request(watch_url)
    if not soup:
        return None

    data = get_data_from_qwik_json(soup)
    if not data or not isinstance(data, list):
        return {"error": "Could not parse stream data."}

    sources_list = None
    for item in data:
        if isinstance(item, dict) and 'sourcesNode_list' in item:
            sources_list = item['sourcesNode_list']
            break
    
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
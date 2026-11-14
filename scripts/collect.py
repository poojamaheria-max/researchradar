"""Fetch Europe PMC records and publish a static JSON feed.
No dependencies beyond the Python standard library.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config.json').read_text())
DATA = ROOT / 'docs' / 'data.json'
STATE = ROOT / 'state.json'
TODAY = dt.datetime.now(dt.timezone.utc).isoformat()


def fetch(query, size):
    params = urllib.parse.urlencode({
        'query': query, 'format': 'json', 'pageSize': min(size, 100),
        'sort': 'FIRST_PDATE_D desc', 'resultType': 'core'
    })
    req = urllib.request.Request('https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + params,
                                 headers={'User-Agent': 'ResearchRadar/0.1 (personal research monitor)'})
    with urllib.request.urlopen(req, timeout=35) as response:
        return json.load(response)['resultList']['result']


def normalize(record, topic):
    source = record.get('source', '')
    ident = record.get('id', '')
    doi = record.get('doi', '')
    link = 'https://doi.org/' + doi if doi else ('https://europepmc.org/article/' + source + '/' + ident)
    title = record.get('title', '').strip()
    abstract = record.get('abstractText', '')
    return {'id': source + ':' + ident, 'topic': topic, 'title': title,
            'authors': record.get('authorString', ''), 'journal': record.get('journalTitle', ''),
            'date': record.get('firstPublicationDate', record.get('firstIndexDate', '')),
            'abstract': abstract, 'url': link, 'source': source,
            'doi': doi, 'is_preprint': source == 'PPR'}


def send_notification(topic, item):
    endpoint = os.environ.get('NTFY_TOPIC_URL', '').strip().rstrip('/')
    if not endpoint:
        return
    body = (item['title'] + '\n' + item['url']).encode('utf-8')
    req = urllib.request.Request(endpoint, data=body, method='POST', headers={
        'Title': 'ResearchRadar: ' + topic, 'Tags': 'microscope',
        'Click': item['url'], 'Priority': 'default'
    })
    with urllib.request.urlopen(req, timeout=20):
        pass


def main():
    old_state = json.loads(STATE.read_text()) if STATE.exists() else None
    known = set(old_state.get('seen', [])) if old_state else set()
    all_items = {}
    found_ids = set()
    new_items = []
    errors = []
    for topic in CONFIG['topics']:
        try:
            records = fetch(topic['query'], CONFIG.get('max_results_per_topic', 70))
        except Exception as exc:
            errors.append(topic['name'] + ': ' + str(exc))
            continue
        for rec in records:
            item = normalize(rec, topic['name'])
            if not item['id'] or not item['title']:
                continue
            key = topic['name'] + '|' + item['id']
            found_ids.add(key)
            if key not in known and old_state is not None:
                new_items.append((topic['name'], item))
            if item['id'] not in all_items:
                item['topics'] = [topic['name']]
                all_items[item['id']] = item
            elif topic['name'] not in all_items[item['id']]['topics']:
                all_items[item['id']]['topics'].append(topic['name'])
    if errors and not all_items:
        raise RuntimeError('All sources failed: ' + '; '.join(errors))
    DATA.parent.mkdir(exist_ok=True)
    # Keep the last successful feed for topics that failed this run.
    if errors and DATA.exists():
        prior = json.loads(DATA.read_text())
        for item in prior.get('items', []):
            if item['id'] not in all_items:
                all_items[item['id']] = item
    items = sorted(all_items.values(), key=lambda x: x['date'], reverse=True)
    DATA.write_text(json.dumps({'updated': TODAY, 'items': items, 'errors': errors}, ensure_ascii=False, indent=2))
    STATE.write_text(json.dumps({'seen': sorted(known | found_ids), 'updated': TODAY}, indent=2))
    if old_state is None:
        print('Initial scan: loaded existing research, no notifications sent.')
    else:
        for topic, item in new_items[:10]:
            try:
                send_notification(topic, item)
            except Exception as exc:
                print('Notification failed:', exc)
    print('Items:', len(items), 'new:', len(new_items), 'errors:', errors)


if __name__ == '__main__':
    main()

# File: src/collectors/rss_macro.py
#!/usr/bin/env python3
import os
import json
import hashlib
import logging
import yaml
import feedparser
import httpx
from bs4 import BeautifulSoup, FeatureNotFound
from bs4.element import Tag
from dateutil import parser as dt
from dotenv import load_dotenv
from supabase import create_client

# Supabase init
def _init_supabase():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not (url and key):
        logging.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        raise SystemExit(1)
    return create_client(url, key)

# Load macro feeds YAML
CFG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", 'feeds_macro.yml')
)
with open(CFG_PATH, encoding='utf-8') as f:
    FEEDS = yaml.safe_load(f)

# Save helper
def _save_macro(item: dict, feed_id: str, supabase, debug: bool):
    guid = item.get('id') or hashlib.sha256(
        item.get('link','').encode('utf-8')
    ).hexdigest()
    try:
        published_at = dt.parse(item.get('published','')).isoformat()
    except Exception:
        published_at = None
    record = {
        'guid': guid,
        'source': feed_id,
        'title': item.get('title',''),
        'summary': item.get('summary',''),
        'published_at': published_at,
        'raw_json': json.dumps(item, default=str)
    }
    res = supabase.table('raw_news_macro').upsert(record).execute()
    err = getattr(res, 'error', None)
    status = getattr(res, 'status_code', None)
    if err or (status and status >= 300):
        logging.error('Erro ao salvar GUID %s: %s', guid, err or status)
    elif debug:
        logging.debug('Salvo macro GUID %s do feed %s', guid, feed_id)

# Poll macro RSS

def _poll_macro_rss(feed: dict, supabase, debug: bool):
    fid = feed.get('id','')
    url = feed.get('url','')
    logging.debug('Polling RSS macro %s → %s', fid, url)
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except httpx.ReadTimeout:
        logging.error('Timeout accessing RSS macro %s: %s', fid, url)
        return
    except Exception as e:
        logging.error('Erro RSS macro %s: %s', fid, e)
        return
    try:
        soup = BeautifulSoup(resp.content, 'xml')
    except FeatureNotFound:
        soup = BeautifulSoup(resp.content, 'html.parser')
    parsed = feedparser.parse(str(soup))
    for entry in parsed.entries or []:
        item = {
            'id': entry.get('id'),
            'link': entry.get('link',''),
            'title': entry.get('title',''),
            'summary': entry.get('summary',''),
            'published': entry.get('published', entry.get('updated',''))
        }
        _save_macro(item, fid, supabase, debug)
    logging.info('RSS macro %s → %d entradas', fid, len(parsed.entries or []))

# Poll macro sitemap

def _poll_macro_sitemap(feed: dict, supabase, debug: bool):
    fid = feed.get('id','')
    url = feed.get('url','')
    logging.debug('Polling sitemap %s → %s', fid, url)
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except httpx.ReadTimeout:
        logging.error('Timeout accessing sitemap %s: %s', fid, url)
        return
    except Exception as e:
        logging.error('Erro sitemap %s: %s', fid, e)
        return
    try:
        soup = BeautifulSoup(resp.content, 'xml')
    except FeatureNotFound:
        soup = BeautifulSoup(resp.content, 'html.parser')
    count = 0
    for url_tag in soup.find_all('url'):
        if not isinstance(url_tag, Tag):
            continue
        loc = url_tag.find('loc')
        news = url_tag.find('news:news')
        if not (isinstance(loc, Tag) and isinstance(news, Tag)):
            continue
        link = loc.text.strip()
        title_el = news.find('news:title')
        date_el = news.find('news:publication_date')
        item = {
            'id': hashlib.sha256(link.encode('utf-8')).hexdigest(),
            'link': link,
            'title': title_el.text.strip() if isinstance(title_el, Tag) else '',
            'summary': '',
            'published': date_el.text.strip() if isinstance(date_el, Tag) else ''
        }
        _save_macro(item, fid, supabase, debug)
        count += 1
    logging.info('Sitemap %s → %d URLs', fid, count)

# Entry point for macro collector
def run_macro(debug: bool = False):
    logging.getLogger().setLevel(logging.DEBUG if debug else logging.INFO)
    supabase = _init_supabase()
    logging.info('Iniciando coleta macro%s', ' (DEBUG)' if debug else '')
    for feed in FEEDS:
        fid = feed.get('id','').lower()
        if fid.startswith('bloomberg'):
            _poll_macro_sitemap(feed, supabase, debug)
        else:
            _poll_macro_rss(feed, supabase, debug)
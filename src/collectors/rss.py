# File: src/collectors/rss.py
#!/usr/bin/env python3
import os
import json
import hashlib
import logging
import yaml
import feedparser
import httpx
from bs4 import BeautifulSoup, FeatureNotFound
from dateutil import parser as dt
from dotenv import load_dotenv
from supabase import create_client

# Supabase & config

def _init_supabase():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not (url and key):
        logging.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        raise SystemExit(1)
    return create_client(url, key)

# Load corporate feeds YAML
CFG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", 'feeds_corporate.yml')
)
with open(CFG_PATH, encoding='utf-8') as f:
    FEEDS = yaml.safe_load(f)

# Save helper
def _save_corp(item: dict, feed_id: str, supabase, debug: bool):
    guid = item.get('id') or hashlib.sha256(
        item.get('link','').encode('utf-8')
    ).hexdigest()
    try:
        published_at = dt.parse(item.get('published','')).isoformat()
    except Exception:
        published_at = None
    record = {
        'guid': guid,
        'feed_id': feed_id,
        'title': item.get('title',''),
        'link': item.get('link',''),
        'published_at': published_at,
        'raw': json.dumps(item, default=str)
    }
    res = supabase.table('raw_news').upsert(record).execute()
    err = getattr(res, 'error', None)
    status = getattr(res, 'status_code', None)
    if err or (status and status >= 300):
        logging.error('Erro ao salvar GUID %s: %s', guid, err or status)
    elif debug:
        logging.debug('Salvo GUID %s do feed %s', guid, feed_id)

# Poll corporate RSS

def _poll_corp(feed: dict, supabase, debug: bool):
    fid = feed.get('id','')
    url = feed.get('url','')
    logging.debug('Polling RSS corp %s → %s', fid, url)
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except httpx.ReadTimeout:
        logging.error('Timeout accessing RSS corp %s: %s', fid, url)
        return
    except Exception as e:
        logging.error('Erro RSS corp %s: %s', fid, e)
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
            'published': entry.get('published', entry.get('updated',''))
        }
        _save_corp(item, fid, supabase, debug)
    logging.info('RSS corp %s → %d entradas', fid, len(parsed.entries or []))

# Entry point for corporate collector
def run_corporate(debug: bool = False):
    logging.getLogger().setLevel(logging.DEBUG if debug else logging.INFO)
    supabase = _init_supabase()
    logging.info('Iniciando coleta corporate%s', ' (DEBUG)' if debug else '')
    for feed in FEEDS:
        _poll_corp(feed, supabase, debug)
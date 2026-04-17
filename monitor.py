"""
GSC Traffic Monitor - Simple Daily Collector
Собирает ежедневные данные из Google Search Console
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import requests

# Supabase
SUPABASE_URL = "https://puxnigzdbscstvjlyvbg.supabase.co"
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1eG5pZ3pkYnNjc3R2amx5dmJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzMxNDIsImV4cCI6MjA5MTMwOTE0Mn0.fxNYsN9ZlXIoJSbQdflKLSP7w-69TY4r8AP3biZsdmY')

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def get_gsc_service():
    """Создаёт GSC сервис из credentials"""
    creds_json = os.environ.get('GSC_CREDENTIALS')
    if not creds_json:
        raise ValueError("GSC_CREDENTIALS not set")
    
    creds_info = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_info, 
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    return build('searchconsole', 'v1', credentials=credentials)

def get_sites(service):
    """Получает список всех сайтов"""
    result = service.sites().list().execute()
    return [site['siteUrl'] for site in result.get('siteEntry', [])]

def fetch_data(service, site_url, start_date, end_date, dimensions, limit=25000):
    """Запрашивает данные из GSC API"""
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': limit
            }
        ).execute()
        return response.get('rows', [])
    except Exception as e:
        print(f"  ⚠️ Error {dimensions}: {e}")
        return []

def save_to_supabase(table, data):
    """Сохраняет данные в Supabase (upsert по site_url+date)"""
    if not data:
        return 0

    # Batch по 500 записей
    saved = 0
    for i in range(0, len(data), 500):
        batch = data[i:i+500]
        try:
            r = requests.post(
                f"{SUPABASE_URL}/rest/v1/{table}?on_conflict=site_url,date",
                headers=HEADERS,
                json=batch,
                timeout=30
            )
            if r.status_code in [200, 201]:
                saved += len(batch)
            else:
                print(f"  ❌ {table}: {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"  ❌ {table}: {e}")

    return saved

def process_site(service, site_url, start_date, end_date):
    """Обрабатывает один сайт"""
    
    # 1. Daily data (по дням)
    daily_rows = fetch_data(service, site_url, start_date, end_date, ['date'])
    daily_data = []
    for row in daily_rows:
        daily_data.append({
            "site_url": site_url,
            "date": row['keys'][0],
            "clicks": row['clicks'],
            "impressions": row['impressions'],
            "position": round(row['position'], 2),
            "ctr": round(row['ctr'], 4)
        })
    
    saved_daily = save_to_supabase('traffic_daily', daily_data)
    print(f"  📅 Daily: {saved_daily} rows")
    
    # 2. Totals (суммарно за период)
    total_clicks = sum(r['clicks'] for r in daily_rows)
    total_impressions = sum(r['impressions'] for r in daily_rows)
    avg_position = sum(r['position'] for r in daily_rows) / len(daily_rows) if daily_rows else 0
    avg_ctr = sum(r['ctr'] for r in daily_rows) / len(daily_rows) if daily_rows else 0
    
    # 3. Предыдущий период для сравнения
    period_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
    prev_end = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_start = (datetime.strptime(prev_end, '%Y-%m-%d') - timedelta(days=period_days-1)).strftime('%Y-%m-%d')
    
    prev_rows = fetch_data(service, site_url, prev_start, prev_end, ['date'])
    prev_clicks = sum(r['clicks'] for r in prev_rows)
    prev_impressions = sum(r['impressions'] for r in prev_rows)
    
    clicks_change = ((total_clicks - prev_clicks) / prev_clicks * 100) if prev_clicks > 0 else 0
    impressions_change = ((total_impressions - prev_impressions) / prev_impressions * 100) if prev_impressions > 0 else 0
    
    # 4. Save site summary
    site_data = {
        "site_url": site_url,
        "date": end_date,
        "clicks": total_clicks,
        "impressions": total_impressions,
        "position": round(avg_position, 2),
        "ctr": round(avg_ctr, 4),
        "clicks_change": round(clicks_change, 1),
        "impressions_change": round(impressions_change, 1)
    }
    save_to_supabase('traffic_sites', [site_data])
    
    return total_clicks, total_impressions

def main():
    print("🚀 GSC Traffic Monitor")
    print("=" * 50)
    
    # Период: последние 30 дней (GSC имеет задержку 3 дня)
    end_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=33)).strftime('%Y-%m-%d')
    
    print(f"📅 Период: {start_date} — {end_date}")
    print()
    
    service = get_gsc_service()
    sites = get_sites(service)
    
    print(f"🌐 Найдено сайтов: {len(sites)}")
    print()
    
    total_clicks = 0
    total_impressions = 0
    
    for i, site in enumerate(sites, 1):
        print(f"[{i}/{len(sites)}] {site}")
        try:
            clicks, impressions = process_site(service, site, start_date, end_date)
            total_clicks += clicks
            total_impressions += impressions
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()
    
    print("=" * 50)
    print(f"✅ Готово!")
    print(f"📊 Всего: {total_clicks:,} кликов, {total_impressions:,} показов")

if __name__ == "__main__":
    main()

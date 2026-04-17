-- Таблица ежедневных данных
CREATE TABLE IF NOT EXISTS traffic_daily (
    id SERIAL PRIMARY KEY,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    position DECIMAL(5,2),
    ctr DECIMAL(6,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(site_url, date)
);

-- Таблица сводки по сайтам
CREATE TABLE IF NOT EXISTS traffic_sites (
    id SERIAL PRIMARY KEY,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    position DECIMAL(5,2),
    ctr DECIMAL(6,4),
    clicks_change DECIMAL(6,1),
    impressions_change DECIMAL(6,1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(site_url, date)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_traffic_daily_site ON traffic_daily(site_url);
CREATE INDEX IF NOT EXISTS idx_traffic_daily_date ON traffic_daily(date);
CREATE INDEX IF NOT EXISTS idx_traffic_sites_clicks ON traffic_sites(clicks DESC);

-- RLS политики (разрешить чтение и запись)
ALTER TABLE traffic_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE traffic_sites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for traffic_daily" ON traffic_daily FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for traffic_sites" ON traffic_sites FOR ALL USING (true) WITH CHECK (true);

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

-- Сводка по сайтам (по периодам)
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

-- Ключевые слова (top-500 за период)
CREATE TABLE IF NOT EXISTS traffic_keywords (
    id SERIAL PRIMARY KEY,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    query TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    position DECIMAL(5,2),
    ctr DECIMAL(6,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(site_url, query, date)
);

-- Гео (страны за период)
CREATE TABLE IF NOT EXISTS traffic_geo (
    id SERIAL PRIMARY KEY,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    country TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    position DECIMAL(5,2),
    ctr DECIMAL(6,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(site_url, country, date)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_daily_site_date ON traffic_daily(site_url, date);
CREATE INDEX IF NOT EXISTS idx_sites_date ON traffic_sites(date DESC);
CREATE INDEX IF NOT EXISTS idx_sites_clicks ON traffic_sites(clicks DESC);
CREATE INDEX IF NOT EXISTS idx_keywords_site_date ON traffic_keywords(site_url, date, clicks DESC);
CREATE INDEX IF NOT EXISTS idx_geo_site_date ON traffic_geo(site_url, date, clicks DESC);

-- RLS
ALTER TABLE traffic_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE traffic_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE traffic_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE traffic_geo ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Allow all" ON traffic_daily FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "Allow all" ON traffic_sites FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "Allow all" ON traffic_keywords FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "Allow all" ON traffic_geo FOR ALL USING (true) WITH CHECK (true);

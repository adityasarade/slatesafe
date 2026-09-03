CREATE DATABASE IF NOT EXISTS slatesafe;

CREATE TABLE IF NOT EXISTS slatesafe.clearance_events (
  asset_id String,
  category LowCardinality(String),
  territories Array(String),
  expires_at Date,
  release_date Date,
  evidence_url String,
  ingested_at DateTime DEFAULT now()
) ENGINE = MergeTree
ORDER BY (asset_id, expires_at);

INSERT INTO slatesafe.clearance_events
  (asset_id, category, territories, expires_at, release_date, evidence_url)
VALUES
  ('MUSIC-NEON-07', 'music', ['IN', 'US'], '2026-12-31', '2026-09-01', 'fictional://music-neon-07'),
  ('LOGO-COLA-22', 'brand', ['US'], '2026-08-31', '2026-09-01', 'fictional://logo-cola-22'),
  ('ART-POSTER-11', 'artwork', ['IN', 'US'], '2027-01-31', '2026-09-01', 'fictional://art-poster-11');

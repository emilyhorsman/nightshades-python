DROP SCHEMA IF EXISTS nightshades CASCADE;
CREATE SCHEMA nightshades;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE nightshades.users (
  id   bigserial PRIMARY KEY,
  name varchar(255)
);

CREATE TABLE nightshades.units (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     integer REFERENCES nightshades.users(id),
  completed   boolean DEFAULT FALSE NOT NULL,
  start_time  timestamp with time zone NOT NULL DEFAULT NOW(),
  expiry_time timestamp with time zone NOT NULL
);

CREATE TABLE nightshades.unit_tags (
  unit_id uuid REFERENCES nightshades.units(id),
  string  varchar(40) NOT NULL
);

INSERT INTO nightshades.users (name) VALUES ('Emily Horsman');

INSERT INTO nightshades.units (user_id, completed, start_time, expiry_time) VALUES
  (
    (SELECT id FROM nightshades.users LIMIT 1),
    TRUE,
    '2016-01-20 09:05:10 America/Toronto',
    timestamp '2016-01-20 09:05:10 America/Toronto' + interval '25 minutes'
  ),
  (
    (SELECT id FROM nightshades.users LIMIT 1),
    TRUE,
    NOW() - interval '30 minutes',
    NOW() - interval '5 minutes'
  ),
  (
    (SELECT id FROM nightshades.users LIMIT 1),
    FALSE,
    NOW(),
    NOW() + interval '25 minutes'
  )
;

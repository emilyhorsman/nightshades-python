CREATE TABLE nightshades.user_login_providers (
  user_id          uuid REFERENCES nightshades.users(id),
  provider         text NOT NULL CHECK (TRIM(provider) <> ''),
  provider_user_id text NOT NULL CHECK (TRIM(provider_user_id) <> ''),
  created_at       timestamp with time zone NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX unique_provider ON nightshades.user_login_providers(provider, provider_user_id);

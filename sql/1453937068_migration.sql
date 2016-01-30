CREATE TABLE nightshades.user_login_providers (
  user_id          uuid REFERENCES nightshades.users(id),
  provider         text NOT NULL,
  provider_user_id text NOT NULL,
  created_at       timestamp with time zone NOT NULL DEFAULT NOW()
);

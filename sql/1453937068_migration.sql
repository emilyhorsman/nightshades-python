CREATE TABLE nightshades.user_login_providers (
  user_id          uuid REFERENCES nightshades.users(id),
  provider         varchar(16) NOT NULL,
  provider_user_id varchar(255) NOT NULL,
  created_at       timestamp with time zone NOT NULL DEFAULT NOW()
);

# api/settings.py
from __future__ import annotations

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------
    # API / Logging
    # ---------------------------
    api_version: str = "1.0.0"
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL"),
    )
    log_sensitive: bool = Field(
        default=False,
        validation_alias=AliasChoices("LOG_SENSITIVE"),
    )

    # ---------------------------
    # Auth (API key service-to-service)
    # ---------------------------
    plum_id_api_key: str = Field(
        default="MON_SUPER_TOKEN",
        validation_alias=AliasChoices("PLUMID_API_KEY"),
        description="Bearer token pour appels service-to-service",
    )

    # ---------------------------
    # Auth (comptes + JWT)
    # ---------------------------
    auth_secret: str = Field(
        default="PLEASE_CHANGE_ME",
        validation_alias=AliasChoices("AUTH_SECRET", "JWT_SECRET"),
        description="Secret HS256 pour signer les tokens d'accès",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES"),
        description="Durée (minutes) du token d'accès",
    )

    # ---------------------------
    # CORS (dev: * / prod: domaines)
    # ---------------------------
    cors_allow_origins: str = Field(
        default="*",
        validation_alias=AliasChoices("CORS_ALLOW_ORIGINS"),
        description="CSV de domaines autorisés, ex: https://exemple.com,https://studio.local",
    )

    # ---------------------------
    # DB (PostgreSQL) — 2 modes :
    # 1) DATABASE_URL (recommandé, fourni automatiquement par Railway PostgreSQL)
    #    ex: postgresql+psycopg2://user:pass@host:5432/db
    # 2) Construction à partir des champs ci-dessous si DATABASE_URL vide
    # ---------------------------
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_URL"),
    )

    ip_db: str = Field(
        default="localhost",
        validation_alias=AliasChoices("IP_DB", "DB_HOST", "PGHOST"),
    )
    port_db: str = Field(
        default="5432",
        validation_alias=AliasChoices("PORT_DB", "DB_PORT", "PGPORT"),
    )
    user_db: str = Field(
        default="plumid_app",
        validation_alias=AliasChoices("USER_DB", "DB_USER", "PGUSER"),
    )
    password_db: str = Field(
        default="AppUser123!",
        validation_alias=AliasChoices("MDP_DB", "DB_PASSWORD", "PGPASSWORD"),
    )
    name_db: str = Field(
        default="plumid",
        validation_alias=AliasChoices("NAME_DB", "DB_NAME", "PGDATABASE"),
    )

    # Pool & SSL (optionnels)
    db_pool_size: int = Field(
        default=5,
        validation_alias=AliasChoices("DB_POOL_SIZE"),
    )
    db_max_overflow: int = Field(
        default=10,
        validation_alias=AliasChoices("DB_MAX_OVERFLOW"),
    )
    db_sslmode: str = Field(
        default="",
        validation_alias=AliasChoices("DB_SSLMODE", "PGSSLMODE"),
        description="PostgreSQL sslmode (ex: 'require', 'disable', 'verify-full')",
    )

    # ---------------------------
    # Model service (microservice de prétraitement / inférence)
    # ---------------------------
    model_service_url: str = Field(
        default="",
        validation_alias=AliasChoices("MODEL_SERVICE_URL"),
        description="URL du service modèle (ex: http://plumid-model:8001)",
    )
    model_service_timeout: float = Field(
        default=30.0,
        validation_alias=AliasChoices("MODEL_SERVICE_TIMEOUT"),
        description="Timeout (secondes) pour les appels au service modèle",
    )

    # ---------------------------
    # SMTP / Email (vérification d'email)
    # ---------------------------
    smtp_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("SMTP_HOST"),
        description="Hôte SMTP pour l'envoi des emails",
    )
    smtp_port: int = Field(
        default=25,
        validation_alias=AliasChoices("SMTP_PORT"),
        description="Port SMTP",
    )
    smtp_user: str = Field(
        default="",
        validation_alias=AliasChoices("SMTP_USER"),
        description="Utilisateur SMTP (optionnel)",
    )
    smtp_password: str = Field(
        default="",
        validation_alias=AliasChoices("SMTP_PASSWORD"),
        description="Mot de passe SMTP (optionnel)",
    )
    smtp_from: str = Field(
        default="no-reply@plumid.local",
        validation_alias=AliasChoices("SMTP_FROM"),
        description="Adresse d'expéditeur pour les emails sortants",
    )

    # ---------------------------
    # Frontend (pour les liens de vérification d'email, reset password, etc.)
    # ---------------------------
    frontend_base_url: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("FRONTEND_BASE_URL"),
        description="URL de base du frontend pour construire les liens (ex: vérification d'email)",
    )

    # ---------------------------
    # pydantic-settings v2
    # ---------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        protected_namespaces=("settings_",),
    )

    # --- Anti-abuse / Rate limit ---
    rl_default_per_min: int = Field(60, validation_alias=AliasChoices("RL_DEFAULT_PER_MIN"))
    rl_burst: int = Field(120, validation_alias=AliasChoices("RL_BURST"))
    rl_login_per_min: int = Field(10, validation_alias=AliasChoices("RL_LOGIN_PER_MIN"))
    rl_window_seconds: int = Field(60, validation_alias=AliasChoices("RL_WINDOW_SECONDS"))

    # --- Signature / Anti-replay ---
    app_hmac_secret: str = Field(
        default="CHANGE_ME_SUPER_SECRET",
        validation_alias=AliasChoices("APP_HMAC_SECRET"),
        description="Clé HMAC partagée avec l'app mobile",
    )
    max_clock_skew_sec: int = Field(300, validation_alias=AliasChoices("MAX_CLOCK_SKEW_SEC"))
    anti_replay_ttl_sec: int = Field(600, validation_alias=AliasChoices("ANTI_REPLAY_TTL_SEC"))

    # --- Body cap ---
    max_request_body_bytes: int = Field(
        5_000_000,
        validation_alias=AliasChoices("MAX_REQUEST_BODY_BYTES"),
    )  # 5MB

    # ---------------------------
    # Helpers
    # ---------------------------
    @property
    def cors_origins(self) -> list[str]:
        raw = (self.cors_allow_origins or "").strip()
        if not raw or raw == "*":
            # "*" -> on laisse FastAPI gérer comme origines ouvertes
            return ["*"]
        return [s.strip() for s in raw.split(",") if s.strip()]

    @property
    def postgres_dsn(self) -> str:
        """
        Construit un DSN PostgreSQL avec psycopg2 à partir des champs unitaires.
        """
        base = (
            f"postgresql+psycopg2://{self.user_db}:{self.password_db}"
            f"@{self.ip_db}:{self.port_db}/{self.name_db}"
        )
        if self.db_sslmode:
            base += f"?sslmode={self.db_sslmode}"
        return base

    @property
    def db_url(self) -> str:
        """
        Privilégie DATABASE_URL si fourni (Railway le fait automatiquement),
        sinon construit un DSN PostgreSQL complet.

        Note : Railway / Heroku donnent souvent une URL de la forme
        `postgres://...`. SQLAlchemy 2.x exige `postgresql+psycopg2://...`.
        On normalise le préfixe ici.
        """
        url = self.database_url.strip()
        if not url:
            return self.postgres_dsn
        # Normalisation Railway / Heroku
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and "+psycopg2" not in url and "+psycopg" not in url:
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url


settings = Settings()

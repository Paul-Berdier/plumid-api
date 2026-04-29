-- =====================================================================
-- PlumID — PostgreSQL bootstrap script
-- ---------------------------------------------------------------------
-- This file is mounted into the official `postgres` image at
--   /docker-entrypoint-initdb.d/01-schema.sql
-- and executed automatically on the FIRST boot of an empty data volume.
-- It runs as the POSTGRES_USER superuser inside the database
-- POSTGRES_DB (both set via environment variables).
--
-- Source of truth: SQL_migration_DB.sql
-- =====================================================================

-- =========================
-- 1. TABLES
-- =========================

CREATE TABLE IF NOT EXISTS species (
    idspecies SERIAL PRIMARY KEY,
    sex CHAR(1),
    region VARCHAR(100),
    environment VARCHAR(100),
    information TEXT,
    species_name VARCHAR(100) UNIQUE,
    species_url_picture TEXT
);

CREATE TABLE IF NOT EXISTS feathers (
    idfeathers SERIAL PRIMARY KEY,
    side VARCHAR(45),
    type VARCHAR(45),
    body_zone VARCHAR(45),
    species_id INT,
    CONSTRAINT fk_feathers_species
        FOREIGN KEY (species_id)
        REFERENCES species(idspecies)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pictures (
    idpictures SERIAL PRIMARY KEY,
    url TEXT,
    longitude NUMERIC(9,6),
    latitude NUMERIC(9,6),
    date_collected DATE,
    feathers_id INT,
    CONSTRAINT fk_pictures_feathers
        FOREIGN KEY (feathers_id)
        REFERENCES feathers(idfeathers)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    idusers SERIAL PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    mail VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified_at TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    pictures_id INT,
    CONSTRAINT fk_users_pictures
        FOREIGN KEY (pictures_id)
        REFERENCES pictures(idpictures)
        ON DELETE SET NULL,
    CONSTRAINT chk_is_active CHECK (is_active IN (TRUE, FALSE))
);

-- =========================
-- 2. INDEXES
-- =========================

CREATE INDEX IF NOT EXISTS idx_feathers_species  ON feathers(species_id);
CREATE INDEX IF NOT EXISTS idx_pictures_feathers ON pictures(feathers_id);

-- =========================
-- 3. ROLES (idempotent)
-- ---------------------------------------------------------------------
-- The image bootstrap creates a primary superuser via POSTGRES_USER /
-- POSTGRES_PASSWORD; the API connects with one of the roles below
-- (typically `plumid_app`). Default passwords are placeholders — they
-- can be overridden by environment variables read in the wrapper script.
-- =========================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'db_admin') THEN
        CREATE ROLE db_admin LOGIN PASSWORD 'AdminFort!';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'plumid_app') THEN
        CREATE ROLE plumid_app LOGIN PASSWORD 'AppUser123!';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'plumid_editor') THEN
        CREATE ROLE plumid_editor LOGIN PASSWORD 'Editor123!';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'plumid_viewer') THEN
        CREATE ROLE plumid_viewer LOGIN PASSWORD 'Viewer123!';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'plumid_ia') THEN
        CREATE ROLE plumid_ia LOGIN PASSWORD 'IAuser123!';
    END IF;
END$$;

-- Grant minimum privileges per role
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO db_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO db_admin;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO plumid_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO plumid_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON species  TO plumid_editor;
GRANT SELECT, INSERT, UPDATE, DELETE ON feathers TO plumid_editor;
GRANT SELECT, INSERT, UPDATE, DELETE ON pictures TO plumid_editor;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO plumid_editor;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO plumid_viewer;

GRANT SELECT ON species  TO plumid_ia;
GRANT SELECT ON pictures TO plumid_ia;

-- Default privileges for future tables created by superuser
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO plumid_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO plumid_viewer;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO plumid_app;

-- =========================
-- 4. SEED DATA (species)
-- ---------------------------------------------------------------------
-- ON CONFLICT (species_name) DO NOTHING makes the seed idempotent so the
-- script can safely be re-run.
-- =========================

INSERT INTO species (region, environment, information, species_name, species_url_picture) VALUES
('Europe', 'Forêts, zones urbaines', 'La Pie bavarde (Pica pica) est une espèce de passereaux de la famille des Corvidae, et l''une des espèces de corvidés parmi les plus répandues en Europe et dans une grande partie de l''Asie. Les pies peuvent aisément être identifiées grâce à leur morphologie et à leur plumage noir et blanc caractéristique. Il existe 13 sous-espèces de pie bavarde.', 'Pie bavarde (Pica pica)', NULL),

('Europe', 'Forêts', 'Le Pic épeiche (Dendrocopos major) est l''espèce de pics la plus répandue et la plus commune en Europe et dans le Nord de l''Asie. Faisant partie des pics de taille moyenne, il se caractérise par un plumage rayé de blanc et de noir et une tache rouge écarlate sur le bas-ventre près de la queue. Espèce diurne, le Pic épeiche vit solitaire ou par couple dans un territoire dont il ne s''éloigne guère, même en hiver, les mâles étant les plus sédentaires. Il peut adopter un comportement plus erratique et migrer en hiver lorsque la nourriture se raréfie.', 'Pic épeiche (Dendrocopos major)', NULL),

('Europe, Asie (introduite en Europe)', 'Zones urbaines, parcs', 'La Perruche à collier (Psittacula krameri) est une espèce de grandes perruches originaire d''Asie et d''Afrique et aujourd''hui naturalisée en Europe de l''Ouest. Elle est souvent élevée en captivité comme animal de compagnie. Elle est considérée comme l''un des oiseaux parleurs les plus habiles. Elle est d''ailleurs bien connue en Europe depuis l''Antiquité et le Moyen Âge, où elle fait partie des plus anciens oiseaux de compagnie, comme sa cousine la Perruche alexandre. Elle est souvent représentée dans l''art européen, depuis les mosaïques romaines jusqu''aux peintures de la Renaissance en passant par les enluminures médiévales.', 'Perruche à collier (Psittacula krameri)', NULL),

('Europe', 'Forêts, parcs', 'Le Geai des chênes (Garrulus glandarius) est un oiseau de la famille des Corvidae facilement reconnaissable à son plumage brun rosé, ses ailes ornées de plumes bleu vif barrées de noir et sa moustache noire. Très vif et méfiant, il est connu pour ses cris rauques et ses talents d''imitateur, capables de reproduire les appels d''autres oiseaux ou même certains bruits environnants. Principalement forestier, il fréquente aussi les parcs et jardins arborés. Son nom provient de son comportement caractéristique : il collecte et cache des glands en grande quantité pour constituer des réserves alimentaires, jouant ainsi un rôle important dans la dispersion des chênes. Omnivore, il se nourrit également d''insectes, de fruits, de graines et parfois d''œufs ou de petits animaux.', 'Geai des chênes (Garrulus glandarius)', NULL),

('Europe', 'Zones urbaines, campagnes', 'La Corneille noire (Corvus corone) est une espèce de passereaux de la famille des Corvidae. Elle est présente dans deux aires distinctes de l''écozone paléarctique : l''Europe de l''Ouest et du Sud-Ouest, où sa population est estimée entre 5,5 et 12 millions de couples, et en Asie du Kazakhstan au Japon, où sa population n''est pas connue. Un des oiseaux les plus communs dans son aire de répartition, elle se trouve à peu près partout, de la campagne jusqu''au cœur des grandes villes.', 'Corneille noire (Corvus corone)', NULL),

('Europe, Asie, Amérique du Nord', 'Zones humides, étangs, rivières', 'Le Canard colvert, col-vert (Anas platyrhynchos), ou Canard malard au Canada, est une espèce d''oiseaux de l''ordre des Ansériformes, de la famille des Anatidae et de la sous-famille des Anatinae. C''est certainement le plus connu et reconnaissable de tous les canards, du fait de l''existence de races de canards domestiques issues de cette espèce.', 'Canard colvert (Anas platyrhynchos)', NULL)
ON CONFLICT (species_name) DO NOTHING;

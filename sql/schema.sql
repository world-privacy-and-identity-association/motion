DROP TABLE IF EXISTS voter;
CREATE TABLE voter (id serial NOT NULL,
                   email VARCHAR(255) NOT NULL,
                   host VARCHAR(500) NOT NULL,
                   PRIMARY KEY(id));


DROP TABLE IF EXISTS motion;
CREATE TABLE motion (id serial NOT NULL,
                   identifier VARCHAR(20) NOT NULL,
                   name VARCHAR(250) NOT NULL,
                   type VARCHAR(250) NOT NULL,
                   host VARCHAR(500) NOT NULL,
                   content text NOT NULL,
                   posed timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                   posed_by int NOT NULL,
                   deadline timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP + interval '3 days'),
                   canceled timestamp NULL DEFAULT NULL,
                   cancelation_reason text NULL DEFAULT NULL,
                   canceled_by int NULL DEFAULT NULL,
                   PRIMARY KEY(id));
CREATE UNIQUE INDEX motion_ident ON motion (identifier);

DROP TABLE IF EXISTS vote;
DROP TYPE IF EXISTS "vote_type";
CREATE TYPE "vote_type" AS ENUM ('yes', 'no', 'abstain');
CREATE TABLE vote (motion_id INTEGER NOT NULL,
                 voter_id INTEGER NOT NULL,
                 result vote_type NOT NULL,
                 entered timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                 proxy_id INTEGER NOT NULL,
                 PRIMARY KEY(motion_id, voter_id));

DROP TABLE IF EXISTS proxy;
CREATE TABLE proxy (id serial NOT NULL,
                   voter_id INTEGER NOT NULL,
                   proxy_id INTEGER NOT NULL,
                   granted timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                   granted_by int NOT NULL,
                   revoked timestamp NULL DEFAULT NULL,
                   revoked_by int NULL DEFAULT NULL,
                   PRIMARY KEY(id));
CREATE INDEX proxy_voter ON proxy (voter_id);
CREATE INDEX proxy_proxy ON proxy (proxy_id);

DROP TABLE IF EXISTS adminlog;
DROP TYPE IF EXISTS "admin_log";
CREATE TYPE "admin_log" AS ENUM ('motionmasking', 'proxygranted', 'proxyrevoked', 'proxyrevokedall');
CREATE TABLE adminlog (id serial NOT NULL,
                   user_id INTEGER NOT NULL,
                   action admin_log NOT NULL,
                   comment text NULL,
                   action_user_id INTEGER NOT NULL,
                   actiontime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                   PRIMARY KEY(id));

DROP TABLE IF EXISTS schema_version;
CREATE TABLE schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version(version) VALUES(7);

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

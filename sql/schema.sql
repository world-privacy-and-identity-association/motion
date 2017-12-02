DROP TABLE IF EXISTS voter;
CREATE TABLE voter (id serial NOT NULL, email VARCHAR(255) NOT NULL, PRIMARY KEY(id));


DROP TABLE IF EXISTS motion;
CREATE TABLE motion (id serial NOT NULL,
                   name VARCHAR(250) NOT NULL,
                   type VARCHAR(250) NOT NULL,
                   content text NOT NULL,
                   posed timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                   posed_by int NOT NULL,
                   deadline timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP + interval '3 days'),
                   canceled timestamp NULL DEFAULT NULL,
                   cancelation_reason text NULL DEFAULT NULL,
                   canceled_by int NULL DEFAULT NULL,
                   PRIMARY KEY(id));


DROP TABLE IF EXISTS vote;
DROP TYPE IF EXISTS "vote_type";
CREATE TYPE "vote_type" AS ENUM ('yes', 'no', 'abstain');
CREATE TABLE vote (motion_id INTEGER NOT NULL,
                 voter_id INTEGER NOT NULL,
                 result vote_type NOT NULL,
                 entered timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                 PRIMARY KEY(motion_id, voter_id));

DROP TABLE IF EXISTS schema_version;
CREATE TABLE schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version(version) VALUES(1);

DROP TABLE IF EXISTS voter;
CREATE TABLE voter (id serial NOT NULL, name VARCHAR(10) NOT NULL, PRIMARY KEY(id));


DROP TABLE IF EXISTS motion;
CREATE TABLE motion (id serial NOT NULL,
                   name VARCHAR(250) NOT NULL,
                   content text NOT NULL,
                   posed timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                   deadline timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP + interval '3 days'),
                   PRIMARY KEY(id));

DROP TABLE IF EXISTS vote;
DROP TYPE IF EXISTS "vote_type";
CREATE TYPE "vote_type" AS ENUM ('yes', 'no', 'abstain');
CREATE TABLE vote (motion_id INTEGER NOT NULL,
                 voter_id INTEGER NOT NULL,
                 result vote_type NOT NULL,
                 entered timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                 PRIMARY KEY(motion_id, voter_id));

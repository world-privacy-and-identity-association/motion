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

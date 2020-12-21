# Installation
Requires Python 3 and a running PostgreSQL installation.

For a productive environment use a nginx webserver.

To install:
```
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt
```
Then edit config.py.example into config.py with your database connection and web site settings

## Development and debug

To debug-run linux:
```
LANG=C.UTF-8 FLASK_DEBUG=1 FLASK_APP=motion.py flask run
```

To debug-run windows:
```
set LANG=C.UTF-8
set FLASK_DEBUG=1
set FLASK_APP=motion.py
flask run
```

For unit testing use config values from config.py.example:
```
python -m unittest tests/test_motion.py
```

The database schema is automatically installed when the table "schema_version" does not exist and the application is started.

The following user rights can be granted:
- create: user is able to create a new motion
- vote: user is able to vote running motions
- cancel: user is able to cancel a running motion
- finish: user is able to close a running motion
- audit: user is able to see given votes of a finished motion
- proxyadmin: user is able to grant proxy rights for users

To grant right use the following (here with vote right as example):
- on all groups add "vote:*"
- on one given group add "vote:group1"
- on two given groups add "vote:group1 vote:group2"

# Usage

Within the motion content markdown can be used for formatting e.g. 
* To add a line break add two lines
* to enter a link use `[text](https://domain.tld/link)`

## Settings for nginx

To control the access this map is used:

```
map "$host:$ssl_client_serial:$ssl_client_i_dn" $motion_user_role {
"host.domain.tld:serialnumber:/issuername" 'username/create:* vote:* cancel:* audit:*';
...
default "<invalid>/";
}
```

example taken from motions.board.wpia.club:
```
map "$host:$ssl_client_serial:$ssl_client_i_dn" $motion_user_role {
"motions.board.wpia.club:0a0000000a1234567890abcdef1234567890abcde:/CN=Orga 2019-2/O=TC InterimCA/OU=TC InterimCAs/C=AT" 'president/create:* vote:* cancel:* audit:*';
...
default "<invalid>/";
}
```


## configuration
```
listen 0.0.0.0:443 ssl;
listen [::]:443 ssl;
server_name host.domain.tld;
gzip on;
ssl_certificate /etc/ssl/private/host.domain.tld.crt;
ssl_certificate_key /etc/ssl/private/host.domain.tld.key;

ssl_client_certificate /etc/ssl/host.domain.tld.pem;
ssl_verify_client on;
ssl_verify_depth 4;
access_log /tmp/host.domain.tld.log motion-cert;

location / {
fastcgi_param QUERY_STRING $query_string;
fastcgi_param REQUEST_METHOD $request_method;
fastcgi_param CONTENT_TYPE $content_type;
fastcgi_param CONTENT_LENGTH $content_length;
fastcgi_param REQUEST_URI $request_uri;
fastcgi_param PATH_INFO $document_uri;
fastcgi_param REMOTE_ADDR $remote_addr;
fastcgi_param REMOTE_PORT $remote_port;
fastcgi_param SERVER_NAME $host;
fastcgi_param SERVER_PORT '443';
fastcgi_param SERVER_PROTOCOL 'https';
fastcgi_param USER_ROLES $motion_user_role;
fastcgi_pass unix:/motion-socket/motion.fcgi;
}
```

# Configuration for a Jenkins Freestyle Project

## Preconditions for Jenkins system

* Python 3 installed with:

  python3 virtualenv python3-pip

* PostgreSQL server installed with motion database and database user


## Add freestyle project

### Source-Code-Management

Adjust Git settings

### Build Environment

Add Bindings

Add Username and password (separated)

Enter username (DB_USER) and password (DB_PW) according to database credentials

### Build

Add build step shell

Add the command

```
rm -rf env
virtualenv -p python3 env
. env/bin/activate
pip3 install -r requirements.txt


cat > config.py << EOF
DATABASE="pq://IP-ADDRESS/motion"
USER="${DB_USER}"
PASSWORD="${DB_PW}"
EOF

python3 jenkins_job.py
```

If an IPv6 address is used the following needs to be added to the script to fix a bug of the IPv6 literal translation:
(https://github.com/python-postgres/fe/issues/104)

```
patch env/lib/python3*/site-packages/postgresql/versionstring.py <<EOF
diff --git a/postgresql/versionstring.py b/postgresql/versionstring.py
index ccb3953..2503013 100644
--- a/postgresql/versionstring.py
+++ b/postgresql/versionstring.py
@@ -15,7 +15,7 @@ def split(vstr : str) -> (
    Split a PostgreSQL version string into a tuple
    (major,minor,patch,...,state_class,state_level)
    """
-   v = vstr.strip().split('.')
+   v = vstr.strip().split(' ')[0].split('.')
 
    # Get rid of the numbers around the state_class (beta,a,dev,alpha, etc)
    state_class = v[-1].strip('0123456789')
EOF
```

### Post build actions

Add Publish JUnit test result report - test report XMLs

```
python_tests_xml/*
```

## Add user via command line

For linux start with
```
FLASK_APP=motion.py
```

For windows start with
```
set FLASK_APP=motion.py

```

To add a user use this command
```
flask create-user "email address" "host"

```

The application will return a message for success.

To mask motions use this command
```
flask motion_masking motionidentifier motionurl host"

```

where:

* motionidentifier - the motion identifier or left part of it which should be cleaned
* motionurl - an url to a motion that is the reason for the cleanup
* host - host where the motions are located

The application will return a message for success.

# Installation
Requires Python 3 and a running PostgreSQL installation.

For a productive environment use a nginx webserver.

To install:
```
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt
```
Then edit config.py.example into config.py with your database connection

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

# Usage

Within the motion content markdown can be used for formatting e.g. 
* To add a line break add two lines
* to enter a link use `[text](https//domain.tld/link)`

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

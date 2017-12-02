# Installation
Requires 3.
To install:
```
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt
```
Then edit config.py.example into config.py with your database connection

To debug-run:
```
LANG=C.UTF-8 FLASK_DEBUG=1 FLASK_APP=motion.py flask run
```

The database schema is automatically installed when the table "schema_version" does not exist and the application is started.

# Installation
Requires 3.
To install:
```
virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt
```
Then edit config.py.example into config.py with your database connection

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

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

To install database schema, run in an interactive python shell (`python`):
```
import motion
motion.init_db()
```

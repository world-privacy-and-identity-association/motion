from flask import g
from flask import Flask
from flask import render_template, redirect
from flask import request
import postgresql
import filters

times=[3,5,14]

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = postgresql.open(app.config.get("DATABASE"), user=app.config.get("USER"), password=app.config.get("PASSWORD"))
    #db.row_factory = sqlite3.Row
    return db

app = Flask(__name__)
app.register_blueprint(filters.blueprint)

# Load config
app.config.from_pyfile('config.py')

prefix=app.config.get("GROUP_PREFIX")

@app.before_request
def lookup_user():
    global prefix

    env = request.environ
    user = None
    if "USER_ROLES" in env:
        parts = env.get("USER_ROLES").split("/", 1)
        user = parts[0]
        roles = parts[1]

    if "USER" in env and "ROLES" in env:
        user = env.get("USER")
        roles = env.get("ROLES")

    if user is None:
        return "Server misconfigured", 500
    roles = roles.split(" ")

    if user == "<invalid>":
        return "Access denied", 403;

    db = get_db()
    with db.xact():
        rv = db.prepare("SELECT id FROM voter WHERE email=$1")(user)
        if len(rv) == 0:
            db.prepare("INSERT INTO voter(\"email\") VALUES($1)")(user)
            rv = db.prepare("SELECT id FROM voter WHERE email=$1")(user)
        g.voter = rv[0].get("id");
    g.user = user
    g.roles = {}

    for r in roles:
        a = r.split(":", 1)
        val = a[1]
        if a[0] not in g.roles:
            g.roles[a[0]] = []
        if val == "*":
            g.roles[a[0]] = [group for group in prefix[request.host]]
        else:
            g.roles[a[0]].append(val)
    return None

def get_allowed_cats(action):
    return g.roles.get(action, []);

def may(action, motion):
    return motion in get_allowed_cats(action)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        try:
            ver = db.prepare("SELECT version FROM schema_version")()[0][0];
            print("Database Schema version: ", ver)
        except postgresql.exceptions.UndefinedTableError:
            ver = 0

        if ver < 1:
            with app.open_resource('sql/schema.sql', mode='r') as f:
                db.execute(f.read())
            return

        if ver < 2:
            with app.open_resource('sql/from_1.sql', mode='r') as f:
                db.execute(f.read())
                ct={}
                for g in [group for group in prefix[app.config.get("DEFAULT_HOST")]]:
                    ct[g] = {"dt": "", "c": 0}

                p = db.prepare("UPDATE \"motion\" SET \"identifier\"=$1 WHERE \"id\"=$2")
                for row in db.prepare("SELECT id, \"type\", \"posed\" FROM \"motion\" ORDER BY \"id\" ASC"):
                    dt=row[2].strftime("%Y%m%d")
                    if ct[row[1]]["dt"] != dt:
                        ct[row[1]]["dt"] = dt
                        ct[row[1]]["c"] = 0
                    ct[row[1]]["c"] = ct[row[1]]["c"] + 1
                    name=prefix[app.config.get("DEFAULT_HOST")][row[1]]+"."+dt+"."+("%03d" % ct[row[1]]["c"])
                    p(name, row[0])
                db.prepare("ALTER TABLE \"motion\" ALTER COLUMN \"identifier\" SET NOT NULL")()
                db.prepare("UPDATE \"schema_version\" SET \"version\"=2")()
                db.prepare("CREATE UNIQUE INDEX motion_ident ON motion (identifier)")()

        if ver < 3:
            with app.open_resource('sql/from_2.sql', mode='r') as f:
                db.execute(f.read())
                db.prepare("UPDATE \"motion\" SET \"host\"=$1")(app.config.get("DEFAULT_HOST"))
                db.prepare("ALTER TABLE \"motion\" ALTER COLUMN \"host\" SET NOT NULL")()
                db.prepare("UPDATE \"schema_version\" SET \"version\"=3")()


init_db()

@app.route("/")
def main():
    start=int(request.args.get("start", "-1"));
    q = "SELECT motion.*, votes.*, poser.email AS poser, canceler.email AS canceler, (motion.deadline > CURRENT_TIMESTAMP AND canceled is NULL) AS running FROM motion LEFT JOIN (SELECT motion_id, "\
                             + "COUNT(CASE WHEN result='yes' THEN 'yes' ELSE NULL END) as yes, "\
                             + "COUNT(CASE WHEN result='no' THEN 'no' ELSE NULL END) as no, "\
                             + "COUNT(CASE WHEN result='abstain' THEN 'abstain' ELSE NULL END) as abstain "\
                             + "FROM vote GROUP BY motion_id) as votes ON votes.motion_id=motion.id "\
                             + "LEFT JOIN voter poser ON poser.id = motion.posed_by "\
                             + "LEFT JOIN voter canceler ON canceler.id = motion.canceled_by "
    prev=None
    if start == -1:
        p = get_db().prepare(q + "WHERE motion.host = $1 ORDER BY motion.id DESC LIMIT 11")
        rv = p(request.host)
    else:
        p = get_db().prepare(q + "WHERE motion.host = $1 AND motion.id <= $2 ORDER BY motion.id DESC LIMIT 11")
        rv = p(request.host, start)
        rs = get_db().prepare("SELECT id FROM motion WHERE motion.host = $1 AND motion.id > $2 ORDER BY id ASC LIMIT 10")(request.host, start)
        if len(rs) == 10:
            prev = rs[9][0]
        else:
            prev = -1
    return render_template('index.html', motions=rv[:10], more=rv[10]["id"] if len(rv) == 11 else None, times=times, prev=prev,
                           categories=get_allowed_cats("create"))

def rel_redirect(loc):
    r = redirect(loc)
    r.autocorrect_location_header = False
    return r

@app.route("/motion", methods=['POST'])
def put_motion():
    cat=request.form.get("category", "")
    if cat not in get_allowed_cats("create"):
        return "Forbidden", 403
    time = int(request.form.get("days", "3"));
    if time not in times:
        return "Error, invalid length", 500
    db = get_db()
    with db.xact():
        t = db.prepare("SELECT CURRENT_TIMESTAMP")()[0][0];
        s = db.prepare("SELECT MAX(\"identifier\") FROM \"motion\" WHERE \"type\"=$1 AND \"host\"=$2 AND DATE(\"posed\")=DATE(CURRENT_TIMESTAMP)")
        sr = s(cat, request.host)
        ident=""
        if len(sr) == 0 or sr[0][0] is None:
            ident=prefix[request.host][cat]+"."+t.strftime("%Y%m%d")+".001"
        else:
            ident=prefix[request.host][cat]+"."+t.strftime("%Y%m%d")+"."+("%03d" % (int(sr[0][0].split(".")[2])+1))
        p = db.prepare("INSERT INTO motion(\"name\", \"content\", \"deadline\", \"posed_by\", \"type\", \"identifier\", \"host\") VALUES($1, $2, CURRENT_TIMESTAMP + $3 * interval '1 days', $4, $5, $6, $7)")
        p(request.form.get("title", ""), request.form.get("content",""), time, g.voter, cat, ident, request.host)
    return rel_redirect("/")

def motion_edited(motion):
    return rel_redirect("/?start=" + str(motion) + "#motion-" + str(motion))

@app.route("/motion/<string:motion>/cancel", methods=['POST'])
def cancel_motion(motion):
    rv = get_db().prepare("SELECT id, type FROM motion WHERE identifier=$1 AND request.host")(motion, request.host);
    if len(rv) == 0:
        return "Error, Not found", 404
    id = rv[0].get("id")
    if not may("cancel", rv[0].get("type")):
        return "Forbidden", 403
    if request.form.get("reason", "none") == "none":
        return "Error, form requires reason", 500
    rv = get_db().prepare("UPDATE motion SET canceled=CURRENT_TIMESTAMP, cancelation_reason=$1, canceled_by=$2 WHERE identifier=$3 AND host=$4 AND canceled is NULL")(request.form.get("reason", ""), g.voter, motion, request.host)
    return motion_edited(id)

@app.route("/motion/<string:motion>")
def show_motion(motion):
    p = get_db().prepare("SELECT motion.*, poser.email AS poser, canceler.email AS canceler, (motion.deadline > CURRENT_TIMESTAMP AND canceled is NULL) AS running, vote.result FROM motion "\
                         + "LEFT JOIN vote on vote.motion_id=motion.id AND vote.voter_id=$2 "\
                         + "LEFT JOIN voter poser ON poser.id = motion.posed_by "\
                         + "LEFT JOIN voter canceler ON canceler.id = motion.canceled_by "
                         + "WHERE motion.identifier=$1 AND motion.host=$3")
    rv = p(motion, g.voter, request.host)
    votes = None
    if may("audit", rv[0].get("type")) and not rv[0].get("running") and not rv[0].get("canceled"):
        votes = get_db().prepare("SELECT vote.result, voter.email FROM vote INNER JOIN voter ON voter.id = vote.voter_id WHERE vote.motion_id=$1")(rv[0].get("id"));
    return render_template('single_motion.html', motion=rv[0], may_vote=may("vote", rv[0].get("type")), may_cancel=may("cancel", rv[0].get("type")), votes=votes)

@app.route("/motion/<string:motion>/vote", methods=['POST'])
def vote(motion):
    v = request.form.get("vote", "abstain")
    db = get_db()
    with db.xact():
        rv = db.prepare("SELECT id, type FROM motion WHERE identifier=$1 AND host=$2")(motion, host);
        if len(rv) == 0:
            return "Error, Not found", 404
        if not may("vote", rv[0].get("type")):
            return "Forbidden", 403
        p = db.prepare("SELECT deadline > CURRENT_TIMESTAMP FROM motion WHERE identifier = $1 AND host=$2")
        id = rv[0].get("id")
        if not p(motion, request.host)[0][0]:
            return "Error, motion deadline has passed", 500
        p = db.prepare("SELECT * FROM vote WHERE motion_id = $1 AND voter_id = $2 AND host=$3")
        rv = p(id, g.voter, request.host)
        if len(rv) == 0:
            db.prepare("INSERT INTO vote(motion_id, voter_id, result) VALUES($1,$2,$3)")(id, g.voter, v)
        else:
            db.prepare("UPDATE vote SET result=$3, entered=CURRENT_TIMESTAMP WHERE motion_id=$1 AND voter_id = $2")(id, g.voter, v)
    return motion_edited(id)

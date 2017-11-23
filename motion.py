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

groups=["fellowship", "board"]

@app.before_request
def lookup_user():
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
            g.roles[a[0]] = groups
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
        with app.open_resource('schema.sql', mode='r') as f:
            db.execute(f.read())

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
        p = get_db().prepare(q + "ORDER BY motion.id DESC LIMIT 11")
        rv = p()
    else:
        p = get_db().prepare(q + "WHERE motion.id <= $1 ORDER BY motion.id DESC LIMIT 11")
        rv = p(start)
        rs = get_db().prepare("SELECT id FROM motion WHERE motion.id > $1 ORDER BY id ASC LIMIT 10")(start)
        if len(rs) == 10:
            prev = rs[9][0]
        else:
            prev = -1
    return render_template('index.html', motions=rv[:10], more=rv[10]["id"] if len(rv) == 11 else None, times=times, prev=prev,
                           categories=get_allowed_cats("create"))

@app.route("/motion", methods=['POST'])
def put_motion():
    cat=request.form.get("category", "")
    if cat not in get_allowed_cats("create"):
        return "Forbidden", 403
    time = int(request.form.get("days", "3"));
    if time not in times:
        return "Error, invalid length", 500
    p = get_db().prepare("INSERT INTO motion(\"name\", \"content\", \"deadline\", \"posed_by\", \"type\") VALUES($1, $2, CURRENT_TIMESTAMP + $3 * interval '1 days', $4, $5)")
    p(request.form.get("title", ""), request.form.get("content",""), time, g.voter, cat)
    return redirect("/")

def motion_edited(motion):
    return redirect("/?start=" + str(motion) + "#motion-" + str(motion))

@app.route("/motion/<int:motion>/cancel", methods=['POST'])
def cancel_motion(motion):
    rv = get_db().prepare("SELECT type FROM motion WHERE id=$1")(motion);
    if len(rv) == 0:
        return "Error, Not found", 404
    if not may("cancel", rv[0].get("type")):
        return "Forbidden", 403
    if request.form.get("reason", "none") == "none":
        return "Error, form requires reason", 500
    rv = get_db().prepare("UPDATE motion SET canceled=CURRENT_TIMESTAMP, cancelation_reason=$1, canceled_by=$2 WHERE id=$3 AND canceled is NULL")(request.form.get("reason", ""), g.voter, motion)
    return motion_edited(motion)

@app.route("/motion/<int:motion>")
def show_motion(motion):
    p = get_db().prepare("SELECT motion.*, poser.email AS poser, canceler.email AS canceler, (motion.deadline > CURRENT_TIMESTAMP AND canceled is NULL) AS running, vote.result FROM motion "\
                         + "LEFT JOIN vote on vote.motion_id=motion.id AND vote.voter_id=$2 "\
                         + "LEFT JOIN voter poser ON poser.id = motion.posed_by "\
                         + "LEFT JOIN voter canceler ON canceler.id = motion.canceled_by "
                         + "WHERE motion.id=$1")
    rv = p(motion, g.voter)
    votes = None
    if may("audit", rv[0].get("type")):
        votes = get_db().prepare("SELECT vote.result, voter.email FROM vote INNER JOIN voter ON voter.id = vote.voter_id WHERE vote.motion_id=$1")(motion);
    return render_template('single_motion.html', motion=rv[0], may_vote=may("vote", rv[0].get("type")), may_cancel=may("cancel", rv[0].get("type")), votes=votes)

@app.route("/motion/<int:motion>/vote", methods=['POST'])
def vote(motion):
    v = request.form.get("vote", "abstain")
    db = get_db()
    with db.xact():
        rv = db.prepare("SELECT type FROM motion WHERE id=$1")(motion);
        if len(rv) == 0:
            return "Error, Not found", 404
        if not may("vote", rv[0].get("type")):
            return "Forbidden", 403
        p = db.prepare("SELECT deadline > CURRENT_TIMESTAMP FROM motion WHERE id = $1")
        if not p(motion)[0][0]:
            return "Error, motion deadline has passed", 500
        p = db.prepare("SELECT * FROM vote WHERE motion_id = $1 AND voter_id = $2")
        rv = p(motion, g.voter)
        if len(rv) == 0:
            db.prepare("INSERT INTO vote(motion_id, voter_id, result) VALUES($1,$2,$3)")(motion, g.voter, v)
        else:
            db.prepare("UPDATE vote SET result=$3, entered=CURRENT_TIMESTAMP WHERE motion_id=$1 AND voter_id = $2")(motion, g.voter, v)
    return motion_edited(motion)

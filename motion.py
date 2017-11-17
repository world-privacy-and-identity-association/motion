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
    q = "SELECT motion.*, votes.*, poser.email AS poser, canceler.email AS canceler, (motion.deadline > CURRENT_TIMESTAMP AND canceled is NULL) AS running FROM motion LEFT JOIN (SELECT motion_id, voter_id, "\
                             + "COUNT(CASE WHEN result='yes' THEN 'yes' ELSE NULL END) as yes, "\
                             + "COUNT(CASE WHEN result='no' THEN 'no' ELSE NULL END) as no, "\
                             + "COUNT(CASE WHEN result='abstain' THEN 'abstain' ELSE NULL END) as abstain "\
                             + "FROM vote GROUP BY motion_id, voter_id) as votes ON votes.motion_id=motion.id "\
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
    return render_template('index.html', motions=rv[:10], more=rv[10]["id"] if len(rv) == 11 else None, times=times, prev=prev)

@app.route("/motion", methods=['POST'])
def put_motion():
    time = int(request.form.get("days", "3"));
    if time not in times:
        return "Error, invalid length"
    p = get_db().prepare("INSERT INTO motion(\"name\", \"content\", \"deadline\", \"posed_by\") VALUES($1, $2, CURRENT_TIMESTAMP + $3 * interval '1 days', $4)")
    p(request.form.get("title", ""), request.form.get("content",""), time, voter)
    return redirect("/")

voter=1

def motion_edited(motion):
    return redirect("/?start=" + str(motion) + "#motion-" + str(motion))

@app.route("/motion/<int:id>/cancel", methods=['POST'])
def cancel_motion(id):
    if request.form.get("reason", "none") == "none":
        return "Error, form requires reason"
    rv = get_db().prepare("UPDATE motion SET canceled=CURRENT_TIMESTAMP, cancelation_reason=$1, canceled_by=$2 WHERE id=$3 AND canceled is NULL")(request.form.get("reason", ""), voter, id)
    print(rv)
    return motion_edited(id)

@app.route("/motion/<int:motion>")
def show_motion(motion):
    p = get_db().prepare("SELECT motion.*, poser.email AS poser, canceler.email AS canceler, (motion.deadline > CURRENT_TIMESTAMP AND canceled is NULL) AS running, vote.result FROM motion "\
                         + "LEFT JOIN vote on vote.motion_id=motion.id AND vote.voter_id=$2 "\
                         + "LEFT JOIN voter poser ON poser.id = motion.posed_by "\
                         + "LEFT JOIN voter canceler ON canceler.id = motion.canceled_by "
                         + "WHERE motion.id=$1")
    rv = p(motion,voter)
    if len(rv) == 0:
        return "Error, motion not found" # TODO 404
    return render_template('single_motion.html', motion=rv[0])

@app.route("/motion/<int:motion>/vote", methods=['POST'])
def vote(motion):
    v = request.form.get("vote", "abstain")
    db = get_db()
    with db.xact():
        p = db.prepare("SELECT deadline > CURRENT_TIMESTAMP FROM motion WHERE id = $1")
        if not p(motion)[0][0]:
            return "Error, motion deadline has passed"
        p = db.prepare("SELECT * FROM vote WHERE motion_id = $1 AND voter_id = $2")
        rv = p(motion, voter)
        if len(rv) == 0:
            db.prepare("INSERT INTO vote(motion_id, voter_id, result) VALUES($1,$2,$3)")(motion,voter,v)
        else:
            db.prepare("UPDATE vote SET result=$3, entered=CURRENT_TIMESTAMP WHERE motion_id=$1 AND voter_id = $2")(motion,voter,v)
    return motion_edited(motion)

# TODO authentication/user management

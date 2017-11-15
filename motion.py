from flask import g
from flask import Flask
from flask import render_template, redirect
from flask import request
import postgresql
import config

times=[3,5,14]

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = postgresql.open(config.DATABASE, user=config.USER, password=config.PASSWORD)
    #db.row_factory = sqlite3.Row
    return db

app = Flask(__name__)

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
    q = "SELECT *, motion.deadline > CURRENT_TIMESTAMP AS running FROM motion LEFT JOIN (SELECT motion_id, voter_id, "\
                             + "COUNT(CASE WHEN result='yes' THEN 'yes' ELSE NULL END) as yes, "\
                             + "COUNT(CASE WHEN result='no' THEN 'no' ELSE NULL END) as no, "\
                             + "COUNT(CASE WHEN result='abstain' THEN 'abstain' ELSE NULL END) as abstain "\
                             + "FROM vote GROUP BY motion_id, voter_id) as votes ON votes.motion_id=motion.id "
    if start == -1:
        p = get_db().prepare(q + "ORDER BY id DESC LIMIT 11")
        rv = p()
    else:
        p = get_db().prepare(q + "WHERE id <= $1 ORDER BY id DESC LIMIT 11")
        rv = p(start)
    return render_template('index.html', motions=rv[:10], more=rv[10]["id"] if len(rv) == 11 else None, times=times)

@app.route("/motion", methods=['POST'])
def put_motion():
    time = int(request.form.get("days", "3"));
    if time not in times:
        return "Error, invalid length"
    p = get_db().prepare("INSERT INTO motion(\"name\", \"content\", \"deadline\") VALUES($1, $2, CURRENT_TIMESTAMP + $3 * interval '1 days')")
    p(request.form.get("title", ""), request.form.get("content",""), time)
    return redirect("/")

voter=1

@app.route("/motion/<int:id>")
def show_motion(id):
    p = get_db().prepare("SELECT motion.*, motion.deadline > CURRENT_TIMESTAMP AS running, vote.result FROM motion LEFT JOIN vote on vote.motion_id=motion.id AND vote.voter_id=$2 WHERE id=$1")
    rv = p(id,voter)
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
            db.prepare("INSERT INTO vote (motion_id, voter_id, result) VALUES($1,$2,$3)")(motion,voter,v)
        else:
            db.prepare("UPDATE vote SET result=$3, entered=CURRENT_TIMESTAMP WHERE motion_id=$1 AND voter_id = $2")(motion,voter,v)
    return redirect("/motion/" + str(motion))

# TODO cancel running motion (with comment)
# TODO pagination previous link
# TODO authentication/user management
# TODO crop time at second precision

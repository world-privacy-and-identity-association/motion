from flask import g
from flask import Flask
from flask import render_template, redirect
from flask import request
from functools import wraps
from flask_babel import Babel, gettext
import postgresql
import filters
from flaskext.markdown import Markdown
from markdown.extensions import Extension
from datetime import date, time, datetime
from flask_language import Language, current_language
import gettext
import click
import re

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = postgresql.open(app.config.get("DATABASE"), user=app.config.get("USER"), password=app.config.get("PASSWORD"))
    #db.row_factory = sqlite3.Row
    return db

app = Flask(__name__)
app.register_blueprint(filters.blueprint)
babel = Babel(app)
lang = Language(app)
gettext.install('motion')

class EscapeHtml(Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['html_block']
        del md.postprocessors['raw_html']
        del md.inlinePatterns['html']

md = Markdown(app, extensions=[EscapeHtml()])

class default_settings(object):
    COPYRIGHTSTART="2017"
    COPYRIGHTNAME="WPIA"
    COPYRIGHTLINK="https://wpia.club"
    IMPRINTLINK="https://documents.wpia.club/imprint.html"
    DATAPROTECTIONLINK="https://documents.wpia.club/data_privacy_policy_html_pages_en.html"
    MAX_PROXY=2


# Load config
app.config.from_object('motion.default_settings')
app.config.from_pyfile('config.py')


class ConfigProxy:
    def __init__(self, name):
        self.name = name
    @property
    def per_host(self):
        dict = app.config.get(self.name)
        if dict is None:
            return None
        return dict.get(request.host)

prefix = ConfigProxy("GROUP_PREFIX")
times = ConfigProxy("DURATION")
debuguser = ConfigProxy("DEBUGUSER")

max_proxy=app.config.get("MAX_PROXY")

@babel.localeselector
def get_locale():
    return str(current_language)

@lang.allowed_languages
def get_allowed_languages():
    return app.config['LANGUAGES'].keys()

@lang.default_language
def get_default_language():
    return 'en'

def get_languages():
    return app.config['LANGUAGES']

# Manually add vote options to the translation strings. They are used as keys in loops.
TRANSLATION_STRINGS={_('yes'), _('no'), _('abstain')}

@app.before_request
def lookup_user():
    global prefix

    env = request.environ
    user = None
    my_debuguser = debuguser.per_host
    if my_debuguser is not None:
        parts = my_debuguser.split("/", 1)
        user = parts[0]
        roles = parts[1]

    if "USER_ROLES" in env:
        parts = env.get("USER_ROLES").split("/", 1)
        user = parts[0]
        roles = parts[1]

    if "USER" in env and "ROLES" in env:
        user = env.get("USER")
        roles = env.get("ROLES")

    if user is None:
        return _('Server misconfigured'), 500
    roles = roles.split(" ")

    if user == "<invalid>":
        return _('Access denied'), 403;

    db = get_db()
    with db.xact():
        rv = db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")(user, request.host)
        if len(rv) == 0:
            db.prepare("INSERT INTO voter(\"email\", \"host\") VALUES($1, $2)")(user, request.host)
            rv = db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")(user, request.host)
        g.voter = rv[0].get("id");
        g.proxies_given = ""
        rv = db.prepare("SELECT email, voter_id FROM voter, proxy WHERE proxy.proxy_id = voter.id AND proxy.revoked IS NULL AND proxy.voter_id = $1 ")(g.voter)
        if len(rv) != 0:
            g.proxies_given = rv[0].get("email")
        rv = db.prepare("SELECT email, voter_id FROM voter, proxy WHERE proxy.voter_id = voter.id AND proxy.revoked IS NULL AND proxy.proxy_id = $1 ")(g.voter)
        if len(rv) != 0:
            sep = ""
            g.proxies_received = ""
            for x in range(0, len(rv)):
                g.proxies_received += sep + rv[x].get("email")
                sep =", "

    g.user = user
    g.roles = {}

    for r in roles:
        a = r.split(":", 1)
        if len(r)!=0:
            val = a[1]
            if a[0] not in g.roles:
                g.roles[a[0]] = []
            if val == "*":
                g.roles[a[0]] = [group for group in prefix.per_host]
            else:
                g.roles[a[0]].append(val)

    return None

@app.context_processor
def init_footer_variables():
    if int(app.config.get("COPYRIGHTSTART"))<datetime.now().year:
        version_year = "%s - %s" % (app.config.get("COPYRIGHTSTART"), datetime.now().year)
    else:
        version_year = datetime.now().year

    return dict(
        footer = dict( version_year=version_year, 
            copyright_link=app.config.get("COPYRIGHTLINK"),
            copyright_name=app.config.get("COPYRIGHTNAME"),
            imprint_link=app.config.get("DATAPROTECTIONLINK"),
            dataprotection_link=app.config.get("DATAPROTECTIONLINK")
        )
    )


def get_allowed_cats(action):
    return g.roles.get(action, []);

def may(action, motion):
    return motion in get_allowed_cats(action)

def may_admin(action):
    return action in g.roles

def get_voters():
    rv = get_db().prepare("SELECT email FROM voter WHERE host=$1")(request.host)
    return rv

def get_all_proxies():
    rv = get_db().prepare("SELECT p.id as id, v1.email as voter_email, v1.id as voterid, "\
                             + "v2.email as proxy_email, v2.id as proxyid "\
                             + "FROM voter AS v1, voter AS v2, proxy AS p "\
                             + "WHERE v2.id = p.proxy_id AND v1.id = p.voter_id AND p.revoked is NULL "\
                             + "AND v1.host=$1 AND v2.host=$1 ORDER BY voter_email, proxy_email")(request.host)
    return rv

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
            g._database = None
            db = get_db()
            ver = 0

        if ver < 1:
            with app.open_resource('sql/schema.sql', mode='r') as f:
                db.execute(f.read())
            return

        if ver < 2:
            with app.open_resource('sql/from_1.sql', mode='r') as f:
                db.execute(f.read())
                ct={}
                for group in [group for group in prefix[app.config.get("DEFAULT_HOST")]]:
                    ct[group] = {"dt": "", "c": 0}

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

        if ver < 4:
            with app.open_resource('sql/from_3.sql', mode='r') as f:
                db.execute(f.read())
                db.prepare("UPDATE \"schema_version\" SET \"version\"=4")()

        if ver < 5:
            with app.open_resource('sql/from_4.sql', mode='r') as f:
                db.execute(f.read())
                db.prepare("UPDATE \"schema_version\" SET \"version\"=5")()

        if ver < 6:
            with app.open_resource('sql/from_5.sql', mode='r') as f:
                db.execute(f.read())
                rv=db.prepare("INSERT INTO voter (email, host) (SELECT vt.email, m.host FROM motion AS m, voter AS vt, vote as v "\
                             + "WHERE (m.id=v.motion_id AND v.voter_id = vt.id) OR (m.id=v.motion_id AND v.proxy_id = vt.id) "\
                             + "GROUP BY m.host, vt.email ORDER BY m.host, vt.email)")()
                rv=db.prepare("UPDATE vote SET voter_id = "\
                             + "(SELECT v_new.id FROM motion AS m, voter AS v_new, voter as v_old "\
                             + "WHERE v_new.email = v_old.email AND v_old.id = vote.voter_id AND "\
                             + "vote.motion_id = m.id AND m.host = v_new.host AND v_old.host is NULL)")()
                rv=db.prepare("UPDATE vote SET proxy_id = "\
                             + "(SELECT v_new.id FROM motion AS m, voter AS v_new, voter as v_old "\
                             + "WHERE v_new.email = v_old.email AND v_old.id = vote.proxy_id AND "\
                             + "vote.motion_id = m.id AND m.host = v_new.host AND v_old.host is NULL)")()
                db.prepare("DELETE FROM voter WHERE host IS Null")()
                db.prepare("ALTER TABLE \"voter\" ALTER COLUMN \"host\" SET NOT NULL")()
                db.prepare("UPDATE \"schema_version\" SET \"version\"=6")()

        if ver < 7:
            with app.open_resource('sql/from_6.sql', mode='r') as f:
                db.execute(f.read())
                db.prepare("UPDATE \"schema_version\" SET \"version\"=7")()

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
    return render_template('index.html', motions=rv[:10], more=rv[10]["id"] if len(rv) == 11 else None, times=times.per_host, prev=prev,
                           categories=get_allowed_cats("create"), singlemotion=False, may_proxyadmin=may_admin("proxyadmin"), languages=get_languages())

def rel_redirect(loc):
    r = redirect(loc)
    r.autocorrect_location_header = False
    return r

def write_proxy_log(userid, action, comment):
    get_db().prepare("INSERT INTO adminlog(user_id, action, comment, action_user_id) VALUES($1, $2, $3, $4)")(userid, action, comment, g.voter)

def write_masking_log(comment):
    get_db().prepare("INSERT INTO adminlog(user_id, action, comment, action_user_id) VALUES($1, 'motionmasking', $2, $1)")(0, comment)

@app.route("/motion", methods=['POST'])
def put_motion():
    cat=request.form.get("category", "")
    if cat not in get_allowed_cats("create"):
        return _('Forbidden'), 403
    time = int(request.form.get("days", "3"));
    if time not in times.per_host:
        return _('Error, invalid length'), 400
    title=request.form.get("title", "")
    title=title.strip()
    if title =='':
        return _('Error, missing title'), 400
    content=request.form.get("content", "")
    content=content.strip()
    if content =='':
        return _('Error, missing content'), 400

    db = get_db()
    with db.xact():
        t = db.prepare("SELECT CURRENT_TIMESTAMP")()[0][0];
        s = db.prepare("SELECT MAX(\"identifier\") FROM \"motion\" WHERE \"type\"=$1 AND \"host\"=$2 AND DATE(\"posed\")=DATE(CURRENT_TIMESTAMP)")
        sr = s(cat, request.host)
        ident=""
        if len(sr) == 0 or sr[0][0] is None:
            ident=prefix.per_host[cat]+"."+t.strftime("%Y%m%d")+".001"
        else:
            nextId = int(sr[0][0].split(".")[2])+1
            if nextId >= 1000:
                return _('Too many motions for this day'), 500
            ident=prefix.per_host[cat]+"."+t.strftime("%Y%m%d")+"."+("%03d" % nextId)
        p = db.prepare("INSERT INTO motion(\"name\", \"content\", \"deadline\", \"posed_by\", \"type\", \"identifier\", \"host\") VALUES($1, $2, CURRENT_TIMESTAMP + $3 * interval '1 days', $4, $5, $6, $7)")
        p(title, content, time, g.voter, cat, ident, request.host)
    return rel_redirect("/")

def motion_edited(motion):
    return rel_redirect("/motion/" + motion)

def validate_motion_access(privilege):
    def decorator(f):
        def decorated_function(motion):
            db = get_db()
            with db.xact():
                rv = db.prepare("SELECT id, type, deadline < CURRENT_TIMESTAMP AS expired, canceled FROM motion WHERE identifier=$1 AND host=$2")(motion, request.host);
                if len(rv) == 0:
                    return _('Error, Not found'), 404
                id = rv[0].get("id")
                if not may(privilege, rv[0].get("type")):
                    return _('Forbidden'), 403
                if rv[0].get("canceled") is not None:
                    return _('Error, motion was canceled'), 403
                if rv[0].get("expired"):
                    return _('Error, out of time'), 403
            return f(motion, id)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator
    
def validate_motion_access_vote(privilege):
    simple_decorator = validate_motion_access(privilege)
    def decorator(f):
        def decorated_function(motion, voter):
            return simple_decorator(lambda motion, id : f(motion, voter, id))(motion)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

@app.route("/motion/<string:motion>/cancel", methods=['POST'])
@validate_motion_access('cancel')
def cancel_motion(motion, id):
    if request.form.get("reason", "none") == "none":
        return _('Error, form requires reason'), 500
    rv = get_db().prepare("UPDATE motion SET canceled=CURRENT_TIMESTAMP, cancelation_reason=$1, canceled_by=$2 WHERE identifier=$3 AND host=$4 AND canceled is NULL")(request.form.get("reason", ""), g.voter, motion, request.host)
    return motion_edited(motion)

@app.route("/motion/<string:motion>/finish", methods=['POST'])
@validate_motion_access('finish')
def finish_motion(motion, id):
    rv = get_db().prepare("UPDATE motion SET deadline=CURRENT_TIMESTAMP WHERE identifier=$1 AND host=$2 AND canceled is NULL")(motion, request.host)
    return motion_edited(motion)

@app.route("/motion/<string:motion>")
def show_motion(motion):
    p = get_db().prepare("SELECT motion.*, poser.email AS poser, canceler.email AS canceler, (motion.deadline > CURRENT_TIMESTAMP AND canceled is NULL) AS running, vote.result FROM motion "\
                         + "LEFT JOIN vote on vote.motion_id=motion.id AND vote.voter_id=$2 "\
                         + "LEFT JOIN voter poser ON poser.id = motion.posed_by "\
                         + "LEFT JOIN voter canceler ON canceler.id = motion.canceled_by "
                         + "WHERE motion.identifier=$1 AND motion.host=$3")
    resultmotion = p(motion, g.voter, request.host)
    if len(resultmotion) == 0:
        return _('Error, Not found'), 404

    p = get_db().prepare("SELECT voter.email FROM vote INNER JOIN voter ON vote.proxy_id = voter.id WHERE vote.motion_id=$1 AND vote.voter_id=$2 AND vote.proxy_id <> vote.voter_id")
    resultproxyname = p(resultmotion[0][0], g.voter)

    p = get_db().prepare("SELECT v.result, proxy.voter_id, voter.email, CASE WHEN proxy.proxy_id = v.proxy_id THEN NULL ELSE voter.email END AS owneremail FROM proxy LEFT JOIN "\
                          + "(SELECT vote.voter_id, vote.result, vote.proxy_id FROM vote "\
                          + "WHERE vote.motion_id=$1) AS v ON proxy.voter_id = v.voter_id "\
                          + "LEFT JOIN voter ON proxy.voter_id = voter.id "\
                          + "WHERE proxy.proxy_id=$2 AND proxy.revoked IS NULL")
    resultproxyvote = p(resultmotion[0][0], g.voter)

    votes = None
    if may("audit", resultmotion[0].get("type")) and not resultmotion[0].get("running") and not resultmotion[0].get("canceled"):
        votes = get_db().prepare("SELECT vote.result, voter.email FROM vote INNER JOIN voter ON voter.id = vote.voter_id WHERE vote.motion_id=$1")(resultmotion[0].get("id"));
        votes = get_db().prepare("SELECT vote.result, voter.email, CASE voter.email WHEN proxy.email THEN NULL ELSE proxy.email END as proxyemail FROM vote INNER JOIN voter ON voter.id = vote.voter_id INNER JOIN voter as proxy ON proxy.id = vote.proxy_id WHERE vote.motion_id=$1")(resultmotion[0].get("id"));
    return render_template('single_motion.html', motion=resultmotion[0], may_vote=may("vote", resultmotion[0].get("type")), may_cancel=may("cancel", resultmotion[0].get("type")), may_finish=may("finish", resultmotion[0].get("type")), votes=votes, proxyvote=resultproxyvote, proxyname=resultproxyname, languages=get_languages())

@app.route("/motion/<string:motion>/vote/<string:voter>", methods=['POST'])
@validate_motion_access_vote('vote')
def vote(motion, voter, id):
    v = request.form.get("vote", "abstain")
    voterid=int(voter)
    db = get_db()

    # test if voter is proxy
    if (voterid != g.voter):
        rv = db.prepare("SELECT voter_id FROM proxy WHERE proxy.revoked IS NULL AND proxy.proxy_id = $1 AND proxy.voter_id = $2")(g.voter, voterid);
        if len(rv) == 0:
            return _('Error, proxy not found.'), 400

    p = db.prepare("SELECT * FROM vote WHERE motion_id = $1 AND voter_id = $2")
    rv = p(id, voterid)
    if len(rv) == 0:
        db.prepare("INSERT INTO vote(motion_id, voter_id, result, proxy_id) VALUES($1,$2,$3,$4)")(id, voterid, v, g.voter)
    else:
        db.prepare("UPDATE vote SET result=$3, entered=CURRENT_TIMESTAMP, proxy_id=$4 WHERE motion_id=$1 AND voter_id = $2")(id, voterid, v, g.voter)
    return motion_edited(motion)

@app.route("/proxy")
def proxy():
    if not may_admin("proxyadmin"):
        return _('Forbidden'), 403
    return render_template('proxy.html', voters=get_voters(), proxies=get_all_proxies(), may_proxyadmin=may_admin("proxyadmin"), languages=get_languages())

@app.route("/proxy/add", methods=['POST'])
def add_proxy():
    if not may_admin("proxyadmin"):
        return _('Forbidden'), 403
    voter=request.form.get("voter", "")
    proxy=request.form.get("proxy", "")
    if voter == proxy :
        return _('Error, voter equals proxy.'), 400
    rv = get_db().prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")(voter, request.host);
    if len(rv) == 0:
        return _('Error, voter not found.'), 400
    voterid = rv[0].get("id")
    rv = get_db().prepare("SELECT id, host FROM voter WHERE email=$1 AND host=$2")(proxy, request.host);
    if len(rv) == 0:
        return _('Error, proxy not found.'), 400
    proxyid = rv[0].get("id")
    rv = get_db().prepare("SELECT id FROM proxy WHERE voter_id=$1 AND revoked is NULL")(voterid);
    if len(rv) != 0:
        return _('Error, proxy allready given.'), 400
    rv = get_db().prepare("SELECT COUNT(id) as c FROM proxy WHERE proxy_id=$1 AND revoked is NULL GROUP BY proxy_id")(proxyid);
    if len(rv) != 0:
        if rv[0].get("c") is None or rv[0].get("c") >= max_proxy:
            return _("Error, Max proxy for '%s' reached.") % (proxy), 400
    rv = get_db().prepare("INSERT INTO proxy(voter_id, proxy_id, granted_by) VALUES ($1,$2,$3)")(voterid, proxyid, g.voter)
    write_proxy_log(voterid, 'proxygranted', 'proxy: '+str(proxyid))
    return rel_redirect("/proxy")

@app.route("/proxy/revoke", methods=['POST'])
def revoke_proxy():
    if not may_admin("proxyadmin"):
        return _('Forbidden'), 403
    id=request.form.get("id", "")
    rv = get_db().prepare("UPDATE proxy SET revoked=CURRENT_TIMESTAMP, revoked_by=$1 WHERE id=$2")(g.voter, int(id))
    write_proxy_log(int(id), 'proxyrevoked', '')
    return rel_redirect("/proxy")

@app.route("/proxy/revokeall", methods=['POST'])
def revoke_proxy_all():
    if not may_admin("proxyadmin"):
        return _('Forbidden'), 403
    rv = get_db().prepare("UPDATE proxy SET revoked=CURRENT_TIMESTAMP, revoked_by=$1 WHERE revoked IS NULL")(g.voter)
    write_proxy_log(g.voter, 'proxyrevokedall', '')
    return rel_redirect("/proxy")

@app.route("/language/<string:language>")
def set_language(language):
    lang.change_language(language)
    return rel_redirect("/")

@app.cli.command("create-user")
@click.argument("email")
@click.argument("host")
def create_user(email, host):
    db = get_db()
    with db.xact():
        rv = db.prepare("SELECT id FROM voter WHERE lower(email)=lower($1) AND host=$2")(email, host)
        messagetext=_("User '%s' already exists on %s.") % (email, host)
        if len(rv) == 0:
            db.prepare("INSERT INTO voter(\"email\", \"host\") VALUES($1, $2)")(email, host)
            messagetext=_("User '%s' inserted to %s.") % (email, host)
    click.echo(messagetext)

@app.cli.command("motion-masking")
@click.argument("motion")
@click.argument("motionreason")
@click.argument("host")
def motion_masking(motion, motionreason, host):
    if re.search(r"[%_\\]", motion):
        messagetext = _("No wildcards allowed for motion entry '%s'.") % (motion)
        click.echo(messagetext)
    else:
        db = get_db()
        with db.xact():
            rv = db.prepare("SELECT id FROM motion WHERE identifier LIKE $1 AND host = $2")(motion+"%", host)
            count = len(rv)
            messagetext = _("%s record(s) affected by masking of '%s'.") % (count, motion)
            click.echo(messagetext)
            if len(rv) != 0:
                rv = db.prepare("SELECT id FROM motion WHERE content LIKE $1 AND host = $2")('%'+motionreason+"%", host)
                rv = db.prepare("UPDATE motion SET name=$3, content=$4 WHERE identifier LIKE $1 AND host = $2 RETURNING id ")(motion+"%", host, _("Motion masked"), _("Motion masked on base of motion [%s](%s) on %s") % (motionreason, motionreason, datetime.now().strftime("%Y-%m-%d")))
                messagetext = _("%s record(s) updated by masking of '%s'.") % (len(rv), motion)
                write_masking_log(_("%s motion(s) masked on base of motion %s with motion identifier '%s' on host %s") %(len(rv), motionreason, motion, host))
                click.echo(messagetext)

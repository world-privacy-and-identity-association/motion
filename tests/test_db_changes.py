import motion
from motion import app
from motion import init_db
from tests.test_basics import BasicTest


class DatabaseTests(BasicTest):
    def setUp(self):
        global user
        user = 'testuser/'

    def tearDown(self):
        pass

    def test_V5(self):
        with self.open_DB() as db:
            with app.open_resource('tests/sql/schema_test_v5.sql', mode='r') as f:
                db.execute(f.read())
            with app.open_resource('tests/sql/sample_data_test_v4.sql', mode='r') as f:
                db.execute(f.read())

            init_db()
    
            ver = db.prepare("SELECT version FROM schema_version")()[0][0]
            self.assertGreaterEqual(ver,6)
    
            # test motion 1
            motion_id=1
            host=app.config.get("DEFAULT_HOST")
            aid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User A", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, aid)
            self.assertEqual(rn[0].get("result"),"yes")
            self.assertEqual(rn[0].get("proxy_id"),aid)

            bid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User B", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, bid)
            self.assertEqual(rn[0].get("result"),"yes")
            self.assertEqual(rn[0].get("proxy_id"),bid)
            # proxy vote where proxy voted herself too
            cid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User C", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, cid)
            self.assertEqual(rn[0].get("result"),"no")
            self.assertEqual(rn[0].get("proxy_id"),bid)

            # test motion 3
            motion_id=3
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, cid)
            self.assertEqual(rn[0].get("result"),"yes")
            self.assertEqual(rn[0].get("proxy_id"),cid)

            # test motion 4 and proxy vote where proxy did not vote herself
            motion_id=4
            eid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User E", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, aid)
            self.assertEqual(rn[0].get("result"),"yes")
            self.assertEqual(rn[0].get("proxy_id"),eid)

            # test motion 2
            motion_id=2
            host='127.0.0.1:5001'
            aid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User A", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, aid)
            self.assertEqual(rn[0].get("result"),"yes")
            self.assertEqual(rn[0].get("proxy_id"),aid)

            bid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User B", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, bid)
            self.assertEqual(rn[0].get("result"),"no")
            self.assertEqual(rn[0].get("proxy_id"),bid)

            cid=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User C", host)[0][0]
            rn=db.prepare("SELECT * FROM vote WHERE motion_id=$1 AND voter_id=$2")(motion_id, cid)
            self.assertEqual(rn[0].get("result"),"no")
            self.assertEqual(rn[0].get("proxy_id"),cid)

            # User E not in host '127.0.0.1:5001'
            rn=db.prepare("SELECT id FROM voter WHERE email=$1 AND host=$2")("User E", host)
            self.assertEqual(len(rn),0)

            # deleted User D
            rn=db.prepare("SELECT id FROM voter WHERE email=$1")("User D")
            self.assertEqual(len(rn),0)

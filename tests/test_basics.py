import motion
import unittest
import postgresql
from unittest import TestCase
from motion import app
from datetime import datetime

app.config.update(
    DEBUGUSER = {},
    GROUP_PREFIX = {'127.0.0.1:5000': {'group1': 'g1', 'group2': 'g2'}},
    DURATION = {'127.0.0.1:5000':[3, 7, 14]},
    SERVER_NAME = '127.0.0.1:5000',
    DEFAULT_HOST = '127.0.0.1:5000',
    MAX_PROXY=2
)

app.config['TESTING'] = True
app.config['DEBUG'] = False

class BasicTest(TestCase):

    def init_test(self):
        self.app = app.test_client()
        self.assertEqual(app.debug, False)

        # reset database
        self.db_clear()

    # functions to manipulate motions
    def createVote(self, user, motion, vote, voter):
        return self.app.post(
            '/motion/' + motion + '/vote/' + str(voter),
            environ_base={'USER_ROLES': user},
            data=dict(vote=vote)
        )

    def createMotion(self, user, motiontitle, motioncontent, days, category):
        return self.app.post(
            '/motion',
            environ_base={'USER_ROLES': user},
            data=dict(title=motiontitle, content=motioncontent, days=days, category=category)
        )

    def cancelMotion(self, user, motion, reason):
        return self.app.post(
            '/motion/' + motion +'/cancel',
            environ_base={'USER_ROLES': user},
            data=dict(reason=reason)
        )

    def finishMotion(self, user, motion):
        return self.app.post(
            '/motion/' + motion +'/finish',
            environ_base={'USER_ROLES': user}
        )

    def addProxy(self, user, voter, proxy):
        return self.app.post(
            '/proxy/add',
            environ_base={'USER_ROLES': user},
            data=dict(voter=voter, proxy=proxy)
        )

    def revokeProxy(self, user, id):
        return self.app.post(
            '/proxy/revoke',
            environ_base={'USER_ROLES': user},
            data=dict(id=id)
        )

    def buildResultText(self, motiontext, yes, no, abstain):
        return '<p>'+motiontext+'</p></p>\n    <p>\nYes <span class=\"badge badge-pill badge-secondary\">'+str(yes)+'</span><br>'\
            + '\nNo <span class=\"badge badge-pill badge-secondary\">'+str(no)+'</span><br>'\
            + '\nAbstain <span class=\"badge badge-pill badge-secondary\">'+str(abstain)+'</span>'


    def open_DB(self):
        return postgresql.open(app.config.get("DATABASE"), user=app.config.get("USER"), password=app.config.get("PASSWORD"))

    # functions to clear database
    def db_clear(self):
        with self.open_DB() as db:
            with app.open_resource('sql/schema.sql', mode='r') as f:
                db.execute(f.read())

    def db_sampledata(self):
        with self.open_DB() as db:
            with app.open_resource('sql/sample_data.sql', mode='r') as f:
                db.execute(f.read())

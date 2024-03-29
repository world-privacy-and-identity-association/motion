from datetime import datetime
from tests.test_basics import BasicTest
from motion import app

# no specific rights required
class GeneralTests(BasicTest):

    def setUp(self):
        self.init_test()
        global user
        user = 'testuser/'
        global userid
        userid = 4
        self.db_sampledata()

    def tearDown(self):
        pass

    def test_main_page(self):
        response = self.app.get('/', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_basic_results_data(self):
        result = self.app.get('/', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<div class="motion card" id="motion-3">\n  <div class="motion-title card-heading alert-warning">'\
            + '\n    <span class="title-text">Motion C</span> (Canceled)\n    <span class="motion-type">group1</span>'\
            + '\n    <div># g1.20200402.003'\
            + '\n    <a class="btn btn-primary" href="/motion/g1.20200402.003" role="button">Result</a>'\
            + '\n    </div>\n    <div class="date">'\
            + '\n      <div>Proposed: 2020-04-02 21:47:24 (UTC) by User A</div>'\
            + '\n      <div>Canceled: 2020-04-03 21:48:24 (UTC) by User A</div>\n     </div>\n  </div>'\
            + '\n  <div class="card-body">\n    <p><p>A third motion</p></p>'\
            + '\n    <p>\nYes <span class="badge badge-pill badge-secondary">1</span><br>'\
            + '\nNo <span class="badge badge-pill badge-secondary">0</span><br>'\
            + '\nAbstain <span class="badge badge-pill badge-secondary">0</span><br>\n    </p>'\
            + '\n    <p>Cancelation reason: Entered with wrong text</p>\n  </div>\n</div>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= '<div class="motion card" id="motion-2">\n  <div class="motion-title card-heading alert-danger">'\
            + '\n    <span class="title-text">Motion B</span> (Finished)\n    <span class="motion-type">group1</span>'\
            + '\n    <div># g1.20200402.002'\
            + '\n    <a class="btn btn-primary" href="/motion/g1.20200402.002" role="button">Result</a>'\
            + '\n    </div>\n    <div class="date">\n      <div>Proposed: 2020-04-02 21:41:26 (UTC) by User A</div>'\
            + '\n      <div>Votes until: 2020-04-04 21:41:26 (UTC)</div>\n     </div>\n  </div>'\
            + '\n  <div class="card-body">\n    <p><p>A second motion</p></p>\n    <p>'\
            + '\nYes <span class="badge badge-pill badge-secondary">1</span><br>'\
            + '\nNo <span class="badge badge-pill badge-secondary">2</span><br>'\
            + '\nAbstain <span class="badge badge-pill badge-secondary">0</span><br>\n    </p>\n  </div>\n</div>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= '<div class="motion card" id="motion-1">\n  <div class="motion-title card-heading alert-success">'\
            + '\n    <span class="title-text">Motion A</span> (Finished)\n    <span class="motion-type">group1</span>'\
            + '\n    <div># g1.20200402.001'\
            + '\n    <a class="btn btn-primary" href="/motion/g1.20200402.001" role="button">Result</a>'\
            + '\n    </div>\n    <div class="date">\n      <div>Proposed: 2020-04-02 21:40:33 (UTC) by User A</div>'\
            + '\n      <div>Votes until: 2020-04-02 21:40:33 (UTC)</div>\n     </div>\n  </div>'\
            + '\n  <div class="card-body">\n    <p><p>My special motion</p></p>\n    <p>'\
            + '\nYes <span class="badge badge-pill badge-secondary">2</span><br>'\
            + '\nNo <span class="badge badge-pill badge-secondary">1</span><br>'\
            + '\nAbstain <span class="badge badge-pill badge-secondary">0</span><br>\n    </p>\n  </div>\n</div>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'Proxy management'
        self.assertNotIn(str.encode(testtext), result.data)

        # start with second motion
        result = self.app.get('/', environ_base={'USER_ROLES': user}, query_string=dict(start=2))
        testtext= 'id=\"motion-3\">'
        self.assertNotIn(str.encode(testtext), result.data)
        testtext= 'id=\"motion-2">'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'id=\"motion-1\">'
        self.assertIn(str.encode(testtext), result.data)

    def test_basic_results_data_details(self):
        motion='g1.20200402.002'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<p>A second motion</p></p>\n  </div>\n</div>\n<a href=\"/?start=2#motion-2\" class=\"btn btn-primary\">Back</a>'
        self.assertIn(str.encode(testtext), result.data)

    def test_vote(self):
        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', userid)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)

    def test_no_user(self):
        result = self.app.get('/', follow_redirects=True)
        self.assertEqual(result.status_code, 500)
        self.assertIn(str.encode('Server misconfigured'), result.data)

    def test_user_invalid(self):
        result = self.app.get('/', environ_base={'USER_ROLES': '<invalid>/'}, follow_redirects=True)
        self.assertEqual(result.status_code, 403)
        self.assertIn(str.encode('Access denied'), result.data)

    def test_basic_env(self):
        result = self.app.get('/', environ_base={'USER': 'testuser', 'ROLES':''}, follow_redirects=True)
        testtext= 'id=\"motion-3\">'
        self.assertIn(str.encode(testtext), result.data)

    def test_basic_results_data_details_not_given(self):
        motion='g1.30190402.001'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(result.status_code, 404)
        self.assertIn(str.encode('Error, Not found'), result.data)

    def test_no_proxy(self):
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(result.status_code, 403)
        self.assertIn(str.encode('Forbidden'), result.data)

    def test_no_proxy_add(self):
        result = self.app.post('proxy/add', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(result.status_code, 403)
        self.assertIn(str.encode('Forbidden'), result.data)

    def test_no_proxy_revoke(self):
        result = self.app.post('proxy/revoke', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(result.status_code, 403)
        self.assertIn(str.encode('Forbidden'), result.data)

    def test_no_proxy_revokeAll(self):
        result = self.app.post('proxy/revokeall', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(result.status_code, 403)
        self.assertIn(str.encode('Forbidden'), result.data)
        
class VoterTests(BasicTest):

    def setUp(self):
        self.init_test()
        global user
        user='testuser/vote:*'
        global userid
        userid = 4
        self.db_sampledata()

    def tearDown(self):
        pass

    def test_main_page(self):
        response = self.app.get('/', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_home_data(self):
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertNotIn("<select class=\"float form-control\" name=\"category\">", str(result.data) )

    def test_vote_yes(self):
        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        resulttext=self.buildResultText('A fourth motion', 1, 0, 0)
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= 'class=\"btn btn-success\" name=\"vote\" value="yes" id="vote-yes">Yes</button>'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'class=\"btn btn-primary\" name=\"vote\" value=\"no\" id=\"vote-no\">No</button>'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'class=\"btn btn-primary\" name=\"vote\" value=\"abstain\" id=\"vote-abstain\">Abstain</button>'
        self.assertIn(str.encode(testtext), result.data)

    def test_vote_no(self):
        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'no', userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        resulttext=self.buildResultText('A fourth motion', 0, 1, 0)
        self.assertIn(str.encode(resulttext), result.data)
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= 'class="btn btn-primary" name="vote\" value=\"yes\" id=\"vote-yes\">Yes</button>'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'class=\"btn btn-success\" name=\"vote\" value=\"no\" id=\"vote-no\">No</button>'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'class=\"btn btn-primary\" name=\"vote\" value=\"abstain\" id=\"vote-abstain\">Abstain</button>'
        self.assertIn(str.encode(testtext), result.data)

    def test_vote_abstain(self):
        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'abstain', userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        resulttext=self.buildResultText('A fourth motion', 0, 0, 1)
        self.assertIn(str.encode(resulttext), result.data)
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= 'class=\"btn btn-primary\" name=\"vote\" value=\"yes\" id=\"vote-yes\">Yes</button>'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'class=\"btn btn-primary\" name=\"vote\" value=\"no\" id=\"vote-no\">No</button>'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'class=\"btn btn-success\" name=\"vote\" value=\"abstain\" id=\"vote-abstain\">Abstain</button>'
        self.assertIn(str.encode(testtext), result.data)

    def test_vote_change(self):
        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        resulttext=self.buildResultText('A fourth motion', 1, 0, 0)
        self.assertIn(str.encode(resulttext), result.data)
        response = self.createVote(user, motion, 'no', userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        resulttext=self.buildResultText('A fourth motion', 0, 1, 0)
        self.assertIn(str.encode(resulttext), result.data)
        response = self.createVote(user, motion, 'abstain', userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        resulttext=self.buildResultText('A fourth motion', 0, 0, 1)
        self.assertIn(str.encode(resulttext), result.data)

    def test_vote_group(self):
        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', userid)
        self.assertEqual(response.status_code, 302)

        motion='g1.20200402.004'
        user1='testuser/vote:group1'
        response = self.createVote(user1, motion, 'yes', userid)
        self.assertEqual(response.status_code, 302)

        motion='g1.20200402.004'
        user1='testuser/vote:group1 vote:group2'
        response = self.createVote(user1, motion, 'yes', userid)
        self.assertEqual(response.status_code, 302)

    def test_vote_wrong_group(self):
        motion='g1.20200402.004'
        user1='testuser/vote:group2'
        response = self.createVote(user1, motion, 'yes', userid)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)

    def test_vote_closed(self):
        motion='g1.20200402.002'
        response = self.createVote(user, motion, 'abstain', userid)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Error, out of time'), response.data)

    def test_vote_canceled(self):
        motion='g1.20200402.003'
        response = self.createVote(user, motion, 'abstain', userid)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Error, motion was canceled'), response.data)

    def test_vote_not_given(self):
        motion='g1.30190402.001'
        response = self.createVote(user, motion, 'abstain', userid)
        self.assertEqual(response.status_code, 404)
        self.assertIn(str.encode('Error, Not found'), response.data)

    def test_cancelMotion(self):
        motion='g1.20200402.004'
        reason="none"
        response = self.cancelMotion(user, motion, reason)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)

    def test_finishMotion(self):
        motion='g1.20200402.004'
        response = self.finishMotion(user, motion)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)

    def test_see_old_vote(self):
        motion='g1.20200402.002'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<div>Proposed: 2020-04-02 21:41:26 (UTC) by User A</div>\n      <div>Votes until: 2020-04-04 21:41:26 (UTC)</div>'\
            + '\n     </div>\n  </div>\n  <div class="card-body">\n    <p><p>A second motion</p></p>\n  </div>\n</div>'\
            + '\n<a href="/?start=2#motion-2" class="btn btn-primary">Back</a>'
        self.assertIn(str.encode(testtext), result.data)

    def test_createMotion(self):
        title='My Motion'
        content='My body'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)


class CreateMotionTests(BasicTest):

    def setUp(self):
        self.init_test()
        global user
        user='testuser/vote:* create:* cancel:* finish:*'
        self.db_clear()

    def tearDown(self):
        pass

    def test_main_page(self):
        response = self.app.get('/', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_home_data(self):
        result = self.app.get('/', environ_base={'USER_ROLES': user})

        # assert the response data
        self.assertIn(b'User: testuser', result.data)
        self.assertIn("<select class=\"float form-control\" name=\"category\">", str(result.data) )

    def test_createMotion(self):
        title='My Motion'
        content='My body'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(str.encode(title), result.data)
        self.assertIn(str.encode(content), result.data)
        self.assertIn(str.encode('g1.'+datetime.today().strftime('%Y%m%d')+'.001'), result.data)
        testtext='<a class=\"btn btn-primary" href=\"/motion/g1.'+datetime.today().strftime('%Y%m%d')+'.001\" role=\"button\">Vote</a>'
        self.assertIn(str.encode(testtext), result.data)

        title='My Motion1'
        content='My body1'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(str.encode(title), result.data)
        self.assertIn(str.encode(content), result.data)
        self.assertIn(str.encode('g1.'+datetime.today().strftime('%Y%m%d')+'.002'), result.data)

        title='My Motion2'
        content='My body2'
        response = self.createMotion(user, title, content, '3', 'group2')
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(str.encode(title), result.data)
        self.assertIn(str.encode(content), result.data)
        self.assertIn(str.encode('g2.'+datetime.today().strftime('%Y%m%d')+'.001'), result.data)

        title='My Motion3'
        content='My body3'
        user1='testuser/vote:* create:group1 cancel:*'
        response = self.createMotion(user1, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)

        title='My Motion4'
        content='My body4'
        user1='testuser/vote:* create:group1 create:group2 cancel:*'
        response = self.createMotion(user1, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)


    def test_createMotionMarkdown(self):
        title='Markdown Test'
        content= 'MyMotionBody MD [text](https//domain.tld/link)'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(str.encode(title), result.data)
        self.assertIn(b'MyMotionBody MD <a href=\"https//domain.tld/link\">text</a>', result.data)

    def test_createMotionMarkdownDirectLink(self):
        title='Markdown Test Link'
        content='MyMotionBody MD <a href=\"https//domain.tld/link\">direct</a'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(str.encode(title), result.data)
        self.assertIn(b'MyMotionBody MD &lt;a href="https//domain.tld/link"&gt;direct&lt;/a', result.data)

    def test_createMotionMarkdownCombined(self):
        title='Markdown Test Link'
        content='Body [combined](https//domain.tld/link) <a href=\"https//domain.tld/link\">combined1</a'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(str.encode(title), result.data)
        self.assertIn(b'Body <a href=\"https//domain.tld/link\">combined</a> &lt;a href="https//domain.tld/link"&gt;combined1&lt;/a', result.data)

    def test_createMotionWrongDayLength(self):
        title='My Motion'
        content='My body'
        response = self.createMotion(user, title, content, '21', 'group1')
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, invalid length'), response.data)

    def test_createMotionMissingData(self):
        title=''
        content=''
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, missing title'), response.data)
        title='New Motion'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, missing content'), response.data)
        title=''
        content='New Content'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, missing title'), response.data)

    def test_createMotionWrongGroup(self):
        title='My Motion'
        content='My body'
        response = self.createMotion(user, title, content, '3', 'test1')
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)

        user1='testuser/vote:* create:group1 cancel:*'
        response = self.createMotion(user1, title, content, '3', 'group2')
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)

    def test_SeeCancelMotion(self):
        self.db_sampledata()

        motion='g1.20200402.004'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<button type="submit" class="btn btn-danger btn-confirm" data-confirm="Do you really want to cancel the motion?" '\
            + 'data-reply="Cancel,Confirm" name="cancel" value="cancel" id="cancel">Cancel</button>'
        self.assertIn(str.encode(testtext), result.data)

        motion='g1.20200402.004'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': 'testuser/vote:*'}, follow_redirects=True)
        testtext= '<button type="submit" class="btn btn-danger btn-confirm" data-confirm="Do you really want to cancel the motion?" '\
            + 'data-reply="Cancel,Confirm" name="cancel" value="cancel" id="cancel">Cancel</button>'
        self.assertNotIn(str.encode(testtext), result.data)

    def test_cancelMotion(self):
        self.db_sampledata()

        motion='g1.20200402.004'
        reason="none"
        response = self.cancelMotion(user, motion, reason)
        self.assertEqual(response.status_code, 500)
        self.assertIn(str.encode('Error, form requires reason'), response.data)

        reason='cancel-test'
        response = self.cancelMotion(user, motion, reason)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(b'Cancelation reason: ' + str.encode(reason), result.data)

        motion='g1.20190402.001'
        reason="none"
        response = self.cancelMotion(user, motion, reason)
        self.assertEqual(response.status_code, 404)
        self.assertIn(str.encode('Error, Not found'), response.data)

        motion='g1.30200402.001'
        reason="cancel-test"
        response = self.cancelMotion(user, motion, reason)
        self.assertEqual(response.status_code, 404)
        self.assertIn(str.encode('Error, Not found'), response.data)

        motion='g1.20200402.004'
        response = self.cancelMotion(user, motion, reason)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Error, motion was canceled'), response.data)

    def test_SeeFinishMotion(self):
        self.db_sampledata()

        motion='g1.20200402.004'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<button type="submit" class="btn btn-danger btn-confirm" data-confirm="Do you really want to finish the motion?" '\
            + 'data-reply="Cancel,Confirm" name="finish" value="finish" id="finish">Finish</button>'
        self.assertIn(str.encode(testtext), result.data)

        motion='g1.20200402.004'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': 'testuser/vote:*'}, follow_redirects=True)
        testtext= '<button type="submit" class="btn btn-danger btn-confirm" data-confirm="Do you really want to finish the motion?" '\
            + 'data-reply="Cancel,Confirm" name="finish" value="finish" id="finish">Finish</button>'
        self.assertNotIn(str.encode(testtext), result.data)

    def test_finishMotion(self):
        self.db_sampledata()

        motion='g1.20200402.004'
        response = self.finishMotion(user, motion)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('/', environ_base={'USER_ROLES': user})
        self.assertIn(b'Motion D</span> (Finished)', result.data)

        motion='g1.30190402.001'
        response = self.finishMotion(user, motion)
        self.assertEqual(response.status_code, 404)
        self.assertIn(str.encode('Error, Not found'), response.data)
        
        motion='g1.20200402.001'
        response = self.finishMotion(user, motion)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Error, out of time'), response.data)

    def test_createMotionWait(self):
        # test no limit given
        self.db_sampledata()
        title='My Motion'
        content='My body'
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)

        # test different host
        app.config.update(MOTION_WAIT_MINUTES={'127.0.0.1:5001':1})
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertEqual(response.status_code, 302)

        # test 3 minutes
        app.config.update(MOTION_WAIT_MINUTES={'127.0.0.1:5000':3})
        response = self.createMotion(user, title, content, '3', 'group1')
        self.assertIn(str.encode('Error, time between last motion to short. The current setting is 3 minute(s).'), response.data)

class AuditMotionTests(BasicTest):

    def setUp(self):
        self.init_test()
        global user
        user='testuser/audit:*'
        self.db_sampledata()

    def tearDown(self):
        pass

    def test_see_old_vote(self):
        motion='g1.20200402.002'
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<div class="motion card" id="votes">\n  <div class="card-heading text-white bg-info">\n    Motion Votes\n  </div>'\
            + '\n  <div class="card-body">\n    <div>User A: yes</div>\n    <div>User B: no</div>'\
            + '\n    <div>User C: no</div>\n  </div>\n</div>\n<a href="/?start=2#motion-2" class="btn btn-primary">Back</a>'
        self.assertIn(str.encode(testtext), result.data)


if __name__ == "__main__":
    unittest.main()

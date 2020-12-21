from datetime import datetime
from tests.test_basics import BasicTest
import motion
import postgresql
from motion import app


class ProxyManagementTests(BasicTest):

    def setUp(self):
        self.init_test()
        global user
        user='testuser/proxyadmin:*'
        global userid
        userid = 4
        self.db_sampledata()

    def tearDown(self):
        pass

    def test_see_proxy(self):
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= 'div class="container">\n<form action="/proxy/add" method="POST">'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'proxy granted to:'
        self.assertNotIn(str.encode(testtext), result.data)
        testtext= 'holds proxy of:'
        self.assertNotIn(str.encode(testtext), result.data)
        testtext= '<select class="float form-control" name="voter">\n        '\
            + '<option>User A</option>\n        <option>User B</option>\n        '\
            + '<option>User C</option>\n        '\
            + '<option>testuser</option>\n      '\
            + '</select>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= '<select class="float form-control" name="proxy">\n          '\
            + '<option>User A</option>\n          '\
            + '<option>User B</option>\n          '\
            + '<option>User C</option>\n          '\
            + '<option>testuser</option>\n      '\
            + '</select>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        <th>Proxy</th>\n        <th></th>\n      </thead>\n    '\
            + '</table>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= '<a class="nav-link" href="/proxy">Proxy management</a>'
        self.assertIn(str.encode(testtext), result.data)

    def test_add_proxy(self):
        voter=''
        proxy=''
        records=0
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, voter equals proxy.'), response.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))

        voter='User A'
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, proxy not found.'), response.data)

        voter='User Z'
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, voter not found.'), response.data)

        voter=''
        proxy='User B'
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, voter not found.'), response.data)

        voter='User B'
        proxy='User B'
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, voter equals proxy.'), response.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))

        voter='User A'
        voterid=1
        proxy='User B'
        records=1
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<form action="/proxy/revoke" method="POST">'
        self.assertIn(str.encode(testtext), result.data)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        '\
            + '<th>Proxy</th>\n        <th></th>\n      </thead>\n      '\
            + '<tr>\n        <td>User A</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="1">Revoke</button></td>\n      '\
            + '</tr>\n    </table>\n'
        self.assertIn(str.encode(testtext), result.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))
        self.logRecordDetailsTest('proxygranted', records-1, voterid, 'proxy: 2', userid)

        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, proxy allready given.'), response.data)

        voter='User A'
        proxy='User C'
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, proxy allready given.'), response.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))

        voter='User C'
        voterid=3
        proxy='User B'
        records=2
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        '\
            + '<th>Proxy</th>\n        <th></th>\n      </thead>\n      '\
            + '<tr>\n        <td>User A</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="1">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User C</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="2">Revoke</button></td>\n      '\
            + '</tr>\n    </table>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'proxy granted to:'
        self.assertNotIn(str.encode(testtext), result.data)
        testtext= 'holds proxy of:'
        self.assertNotIn(str.encode(testtext), result.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))
        self.logRecordDetailsTest('proxygranted', records-1, voterid, 'proxy: 2', userid)

        voter='testuser'
        proxy='User B'
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, Max proxy for \'User B\' reached.'), response.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))

        voter='testuser'
        voterid=4
        proxy='User A'
        records=3
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        <th>Proxy</th>\n        <th></th>\n      </thead>\n      '\
            + '<tr>\n        <td>testuser</td>\n        <td>User A</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="3">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User A</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="1">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User C</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="2">Revoke</button></td>\n      '\
            + '</tr>\n    </table>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'proxy granted to: User A\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'holds proxy of:'
        self.assertNotIn(str.encode(testtext), result.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))
        self.logRecordDetailsTest('proxygranted', records-1, voterid, 'proxy: 1', userid)

        voter='User B'
        voterid=2
        proxy='testuser'
        records=4
        response = self.addProxy(user, voter, proxy)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        <th>Proxy</th>\n        <th></th>\n      </thead>\n      '\
            + '<tr>\n        <td>testuser</td>\n        <td>User A</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="3">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User A</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="1">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User B</td>\n        <td>testuser</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="4">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User C</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="2">Revoke</button></td>\n      '\
            + '</tr>\n    </table>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'proxy granted to: User A\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'holds proxy of: User B\n'
        self.assertIn(str.encode(testtext), result.data)
        self.assertEqual(records, self.recordCountLog('proxygranted'))
        self.logRecordDetailsTest('proxygranted', records-1, voterid, 'proxy: 4', userid)

        recordsRevoked=0
        self.assertEqual(recordsRevoked, self.recordCountLog('proxyrevoked'))
        recordsRevoked=1
        response = self.revokeProxy(user, userid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        <th>Proxy</th>\n        <th></th>\n      </thead>\n      '\
            + '<tr>\n        <td>testuser</td>\n        <td>User A</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="3">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User A</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="1">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User C</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="2">Revoke</button></td>\n      '\
            + '</tr>\n    </table>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'proxy granted to: User A\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'holds proxy of:'
        self.assertNotIn(str.encode(testtext), result.data)
        self.assertEqual(recordsRevoked, self.recordCountLog('proxyrevoked'))
        self.logRecordDetailsTest('proxyrevoked', recordsRevoked-1, userid, '', userid)

        recordsRevoked=2
        proxyid=3
        response = self.revokeProxy(user, proxyid)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        <th>Proxy</th>\n        <th></th>\n      </thead>\n      '\
            + '<tr>\n        <td>User A</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="1">Revoke</button></td>\n      </tr>\n      '\
            + '<tr>\n        <td>User C</td>\n        <td>User B</td>\n        '\
            + '<td><button type="submit" class="btn btn-danger" name="id" value="2">Revoke</button></td>\n      '\
            + '</tr>\n    </table>\n'
        self.assertIn(str.encode(testtext), result.data)
        testtext= 'proxy granted to:'
        self.assertNotIn(str.encode(testtext), result.data)
        testtext= 'holds proxy of:'
        self.assertNotIn(str.encode(testtext), result.data)
        self.assertEqual(recordsRevoked, self.recordCountLog('proxyrevoked'))
        self.logRecordDetailsTest('proxyrevoked', recordsRevoked-1, proxyid, '', userid)

        recordsRevokedAll=0
        self.assertEqual(recordsRevokedAll, self.recordCountLog('proxyrevokedall'))
        recordsRevokedAll=1
        result = self.app.post('proxy/revokeall', environ_base={'USER_ROLES': user}, follow_redirects=True)
        self.assertEqual(response.status_code, 302)
        result = self.app.get('proxy', environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<table>\n      '\
            + '<thead>\n        '\
            + '<th>Voter</th>\n        <th>Proxy</th>\n        <th></th>\n      </thead>\n    '\
            + '</table>\n'
        self.assertIn(str.encode(testtext), result.data)
        self.assertEqual(recordsRevokedAll, self.recordCountLog('proxyrevokedall'))
        self.logRecordDetailsTest('proxyrevokedall', recordsRevokedAll-1, userid, '', userid)

class ProxyVoteTests(BasicTest):

    def setUp(self):
        self.init_test()
        global user
        user='testuser/vote:* proxyadmin:*'
        self.db_sampledata()

    def tearDown(self):
        pass

    def test_proxy_vote(self):
        voter='testuser'
        proxy='User B'
        proxyid=2
        proxyuser='User B/vote:*'

        response = self.addProxy(user, proxy, voter)
        self.assertEqual(response.status_code, 302)

        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', proxyid)
        self.assertEqual(response.status_code, 302)

        # testuser view
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        # own vote without change
        testtext= '<form action="/motion/g1.20200402.004/vote/4" method="POST">\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="yes" id="vote-yes">Yes</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="no" id="vote-no">No</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="abstain" id="vote-abstain">Abstain</button>\n</form>'
        self.assertIn(str.encode(testtext), result.data)
        # proxy vote with change
        testtext= '<form action="/motion/g1.20200402.004/vote/2" method="POST">\n'\
            + '<button type="submit" class="btn btn-success" name="vote" value="yes" id="vote-yes">Yes</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="no" id="vote-no">No</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="abstain" id="vote-abstain">Abstain</button>\n</form>\n'
        self.assertIn(str.encode(testtext), result.data)
        
        # User B view
        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': proxyuser}, follow_redirects=True)
        # own vote without change
        testtext= '<h3>My vote</h3>\nGiven by testuser\n'\
            + '<form action="/motion/g1.20200402.004/vote/2" method="POST">\n'\
            + '<button type="submit" class="btn btn-success" name="vote" value="yes" id="vote-yes">Yes</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="no" id="vote-no">No</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="abstain" id="vote-abstain">Abstain</button>\n</form>'
        self.assertIn(str.encode(testtext), result.data)
        
        # change vote
        response = self.createVote(user, motion, 'no', proxyid)
        self.assertEqual(response.status_code, 302)

        result = self.app.get('/motion/' + motion, environ_base={'USER_ROLES': user}, follow_redirects=True)
        testtext= '<form action="/motion/g1.20200402.004/vote/2" method="POST">\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="yes" id="vote-yes">Yes</button>\n'\
            + '<button type="submit" class="btn btn-success" name="vote" value="no" id="vote-no">No</button>\n'\
            + '<button type="submit" class="btn btn-primary" name="vote" value="abstain" id="vote-abstain">Abstain</button>\n</form>\n'
        self.assertIn(str.encode(testtext), result.data)

    def test_proxy_vote_no_proxy(self):
        voter='testuser'
        proxy='User B'
        # wrong proxy id
        proxyid=3

        response = self.addProxy(user, proxy, voter)
        self.assertEqual(response.status_code, 302)

        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', proxyid)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, proxy not found'), response.data)
        
        # non existing id
        proxyid=10000

        motion='g1.20200402.004'
        response = self.createVote(user, motion, 'yes', proxyid)
        self.assertEqual(response.status_code, 400)
        self.assertIn(str.encode('Error, proxy not found'), response.data)

    def test_proxy_vote_no_voter(self):
        voter='User A'
        proxy='User B'
        proxyid=2

        response = self.addProxy(user, proxy, voter)
        self.assertEqual(response.status_code, 302)

        user1='testuser1/'
        motion='g1.20200402.004'
        response = self.createVote(user1, motion, 'yes', proxyid)
        self.assertEqual(response.status_code, 403)
        self.assertIn(str.encode('Forbidden'), response.data)
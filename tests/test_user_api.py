from tests.test_basics import BasicTest
import click
import motion
import postgresql

from click.testing import CliRunner
from motion import create_user
from motion import motion_masking
from motion import app


class GeneralTests(BasicTest):

    def setUp(self):
        self.init_test()

    def tearDown(self):
        pass

    def test_create_user(self):
        user = 'John Doe'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(create_user, (user, host))
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' inserted to %s." % host, result.output)

        rv = self.db_select2("SELECT email FROM voter WHERE lower(email)=lower($1) AND host=$2", user, host)
        self.assertIn(user, rv[0].get("email"))

        result = runner.invoke(create_user, (user, host))
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' already exists on %s." % host, result.output)

        # test with second host
        host= '127.0.0.1:5001'
        runner = app.test_cli_runner()
        result = runner.invoke(create_user, (user, host))
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' inserted to 127.0.0.1:5001.", result.output)

        rv = self.db_select2("SELECT email FROM voter WHERE lower(email)=lower($1) AND host=$2", user, host)
        self.assertIn(user, rv[0].get("email"))

        result = runner.invoke(create_user, (user, host))
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' already exists on 127.0.0.1:5001.", result.output)

    def test_motion_masking(self):
        self.db_sampledata()
        records=0
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        # test motion not exists
        motion = 'g1.20200402.999'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("0 record(s) affected by masking of 'g1.20200402.999'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        # test motion with wilcards
        motion = 'g1.20200402.00%'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.20200402.00%'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        motion = 'g1.2020040%.001'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.2020040%.001'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        motion = 'g1.20200402.00_'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.20200402.00_'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        motion = 'g1.2020040_.001'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.2020040_.001'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        motion = 'g1.2020040_.%'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.2020040_.%'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        motion = 'g1.20200402.0\\1'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.20200402.0\\1'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        motion = 'g1.2020040\.001'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= app.config.get("DEFAULT_HOST")
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("No wildcards allowed for motion entry 'g1.2020040\\.001'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

        # test masking single motion
        sql = "SELECT id FROM motion WHERE content LIKE $1"
        motion = 'g1.20200402.001'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("1 record(s) affected by masking of 'g1.20200402.001'.", result.output)
        self.assertIn("1 record(s) updated by masking of 'g1.20200402.001'.", result.output)
        records=1
        self.assertEqual(records, self.recordCountLog('motionmasking'))
        self.logRecordDetailsTest('motionmasking', records-1, 0, 
                          "1 motion(s) masked on base of motion http://motiontest.wpia.club/motion/xxx with motion identifier 'g1.20200402.001' on host 127.0.0.1:5000", 0)
        self.assertEqual(1, self.recordCount(sql, '%' + motionreason +'%'))

        # test masking muliple motions
        motion = 'g1.20200402'
        motionreason='http://motiontest.wpia.club/motion/1xxx'
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("4 record(s) affected by masking of 'g1.20200402'.", result.output)
        self.assertIn("4 record(s) updated by masking of 'g1.20200402'.", result.output)
        records=2
        self.assertEqual(records, self.recordCountLog('motionmasking'))
        self.logRecordDetailsTest('motionmasking', records-1, 0, 
                          "4 motion(s) masked on base of motion http://motiontest.wpia.club/motion/1xxx with motion identifier 'g1.20200402' on host 127.0.0.1:5000", 0)
        self.assertEqual(4, self.recordCount(sql, '%' + motionreason +'%'))

        # test different host
        motion = 'g1.20200402.001'
        motionreason='http://motiontest.wpia.club/motion/xxx'
        host= '127.0.0.1:5001'
        runner = app.test_cli_runner()
        result = runner.invoke(motion_masking, (motion, motionreason, host))
        assert result.exit_code == 0
        self.assertIn("0 record(s) affected by masking of 'g1.20200402.001'.", result.output)
        self.assertEqual(records, self.recordCountLog('motionmasking'))

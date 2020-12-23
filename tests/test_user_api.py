from tests.test_basics import BasicTest
import click
import motion
import postgresql

from click.testing import CliRunner
from motion import create_user
from motion import app


def db_select2(self, sql, parameter, parameter2):
    with self.open_DB() as db:
        rv = db.prepare(sql)(parameter, parameter2)
        return rv

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

        rv = db_select2(self,"SELECT email FROM voter WHERE lower(email)=lower($1) AND host=$2", user, host)
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

        rv = db_select2(self,"SELECT email FROM voter WHERE lower(email)=lower($1) AND host=$2", user, host)
        self.assertIn(user, rv[0].get("email"))

        result = runner.invoke(create_user, (user, host))
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' already exists on 127.0.0.1:5001.", result.output)

from tests.test_basics import BasicTest
import click
import motion
import postgresql

from click.testing import CliRunner
from motion import create_user
from motion import app

def db_select(self, sql, parameter):
    with postgresql.open(app.config.get("DATABASE"), user=app.config.get("USER"), password=app.config.get("PASSWORD")) as db:
        rv = db.prepare(sql)(parameter)
        return rv

class GeneralTests(BasicTest):

    def setUp(self):
        self.init_test()

    def tearDown(self):
        pass
    


    def test_create_user(self):
        user = 'John Doe'
        runner = CliRunner()
        result = runner.invoke(create_user, [user])
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' inserted.", result.output)

        rv = db_select(self,"SELECT email FROM voter WHERE lower(email)=lower($1)", user)
        self.assertIn(user, rv[0].get("email"))

        result = runner.invoke(create_user, [user])
        assert result.exit_code == 0
        self.assertIn("User 'John Doe' already exists.", result.output)

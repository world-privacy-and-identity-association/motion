import unittest
import xmlrunner

def runner(output='python_tests_xml'):
    return xmlrunner.XMLTestRunner(
        output=output
    )

def find_tests():
    return unittest.TestLoader().discover('tests', 'test_*.py')

if __name__ == "__main__":
    runner().run(find_tests())

from test_utils import BaseTest
import unittest

class TestGameplay(BaseTest):
    def test_gameplay(self):
        self.assertTrue(False)

def suite():
    gameplay_tests = unittest.TestLoader().loadTestsFromTestCase(TestGameplay)
    return unittest.TestSuite(gameplay_tests)
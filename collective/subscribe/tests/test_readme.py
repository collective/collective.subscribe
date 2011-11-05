import doctest

doctest.testfile('../README.txt')


import doctest
import unittest2 as unittest

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([doctest.DocFileSuite('../README.txt')])
    return suite

if __name__ == '__main__':
    unittest.main()


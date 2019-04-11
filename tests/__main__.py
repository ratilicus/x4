import unittest
import logging

# logger = logging.getLogger()


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)

    suite = unittest.defaultTestLoader.discover(start_dir='.', pattern='test_*.py')
    runner = unittest.TextTestRunner()
    runner.run(suite)

"""
Run tests
Use: ./run_tests.sh
"""

from unittest import TestCase
from unittest.mock import patch, MagicMock
from pack_mod import pack_mod


class PackModUnitTest(TestCase):

    @patch('pack_mod.pack_path')
    def test_pack(self, patch_pack_path):
        config = MagicMock(MODS='mods/path', X4='x4/path')
        pack_mod(mod_name='blah', config=config)
        patch_pack_path.assert_called_once_with(src='mods/path/blah/',
                                                dst='x4/path/extensions/blah/')
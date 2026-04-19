import os
import unittest
from unittest import mock

from App.config import (
    DEFAULT_APP_PORT,
    preview_face_detector_enabled,
    resolve_server_port,
)


class ResolveServerPortTests(unittest.TestCase):
    def test_uses_default_port_when_env_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_server_port(), DEFAULT_APP_PORT)

    def test_uses_port_from_env_when_valid(self):
        with mock.patch.dict(os.environ, {'PORT': '5050'}, clear=True):
            self.assertEqual(resolve_server_port(), 5050)

    def test_falls_back_when_env_is_not_an_int(self):
        with mock.patch.dict(os.environ, {'PORT': 'abc'}, clear=True):
            self.assertEqual(resolve_server_port(), DEFAULT_APP_PORT)

    def test_falls_back_when_env_is_out_of_range(self):
        with mock.patch.dict(os.environ, {'PORT': '70000'}, clear=True):
            self.assertEqual(resolve_server_port(), DEFAULT_APP_PORT)


class PreviewFaceDetectorEnabledTests(unittest.TestCase):
    def test_enabled_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(preview_face_detector_enabled())

    def test_disabled_for_zero(self):
        with mock.patch.dict(os.environ, {'ENABLE_PREVIEW_FACE_DETECTOR': '0'}, clear=True):
            self.assertFalse(preview_face_detector_enabled())

    def test_disabled_for_false(self):
        with mock.patch.dict(os.environ, {'ENABLE_PREVIEW_FACE_DETECTOR': 'false'}, clear=True):
            self.assertFalse(preview_face_detector_enabled())


if __name__ == '__main__':
    unittest.main()

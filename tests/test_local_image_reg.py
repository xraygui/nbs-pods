"""Tests for local image registry prefix selection."""

import os
import unittest
from unittest import mock

from nbs_pods.config import LOCAL_IMAGE_REG, get_local_image_reg


class LocalImageRegTests(unittest.TestCase):
    """``get_local_image_reg`` respects ``BEAMLINE_NAME`` when set."""

    def test_default_without_beamline(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BEAMLINE_NAME", None)
            self.assertEqual(get_local_image_reg(), LOCAL_IMAGE_REG)

    def test_beamline_name_prefix(self):
        with mock.patch.dict(os.environ, {"BEAMLINE_NAME": "haxpes"}):
            self.assertEqual(get_local_image_reg(), "localhost/haxpes-")

"""Tests for compose file resolution with beamline overrides."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nbs_pods.compose import (
    build_compose_file_string,
    get_compose_file,
    get_compose_override,
)


class ComposeResolutionTests(unittest.TestCase):
    """Compose resolution prefers beamline files over nbs-pods defaults."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        root = Path(self._tmpdir.name)
        self.nbs_dir = root / "nbs_pods"
        self.beamline_dir = root / "beamline_pods"
        for base in (self.nbs_dir, self.beamline_dir):
            (base / "compose" / "queueserver").mkdir(parents=True)

        self.nbs_base = self.nbs_dir / "compose" / "queueserver" / "docker-compose.yml"
        self.nbs_override = (
            self.nbs_dir / "compose" / "queueserver" / "docker-compose.override.yml"
        )
        self.beamline_override = (
            self.beamline_dir
            / "compose"
            / "queueserver"
            / "docker-compose.override.yml"
        )
        self.beamline_base = (
            self.beamline_dir / "compose" / "queueserver" / "docker-compose.yml"
        )

        self.nbs_base.write_text("services: {}\n", encoding="utf-8")
        self.nbs_override.write_text("services: {}\n", encoding="utf-8")
        self.beamline_override.write_text("services: {}\n", encoding="utf-8")

        self._patches = [
            mock.patch("nbs_pods.compose.get_nbs_pods_dir", return_value=self.nbs_dir),
            mock.patch(
                "nbs_pods.compose.get_beamline_pods_dir",
                return_value=self.beamline_dir,
            ),
        ]
        for patcher in self._patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_base_falls_back_to_nbs_when_beamline_missing(self):
        compose_file = get_compose_file("queueserver")
        self.assertEqual(compose_file, self.nbs_base)

    def test_base_prefers_beamline_when_present(self):
        self.beamline_base.write_text("services: {}\n", encoding="utf-8")
        compose_file = get_compose_file("queueserver")
        self.assertEqual(compose_file, self.beamline_base)

    def test_override_prefers_beamline(self):
        override = get_compose_override("queueserver", key="override")
        self.assertEqual(override, self.beamline_override)

    def test_build_compose_string_stacks_beamline_override(self):
        composed = build_compose_file_string(
            "queueserver",
            override_keys=["override"],
        )
        parts = composed.split(":")
        self.assertEqual(parts[0], str(self.nbs_base))
        self.assertEqual(parts[1], str(self.beamline_override))


class CreateVersionPinTests(unittest.TestCase):
    """Version pin helpers for child package scaffolding."""

    def test_clean_release_detection(self):
        from nbs_pods.create import is_clean_release_version

        self.assertTrue(is_clean_release_version("0.2.6"))
        self.assertFalse(is_clean_release_version("0.2.7.dev10"))
        self.assertFalse(is_clean_release_version("0.2.6+gf6af298"))

    def test_format_pin_zero_major_uses_minor_bound(self):
        from nbs_pods.create import format_nbs_pods_pin

        self.assertEqual(format_nbs_pods_pin("0.2.6"), ">=0.2.6, <0.3")

    def test_format_pin_nonzero_major_uses_major_bound(self):
        from nbs_pods.create import format_nbs_pods_pin

        self.assertEqual(format_nbs_pods_pin("1.4.2"), ">=1.4.2, <2")


if __name__ == "__main__":
    unittest.main()

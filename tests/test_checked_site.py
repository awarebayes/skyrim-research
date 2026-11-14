"""An artifact is usable only after successful checks of the exact pushed SHA."""
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import checked_site

SHA = 'a' * 40


class CheckedSite(unittest.TestCase):
    def run_info(self, **over):
        return dict(dict(databaseId=42, headSha=SHA, status='completed', conclusion='success'), **over)

    def artifact(self, run, destination):
        self.assertEqual(run, 42)
        with tarfile.open(destination / 'artifact.tar', 'w') as tar:
            data = b'<html>original synthetic site</html>'
            info = tarfile.TarInfo('index.html'); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

    def test_reuses_only_exact_successful_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            calls = Mock(return_value=[self.run_info(), self.run_info(databaseId=99, headSha='b' * 40)])
            self.assertEqual(checked_site.fetch(SHA, out, 0, gh=calls, fetch_artifact=self.artifact), 42)
            self.assertTrue((out / 'index.html').is_file())
            self.assertIn(SHA, calls.call_args.args)

    def test_red_pending_missing_and_wrong_sha_refuse_before_download(self):
        for info in ([self.run_info(conclusion='failure')], [self.run_info(status='in_progress')], [],
                     [self.run_info(headSha='b' * 40)]):
            with self.subTest(info=info), tempfile.TemporaryDirectory() as tmp:
                download = Mock()
                with self.assertRaises(ValueError):
                    checked_site.fetch(SHA, Path(tmp) / 'site', 0, gh=lambda *args: info, fetch_artifact=download)
                download.assert_not_called()

    def test_artifact_links_and_traversal_are_refused(self):
        for name, kind in (('../escape', tarfile.REGTYPE), ('index.html', tarfile.SYMTYPE)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                def artifact(run, destination):
                    with tarfile.open(destination / 'artifact.tar', 'w') as tar:
                        info = tarfile.TarInfo(name); info.type = kind; info.linkname = '/outside'
                        tar.addfile(info)
                with self.assertRaises((ValueError, tarfile.TarError)):
                    checked_site.fetch(SHA, Path(tmp) / 'site', 0, gh=lambda *args: [self.run_info()], fetch_artifact=artifact)

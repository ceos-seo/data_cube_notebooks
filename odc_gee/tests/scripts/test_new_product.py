from os import remove
from pathlib import Path
from tempfile import gettempdir
import filecmp
import subprocess
import unittest

TMP_DIR = gettempdir()
TEST_FILE = f'{Path(__file__).parent.absolute()}/ls8_test.yaml'

class NewProductTestCase(unittest.TestCase):
    def setUp(self):
        path = Path(f'{TMP_DIR}/ls8_test.yaml')
        if path.exists():
            remove(path)

    def tearDown(self):
        path = Path(f'{TMP_DIR}/ls8_test.yaml')
        if path.exists():
            remove(path)

    def test_new_product(self):
        cmd = ["new_product", "--asset", "LANDSAT/LC08/C01/T1_SR", "--product",
               "ls8_test", "--resolution", "(-2.69493352e-4, 2.69493352e-4)",
               "--output_crs", "EPSG:4326", f"{TMP_DIR}/ls8_test.yaml"]
        subprocess.check_output(cmd)
        path = Path(f'{TMP_DIR}/ls8_test.yaml')
        self.assertTrue(path.exists() & path.is_file())
        self.assertTrue(filecmp.cmp(TEST_FILE, f'{TMP_DIR}/ls8_test.yaml', shallow=False))

if __name__ == '__main__':
    unittest.main()

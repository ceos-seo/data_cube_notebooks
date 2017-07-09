base_downloader_script = """import sys
import os, os.path
import tempfile, shutil
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from io import StringIO

try:
    import datacube
except:
    print("Error importing the Data Cube. Please ensure that your environment has the Data Cube installed.")
    print("If you do not have the Data Cube installed, please do so by following the instructions at: ")
    print("https://github.com/ceos-seo/data_cube_ui/blob/master/docs/datacube_install.md")
    exit(1)

files = [{file_list}]
database_dump_file = "{database_dump_file}"
base_host = "http://{base_host}"
base_data_path = "{base_data_path}"
"""

static_script = """

def download_file(data_file, count, total):

    # see if we've already download this file
    if os.path.isfile(data_file):
        print("Storage unit {0} exists! Skipping download of {1}. ".format(os.path.basename(data_file), data_file))
        return None

    # attempt https connection
    try:
        request = Request(base_host + data_file)
        response = urlopen(request)

        # seems to be working
        print("({0}/{1}) Downloading {2}".format(count, total, data_file))

        # Open our local file for writing and build status bar
        tf = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        chunk_read(response, tf, report_hook=chunk_report)

        tempfile_name = tf.name
        tf.close()

    #handle errors
    except HTTPError as e:
        print("HTTP Error:", e.code, data_file)
        return False

    except URLError as e:
        print("URL Error:", e.reason, data_file)
        return False

    # Return the file size
    shutil.copy(tempfile_name, data_file)
    os.remove(tempfile_name)
    return os.path.getsize(data_file)


#  chunk_report taken from http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook
def chunk_report(bytes_so_far, chunk_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\\r" % (bytes_so_far, total_size, percent))

    if bytes_so_far >= total_size:
        sys.stdout.write('\\n')


#  chunk_read modified from http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook
def chunk_read(response, local_file, chunk_size=8192, report_hook=None):
    try:
        total_size = response.info().getheader('Content-Length').strip()
    except AttributeError:
        total_size = response.getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0

    while 1:
        chunk = response.read(chunk_size)
        try:
            local_file.write(chunk)
        except TypeError:
            local_file.write(chunk.decode(local_file.encoding))
        bytes_so_far += len(chunk)

        if not chunk:
            break

        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)

    return bytes_so_far


if __name__ == "__main__":
    # Make sure we can write it our current directory
    if os.access("/datacube", os.W_OK) is False:
        print("Data Cube root path is not writeable - please ensure that the path '/datacube' exists and is writeable.")
        exit(-1)

    try:
        os.makedirs(base_data_path)
    except:
        pass

    print("Starting data download. When complete, a list of instructions will be provided for the next steps.")

    # summary
    total_bytes = 0
    total_time = 0
    count = 0
    success = []
    failed = []
    skipped = []

    size = download_file(database_dump_file, 1, 1)

    for data_file in files:
        count += 1

        start = time.time()
        size = download_file(data_file, count, len(files))
        end = time.time()

        # stats:
        if size is None:
            skipped.append(data_file)

        elif size is not False:
            # Download was good!
            elapsed = end - start
            elapsed = 1.0 if elapsed < 1 else elapsed
            rate = (size / 1024**2) / elapsed

            print("Downloaded {0}b in {1:.2f}secs, Average Rate: {2:.2f}mb/sec".format(size, elapsed, rate))

            # add up metrics
            total_bytes += size
            total_time += elapsed
            success.append({'file': data_file, 'size': size})

        else:
            print("There was a problem downloading {0}".format(data_file))
            failed.append(data_file)

    # Print summary:
    print("Download Summary")
    print("Successes: {0} files, {1} bytes ".format(len(success), total_bytes))
    if len(failed) > 0:
        print("Failures: {0} files".format(len(failed)))
    if len(skipped) > 0:
        print("  Skipped: {0} files".format(len(skipped)))
    if len(success) > 0:
        print("  Average Rate: {0:.2f}mb/sec".format((total_bytes / 1024.0**2) / total_time))

    print("Requirements:")
    print("\tAn initialized Data Cube database named 'datacube'. More info found at https://github.com/ceos-seo/data_cube_ui/blob/master/docs/datacube_install.md")
    print("\tA database role named 'dc_user' that has read/write access to 'datacube'")
    print("Next steps:")
    print("\tImport the newly created database dump by running 'psql -U dc_user datacube < {}'".format(database_dump_file))
    print("\tVerify the import by running 'datacube -v product list'. There should be two entries.")"""

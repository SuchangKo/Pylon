import sys
import os
import json
import errno
import dropbox
from dropbox.files import FileMetadata, FolderMetadata
import platform
import key
import argparse
import contextlib
import datetime
import os
import six
import sys
import time
import unicodedata
import threading
import queue

ARCH = platform.system()  # Test 'Mac' or 'Windows'

dbx = dropbox.Dropbox(key.DROPBOX_TOKEN)  # Dropbox Oauth Token

mainpath = (ARCH == "Windows") and "C:\Pylon" or "/Users/SuchangKo/Pylon"
json_dir = os.path.join(mainpath, "json")
divide_dir = os.path.join(mainpath, "divide")
merge_dir = os.path.join(mainpath, "merge")
divide_size = 20 * 1024 * 1024  # if This Value is 20, Divide Size:20MB


def make_dir(pathname):
    print(pathname)
    if not os.path.exists(pathname):
        os.makedirs(pathname)


def make_complete_file(filename):
    f = open(filename, 'r')
    file_json = json.loads(f.read())
    f.close()

    filename = file_json['filename']
    filesize = file_json['filesize']
    filearray = file_json['arrays']
    div_total = 0

    # sort
    filearray = sorted(filearray, key=lambda k: k['id'], reverse=False)

    # Merge
    merge_filename = os.path.join(merge_dir, filename)
    if os.path.exists(merge_filename):
        os.remove(merge_filename)

    for file_index in range(len(filearray)):
        filenumber = filearray[file_index]['id']
        div_filename = os.path.join(divide_dir, filename + "." + str(filenumber))
        div_total = div_total + os.path.getsize(div_filename)
        save_merge(merge_filename, div_filename)
    print(filename)
    print("filesize : " + str(filesize))
    print("div_total : " + str(div_total))
    print("mergesize  : " + str(os.path.getsize(merge_filename)))
    print("File Check : " + ((os.path.getsize(merge_filename) == filesize) and "Success" or "Fail"))


def get_filesize(filename):
    try:
        b = os.path.getsize(filename)
        kb = b / 1024
        mb = b / 1024.0 / 1024.0
        gb = b / 1024.0 / 1024.0 / 1024.0

        if gb > 1:
            print("File Size : %.2fGB" % gb)
        elif mb > 1:
            print("File Size : %.2fMB" % mb)
        elif kb > 1:
            print("File Size : %.2fKB" % kb)
        else:
            print("File Size : %.2fByte" % b)

        print(str(int((mb / 20) + 1)) + "개로 나누어집니다.")
        return b

    except os.error:
        print("파일이 없거나 에러입니다.")


def save_merge(filename, div_filename):
    print(filename + "--" + div_filename)
    with open(div_filename, 'rb') as div_file:
        with open(filename, 'ab') as file:
            file.write(div_file.read())


def save_distribution(cloud, filename, bytearray, number):
    basename = os.path.basename(filename)
    save_filename = os.path.join(divide_dir, basename)
    # print(save_filename + "." + str(number))
    with open(save_filename + "." + str(number), 'wb') as file:
        file.write(bytearray)
    return save_filename + "." + str(number)


def main():
    make_dir(mainpath)
    make_dir(divide_dir)
    make_dir(json_dir)
    make_dir(merge_dir)

    filename = os.path.join(mainpath, "ubuntu.iso");
    filesize = get_filesize(filename)
    file_divide_total = int((filesize / 1024.0 / 1024.0 / 20.0) + 1)

    # Read File And Distribution
    fileinfo = {}
    fileinfo['filename'] = str(os.path.basename(filename))
    fileinfo['filesize'] = filesize
    fileinfo['arrays'] = []

    index = 0
    upload_threads = [] #Upload Threads
    upload_queue = queue.Queue()
    with open(filename, 'rb') as f:
        bytearray = f.read(divide_size)
        while bytearray != b"":
            cloud = "dropbox"
            account = "test"
            save_filename = save_distribution(cloud, filename, bytearray, index)
            #upload
            #upload(dbx,save_filename,"Pylon","divide",os.path.basename(save_filename))

            th = threading.Thread(target=upload,
                                  args=(dbx, save_filename, "Pylon", "divide", os.path.basename(save_filename)))
            upload_threads.append(th)
            print(str(index + 1) + "/" + str(file_divide_total) + " {0:.2f}%".format(
                round(((index + 1) / file_divide_total * 100), 2)))
            dist_fileinfo = {}
            dist_fileinfo["id"] = index
            dist_fileinfo["cloud"] = cloud
            dist_fileinfo["account"] = account
            fileinfo["arrays"].append(dist_fileinfo)
            bytearray = f.read(divide_size)
            index = index + 1
    index = 0
    for th in upload_threads:
        th.start()
        upload_queue.put(th)
        print("[START]index : "+str(index)+" queue_size : "+str(upload_queue.qsize()))
        while upload_queue.qsize() >= 5:
            end_th = upload_queue.get()
            print("[WAIT] upload_queue : " + str(end_th)+" queue_size : "+str(upload_queue.qsize()))
            end_th.join()
            print("[END] upload_queue : " + str(end_th)+" queue_size : "+str(upload_queue.qsize()))
            break
        index+=1


    print("Upload Complete")

    # Distribution Data
    jsonpath = os.path.join(json_dir, os.path.basename(filename)) + '.json'
    print(jsonpath)
    with open(jsonpath, 'w') as f:
        json.dump(fileinfo, f)

    # Merge File
    make_complete_file(os.path.join(json_dir, os.path.basename(filename)) + '.json')


def download(dbx, folder, subfolder, name):
    print(str(folder))
    print(str(subfolder))
    print(str(name))
    """Download a file.

    Return the bytes of the file, or None if it doesn't exist.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    with stopwatch('download'):
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    return data


def upload(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.

    Return the request response, or None in case of error.
    """

    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(
                data, path, mode,
                client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                mute=True)
        except dropbox.exceptions.ApiError as err:
            print('*** API error', err)
            return None
    print('uploaded as', res.name.encode('utf8'))
    return res


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))


if __name__ == '__main__':
    main()
    sys.exit(0)

'''
{
    "filename":"a.txt"
    "filesize":99999
    "arrays":[
        {
            "id":1,
            "cloud":"dropbox",
            "account":"abcd"
        },
        {
            "id":1,
            "cloud":"dropbox",
            "account":"abcd"
        }
    ]
}
'''

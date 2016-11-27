import sys
import os
import json

import errno

mainpath = "C:\Pylon"
json_dir = os.path.join(mainpath,"json")
divide_dir = os.path.join(mainpath,"divide")
divide_size = 20 * 1024 * 1024 # if This Value is 20, Divide Size:20MB
def make_dir(pathname):
    print(pathname)
    if not os.path.exists(pathname):
        os.makedirs(pathname)
def make_complete_file(filename):
    f = open(filename,'r')
    file_json = json.loads(f.read())
    f.close()

    filename = file_json['filename']
    filesize = file_json['filesize']
    filearray = file_json['arrays']
    print(filename)
    print(filesize)
    print(filearray)


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

        print(str(int((mb / 20) + 1))+"개로 나누어집니다.")
        return b

    except os.error:
        print("파일이 없거나 에러입니다.")


def save_distribution(cloud,filename,bytearray,number):
    basename = os.path.basename(filename)
    save_filename = os.path.join(divide_dir,basename)
    print(save_filename + "." + str(number))
    with open(save_filename+"."+str(number), 'wb') as file:
        file.write(bytearray)

def main():
    make_dir(mainpath)
    make_dir(divide_dir)
    make_dir(json_dir)

    filename = "C:/Pylon/ubuntu.iso"
    filesize = get_filesize(filename)

    # Read File And Distribution
    fileinfo = {}
    fileinfo['filename'] = str(os.path.basename(filename))
    fileinfo['filesize'] = filesize
    fileinfo['arrays'] = []

    index = 0
    with open(filename, 'rb') as f:
        bytearray = f.read(divide_size)
        while bytearray != b"":
            cloud = "dropbox"
            account = "test"
            save_distribution(cloud,filename,bytearray,index)
            dist_fileinfo = {}
            dist_fileinfo["id"] = index
            dist_fileinfo["cloud"] = cloud
            dist_fileinfo["account"] = account
            fileinfo["arrays"].append(dist_fileinfo)
            bytearray = f.read(divide_size)
            index = index+1

    #Distribution Data
    jsonpath = os.path.join(json_dir,os.path.basename(filename))+'.json'
    print(jsonpath)
    with open(jsonpath,'w') as f:
        json.dump(fileinfo,f)

    make_complete_file(os.path.join(json_dir,os.path.basename(filename))+'.json')
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
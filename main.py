import sys
import os
import json
import errno
import dropbox
ARCH = 'Mac' #Test 'Mac' or 'Windows'

mainpath = (ARCH == 'Mac') and "/Users/SuchangKo/Pylon" or "C:\Pylon"
json_dir = os.path.join(mainpath,"json")
divide_dir = os.path.join(mainpath,"divide")
merge_dir = os.path.join(mainpath,"merge")
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
    div_total = 0

    #sort
    filearray = sorted(filearray,key=lambda k: k['id'],reverse=False)

    #Merge
    merge_filename = os.path.join(merge_dir,filename)
    if os.path.exists(merge_filename):
        os.remove(merge_filename)

    for file_index in range(len(filearray)):
        filenumber = filearray[file_index]['id']
        div_filename = os.path.join(divide_dir, filename + "." + str(filenumber))
        div_total = div_total + os.path.getsize(div_filename)
        save_merge(merge_filename,div_filename)
    print(filename)
    print("filesize : " + str(filesize))
    print("div_total : " + str(div_total))
    print("mergesize  : " + str(os.path.getsize(merge_filename)))
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

def save_merge(filename,div_filename):
    print(filename+"--"+div_filename)
    with open(div_filename , 'rb') as div_file:
        with open(filename, 'ab') as file:
            file.write(div_file.read())

def save_distribution(cloud,filename,bytearray,number):
    basename = os.path.basename(filename)
    save_filename = os.path.join(divide_dir,basename)
    #print(save_filename + "." + str(number))
    with open(save_filename+"."+str(number), 'wb') as file:
        file.write(bytearray)

def main():
    make_dir(mainpath)
    make_dir(divide_dir)
    make_dir(json_dir)
    make_dir(merge_dir)

    filename = os.path.join(mainpath,"ubuntu.iso");
    filesize = get_filesize(filename)
    file_divide_total = int((filesize / 1024.0 / 1024.0 / 20.0) + 1)


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
            print(str(index+1)+"/"+str(file_divide_total) + " {0:.2f}%".format(round(((index+1)/file_divide_total*100),2)) )
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
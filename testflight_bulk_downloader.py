#testflight_bulk_downloader.py: download every ipa on a testflight directory on the wayback machine
#made by phil564 on Discord, 2023

#"pip install requests" if you don't have that library btw

import urllib, json, http.client, requests, os, io, shutil, time, plistlib, fnmatch, string
from urllib.parse import urlparse
from zipfile import ZipFile
endpoints = ["http://d193ln56du8muy.cloudfront.net/ipas/","http://d3qktfj96j46kx.cloudfront.net/desktop_app_uploads/","http://d193ln56du8muy.cloudfront.net/uploads/","http://builds.testflightapp.com.s3.amazonaws.com/"]
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0"

fl = open("filelist.txt", "a+") # weird bypass to create file or something
fl.close()
os.makedirs("ipas", exist_ok=True)
os.makedirs("ipas_dl", exist_ok=True)

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', useragent)]
urllib.request.install_opener(opener)   

def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

def dl_ipa(ipai):
    if (ipai[2] != "original"):
        ipaurl = "http://web.archive.org/web/"+ipai[1]+"oe_/"+ipai[2] # i would use oe_
        a = urlparse(ipai[2])
        filename=os.path.basename(a.path)
        try:
            print("[DOWNLOADER] Downloading: "+ipaurl)
            urllib.request.urlretrieve(ipaurl,filename)
            try:
                with ZipFile(filename, 'r') as ipa_zip:
                    files = ipa_zip.namelist()
                    try:
                        info_plist = fnmatch.filter(files, "Payload/*.app/Info.plist")[0]
                        print("[DOWNLOADER] plist Path: "+info_plist)
                        ipa_zip.extract(info_plist)
                        with open(info_plist, 'rb') as infile:
                            plist = plistlib.load(infile)
                        try:
                            newfilename = format_filename(plist["CFBundleDisplayName"])+" ("+plist["CFBundleIdentifier"]+")_"+plist["CFBundleShortVersionString"]+" "+plist["CFBundleVersion"]+"_"+filename
                        except KeyError as ke2:
                            try:
                                if 'CFBundleDisplayName' in str(ke2):
                                    try:
                                        newfilename = plist["CFBundleIdentifier"]+"_"+plist["CFBundleShortVersionString"]+" "+plist["CFBundleVersion"]+"_"+filename
                                    except KeyError as ke3:
                                        if 'CFBundleShortVersionString' in str(ke3):
                                            newfilename = plist["CFBundleIdentifier"]+"_"+plist["CFBundleVersion"]+"_"+filename
                                        elif 'CFBundleVersion' in str(ke3):
                                            newfilename = plist["CFBundleIdentifier"]+"_"+plist["CFBundleShortVersionString"]+"_"+filename
                                elif 'CFBundleShortVersionString' in str(ke2):
                                    newfilename = format_filename(plist["CFBundleDisplayName"])+" ("+plist["CFBundleIdentifier"]+")_"+plist["CFBundleVersion"]+"_"+filename
                                elif 'CFBundleVersion' in str(ke2):
                                    newfilename = format_filename(plist["CFBundleDisplayName"])+" ("+plist["CFBundleIdentifier"]+")_"+plist["CFBundleShortVersionString"]+"_"+filename
                            except KeyError as ke4:
                                print('[ERROR] Unable to set app name. Error: '+str(ke4))
                                newfilename = filename
                    except Exception as ke1:
                        print('[ERROR] plist Path invalid. Error: '+str(ke1))
                        newfilename = filename
                shutil.move(filename,"./ipas/"+newfilename)
                dlinfo = open("./ipas_dl/"+newfilename+"_dlinfo.txt", "w")
                dlinfo.write(ipai[2])
                dlinfo.close()
                shutil.rmtree("./Payload")
            except Exception as ke5:
                print('[ERROR] This file is likely not an IPA. Deleting. Error: '+str(ke5))
                os.remove(filename)
            urllist = open("filelist.txt", "a+")
            urllist.write("\n"+ipai[2])
            urllist.close()
        except Exception as e:
            if 'retrieval incomplete' in str(e):
                print("[ERROR] This file hasn't been saved completely by the Wayback Machine. Skipping.")
                urllist = open("filelist.txt", "a+")
                urllist.write("\n"+ipai[2])
                urllist.close()
            else:
                print(e)
                time.sleep(5)
                dl_ipa(ipai)

for ep in endpoints:
    print("Current Endpoint: "+ep)
    jsonurl = "http://web.archive.org/cdx/search/cdx?output=json&url="+ep+"*" # TODO: check if this goes over the 200 pages from the web wayback machine URL browser
    respa = requests.get(jsonurl,headers={'User-Agent': useragent})
    if respa.status_code != 404:
        urllib.request.urlretrieve(jsonurl,"currentendpointdata.json")
        with open('currentendpointdata.json', 'r') as f:
            ijson = json.load(f)
        for ipai in ijson:
            a = urlparse(ipai[2])
            filename=os.path.basename(a.path)
            filealreadydld=False
            with open('filelist.txt', 'r') as fp:
                for line in fp:
                    x = line[:-1]
                    if x==ipai[2]:
                        filealreadydld=True
            if filealreadydld==True:
                print("[ERROR] "+filename+" has already been downloaded. Skipping.")
            elif (ipai[2] != "original") & (ipai[2] != ep):
                dl_ipa(ipai)
print(f"[DOWNLOADER] Finished!")

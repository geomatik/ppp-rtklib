import subprocess
import datetime
import os
import igs_ftp
import urllib.request
import shutil


def run_ppp(rinexobs, rinexnav, rapid=True, prefixdir=os.getcwd(), coordtype=None, output=None):

    # Verilen Rinex observation dosyasindan day of year
    # bilgisini al ve doy degiskenine ata

    doy = int(os.path.splitext(os.path.basename(rinexobs))[0][4:-1])
    year = int(os.path.splitext(os.path.basename(rinexobs))[1][1:-1])+2000
    station = os.path.splitext(os.path.basename(rinexobs))[0][:4]

    # Rinex adindan elde edilen doy ve yil degerini datetime objesine donustur

    dt = datetime.datetime(year, 1, 1) +  datetime.timedelta(doy-1)

    # Bern universitesi aiub ftp adresinden,
    # EPH efemeris
    # ERP yer donme parametreleri
    # CLK Uydu saat bilgilerini al 

    (clk, eph, erp) = igs_ftp.get_CODE_rapid(dt, prefixdir)
    
    # ppp cozum program icin baslatma zamani
    dt_start = datetime.datetime.utcnow()
    # Cozum icin gerekli dosya bilgilerini goster

    run_log  = " run start: %d-%02d-%02d %02d:%02d:%02d\n" % ( dt_start.year, dt_start.month, dt_start.day, dt_start.hour, dt_start.minute, dt_start.second)
    run_log += "   Station: %s\n" % os.path.splitext(os.path.basename(rinexobs))[0][:4].upper()
    run_log += "      Year: %d\n" % year
    run_log += "       DOY: %03d\n" % doy
    run_log += "      date:  %d-%02d-%02d\n" % (dt.year, dt.month, dt.day)
    run_log += "     RINEX: %s\n" % rinexobs
    run_log += "       CLK: %s\n" % clk
    run_log += "       EPH: %s\n" % eph
    run_log += "       ERP: %s\n" % erp
    print(run_log)

    # RTKLIB icin DLL dosyalarini yukle
    print("Downloading Necessary DLL files\n\n")
    if os.path.isfile("libguide40.dll"):
        print("libguide40.dll already exists. skipping download.")
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/libguide40.dll", "libguide40.dll")
    if os.path.isfile("libiconv-2.dll"):
        print("libiconv-2.dll already exists. skipping download.")
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/libiconv-2.dll", "libiconv-2.dll")
    if os.path.isfile("libintl-2.dll"):
        print("libintl-2.dll already exists. skipping download.")
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/libintl-2.dll", "libintl-2.dll")
    if os.path.isfile("mkl_def.dll"):
        print("mkl_def.dll already exits. skipping download.")
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/mkl_def.dll", "mkl_def.dll")
    if os.path.isfile("mkl_lapack.dll"):
        print("mkl_lapack.dll already exits. skipping download.")
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/mkl_lapack.dll", "mkl_lapack.dll")
    if os.path.isfile("mkl_p4p.dll"):
        print("mkl_p4p.dll already exits. skipping download.")
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/mkl_p4p.dll", "mkl_p4p.dll")

    # RTKLIB post-processing ppp icin gerekli CLI program yukle (RNX2RTKP)
    urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/rnx2rtkp.exe", prefixdir + "\\products\\CODE_rapid\\" + "rnx2rtkp.exe")

    # .Z compressed efemeris (EPH), clock (CLK) ve yer donme parametre (ERP) dosyalarini acmak ici
    # gzip yukle

    urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/gzip.exe", prefixdir + "\\products\\CODE_rapid\\" + "gzip.exe")


    # indirilen EPH, CLK ve ERP dosyalarini ac.
    # ve
    # rinex dosyalarini kopyala
    code_rapid_path = prefixdir + "\products\CODE_rapid"

    for f in os.listdir(prefixdir):
        if f.endswith(os.path.splitext(os.path.basename(rinexobs))[1]):
            shutil.copy2(f, code_rapid_path)
        elif f.endswith(os.path.splitext(os.path.basename(rinexnav))[1]):
            shutil.copy2(f, code_rapid_path)


    os.chdir(code_rapid_path)
    for f in os.listdir():
        if f.endswith(".Z"):
            subprocess.call("gzip.exe" +' -d '+ f)
        else:
            pass

    # IGS Alici anten bilgileri dosyasinin yolu
    atx_path = prefixdir + "/common/igs08.atx"
    # ppp
    for f in os.listdir(code_rapid_path):
        if f.endswith(".CLK"):
            clockfile = f
        elif f.endswith(".ERP"):
            erpfile = f
        elif f.endswith(".EPH"):
            ephfile = f
        else:
            pass
    if coordtype == 1:
        # Cikti koordinatlari enlem/boylam/elipsoidal yukseklik
        coordopt = " -a "
    elif coordtype == 2:
        # Cikti koordinatlari ECEF xyz
        coordopt = " -e "
    else:
        # Default olarak enlem/boylam
        coordopt = " -a "

    if not output:
        subprocess.call("rnx2rtkp.exe" +' -p 7 ' + coordopt + " " + rinexobs + " " + rinexnav + " " + \
            ephfile + " " + clockfile + " " + erpfile + " " + atx_path )
    elif output:
        output = prefixdir + "\\" + output
        subprocess.call("rnx2rtkp.exe" +' -p 7 ' + coordopt + " " + rinexobs + " " + rinexnav + " " + \
            ephfile + " " + clockfile + " " + erpfile + " " + atx_path + " -o " + output)

    with open(output) as pppout:
        lines = pppout.readlines()
        if coordtype == 2:
            print("X-Coordinate (m):", lines[-1].split()[2])
            print("Y-Coordinate (m):", lines[-1].split()[3])
            print("Z-Coordinate (m):", lines[-1].split()[4])
        else:
            print("Latitude: ", lines[-1].split()[2])
            print("Longitue: ", lines[-1].split()[3])
            print("Ellipsoidal height: ", lines[-1].split()[4])


def run_spp(rinexobs, rinexnav, prefixdir=os.getcwd(), coordtype=None, output=None):
    # RTKLIB icin DLL dosyalarini yukle
    print("Downloading Necessary DLL files\n\n")
    if os.path.isfile("libguide40.dll"):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/libguide40.dll", "libguide40.dll")
    if os.path.isfile("libiconv-2.dll"):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/libiconv-2.dll", "libiconv-2.dll")
    if os.path.isfile("libintl-2.dll"):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/libintl-2.dll", "libintl-2.dll")
    if os.path.isfile("mkl_def.dll"):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/mkl_def.dll", "mkl_def.dll")
    if os.path.isfile("mkl_lapack.dll"):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/mkl_lapack.dll", "mkl_lapack.dll")
    if os.path.isfile("mkl_p4p.dll"):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/mkl_p4p.dll", "mkl_p4p.dll")

    # RTKLIB post-processing ppp icin gerekli CLI program yukle (RNX2RTKP)
    if "rnx2rtkp.exe" in os.listdir(prefixdir):
        pass
    else:
        urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/rnx2rtkp.exe", prefixdir + "\\" + "rnx2rtkp.exe")

    if coordtype == 2:
         # Cikti koordinatlari ECEF xyz
        coordopt = " -e "
    else:
        # Default olarak enlem/boylam
        coordopt = " "

    doy = int(os.path.splitext(os.path.basename(rinexobs))[0][4:-1])
    year = int(os.path.splitext(os.path.basename(rinexobs))[1][1:-1])+2000
    dt = datetime.datetime(year, 1, 1) +  datetime.timedelta(doy-1)
    month = str(dt.month)
    day = str(dt.day)


    if not output:
        subprocess.call("rnx2rtkp.exe" +' -p 0 ' + coordopt + " " + rinexobs + " " + rinexnav + \
            " -ts " + str(year) +"/" + month + "/" + day + " 00:00:30 " + " " + " -te " + str(year) + "/" +\
            month + "/" + day + " 00:00:30 " + coordopt)
    elif output:
        output = prefixdir + "\\" + output
        subprocess.call("rnx2rtkp.exe" +' -p 0 ' + coordopt + " " + rinexobs + " " + rinexnav + \
            " -ts " + str(year) +"/" + month + "/" + day + " 00:00:30 " + " " + " -te " + str(year) + "/" +\
            month + "/" + day + " 00:00:30 " + coordopt + " -o " + output)


    with open(output) as sppout:
        lines = sppout.readlines()
        if coordtype == 2:
            print("X-Coordinate (m):", lines[-1].split()[2])
            print("Y-Coordinate (m):", lines[-1].split()[3])
            print("Z-Coordinate (m):", lines[-1].split()[4])
        else:
            print("Latitude: ", lines[-1].split()[2])
            print("Longitue: ", lines[-1].split()[3])
            print("Ellipsoidal height: ", lines[-1].split()[4])
#run_ppp("ista1810.11o", "ista1810.11n", coordtype=2, output="ppp.txt")
#run_spp("C:\\Users\\bahadir\\Desktop\\ppp-rtklib-master\\ista1810.11o", "C:\\Users\\bahadir\\Desktop\\ppp-rtklib-master\\ista1810.11n", coordtype=2, output="spp.txt")
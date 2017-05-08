import subprocess
import datetime
import os
import igs_ftp
import urllib.request


def run_ppp(rinexobs, rapid=True, prefixdir=os.getcwd()):

    # Verilen Rinex observation dosyasindan day of year
    # bilgisini al ve doy degiskenine ata

    doy = int(os.path.splitext(rinexobs)[0][4:-1])
    year = int(os.path.splitext(rinexobs)[1][1:-1])+2000
    station = os.path.splitext(rinexobs)[0][:4]

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
    run_log += "   Station: %s\n" % os.path.splitext(rinexobs)[0][:4].upper()
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
    urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/rnx2rtkp.exe", "rnx2rtkp.exe")

    # .Z compressed efemeris (EPH), clock (CLK) ve yer donme parametre (ERP) dosyalarini acmak ici
    # gzip yukle

    urllib.request.urlretrieve("https://github.com/tomojitakasu/RTKLIB_bin/raw/master/bin/gzip.exe", "gzip.exe")

    # indirilen EPH, CLK ve ERP dosyalarini ac. 

    run_gzip = prefixdir + "/gzip.exe"
    code_rapid_path = prefixdir + "/products/CODE_rapid/"
    subprocess.Popen(run_gzip, cwd=code_rapid_path, shell=True)
    run_rnx2rtkp = prefixdir + "rnx2rtkp.exe"
    atx_path = prefixdir + "/common/igs08.atx"
    


run_ppp("ista1810.11o")



'''


def glab_run(station, dt, rapid=True, prefixdir=""):
    dt_start = datetime.datetime.utcnow()

    doy = dt.timetuple().tm_yday
    rinex = station.get_rinex( dt )

    (clk, eph, erp) = igs_ftp.get_CODE_rapid(dt, prefixdir)

    run_log  = " run start: %d-%02d-%02d %02d:%02d:%02d\n" % ( dt_start.year, dt_start.month, dt_start.day, dt_start.hour, dt_start.minute, dt_start.second)
    run_log += "   Station: %s\n" % station.name
    run_log += "      Year: %d\n" % dt.year
    run_log += "       DOY: %03d\n" % doy
    run_log += "      date:  %d-%02d-%02d\n" % (dt.year, dt.month, dt.day)
    run_log += "     RINEX: %s\n" % rinex
    run_log += "       CLK: %s\n" % clk
    run_log += "       EPH: %s\n" % eph
    run_log += "       ERP: %s\n" % erp
    print run_log

    # we do processing in a temp directory
    tempdir = prefixdir + "/temp/"
    ftp_tools.check_dir( tempdir )
    ftp_tools.delete_files(tempdir) # empty the temp directory

    # copy files to tempdir
    files_to_copy = [ rinex, clk, eph, eph, erp ]
    copied_files = []
    for f in files_to_copy:
        shutil.copy2( f, tempdir )
        (tmp,fn ) = os.path.split(f)
        copied_files.append( tempdir + fn )

    # unzip zipped files, if needed
    for f in copied_files:
        if f[-1] == "Z" or f[-1] == "z": # compressed .z or .Z file
            cmd ='/bin/gunzip'
            cmd = cmd + " -f " + f # -f overwrites existing file
            print "unzipping: ", cmd
            p = subprocess.Popen(cmd, shell=True)
            p.communicate()

    # TODO: if the RINEX file is hatanaka-compressed, uncompress it
    # this requires the CRX2RNX binary
    """
    if rinexfile[-3] == "d" or rinexfile[-3] == "D":
        hata_file = moved_files[0]
        cmd = "CRX2RNX " + hata_file[:-2]
        print "Hatanaka uncompress: ", cmd
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
    """

    # figure out the rinex file name
    (tmp,rinexfile ) = os.path.split(rinex)
    inputfile = rinexfile[:-2] # strip off ".Z"

    # now ppp itself:
    os.chdir( tempdir )

    antfile = prefixdir + "/common/igs08.atx"
    outfile = tempdir + "out.txt"
    
    cmd =  glab_binary # must have this executable in path
    # see doc/glab_options.txt
    options = [ " -input:obs %s" % inputfile,
                " -input:clk %s" % clk,
                " -input:orb %s" % eph,
                " -input:ant %s" % antfile,
                " -model:recphasecenter no", # USNO receiver antenna is not in igs08.atx (?should it be?)
                " -output:file %s" % outfile,
                " -pre:dec 30", # rinex data is at 30s intervals, don't decimate
                " -pre:elevation 10", # elevation mask
                " --print:input", # discard unnecessary output
                " --print:model",
                " --print:prefit",
                " --print:postfit",
                " --print:satellites" ]

    for opt in options:
        cmd += opt
    p = subprocess.Popen(cmd, shell=True, cwd = tempdir )
    p.communicate() # wait for processing to finish

    dt_end = datetime.datetime.utcnow()
    delta = dt_end-dt_start
    run_log2  = "   run end: %d-%02d-%02d %02d:%02d:%02d\n" % ( dt_end.year, dt_end.month, dt_end.day, dt_end.hour, dt_end.minute, dt_end.second)
    run_log2 += "   elapsed: %.2f s\n" % (delta.seconds+delta.microseconds/1.0e6)
    print run_log2

    # here we may parse the output and store it to file somewhere
    ppp_result = glab_parse_result(outfile, station)
    ppp_common.write_result_file( ppp_result=ppp_result, preamble=run_log+run_log2, rapid=rapid, tag=glab_tag, prefixdir=prefixdir )
'''
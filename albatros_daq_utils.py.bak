import numpy as np
import subprocess
import sys
import math
import operator
import os
import stat
import datetime
import time
import re
import configparser

def lprint(msg, logger=None, level=20):
    '''
    Print message to console or logger (if logging instance is provided).
    Logging level defaults to 20 (INFO). Other logging levels: 10=DEBUG, 30=WARNING, 40=ERROR, 50=CRITICAL
    '''

    if logger is not None:
        logger.log(level, msg)
    else:
        print(msg)

def get_channels_from_str(chan, nbits):
    new_chans=np.empty(0, dtype=">H")
    multi_chan=chan.split(" ")
    chan_start_stop=[]
    for single_chan in multi_chan:
        start_stop=map(int, single_chan.split(":"))
        chan_start_stop.extend(start_stop)
    if nbits==1:
        for i in range(len(chan_start_stop)/2):
            new_chans=np.append(new_chans, np.arange(chan_start_stop[2*i], chan_start_stop[2*i+1], 2, dtype=">H"))
    elif nbits==2:
        for i in range(len(chan_start_stop)/2):
            new_chans=np.append(new_chans, np.arange(chan_start_stop[2*i], chan_start_stop[2*i+1], dtype=">H"))
    else:
        for i in range(len(chan_start_stop)/2):
            chans=np.arange(chan_start_stop[2*i], chan_start_stop[2*i+1], dtype=">H")
            new_chans=np.append(new_chans, np.ravel(np.column_stack((chans, chans))))
    return new_chans

def get_coeffs_from_str(coeffs):
    multi_coeff=coeffs.split(" ")
    new_coeffs=np.zeros(2048)
    for single_coeff in multi_coeff:
        start_stop_coeff=map(int, single_coeff.split(":"))
        if start_stop_coeff[2]>=0:
            val=start_stop_coeff[2]
        else:
            val=2**(-start_stop_coeff[2])
        #new_coeffs[np.arange(start_stop_coeff[0], start_stop_coeff[1])]=start_stop_coeff[2]
        new_coeffs[np.arange(start_stop_coeff[0], start_stop_coeff[1])]=val
    new_coeffs=np.asarray(new_coeffs, dtype=">I")
    return new_coeffs

def get_channels_from_freq(nu=[0,30],nbit=0,nu_max=125,nchan=2048,dtype='>i2',verbose=False):
    nseg=len(nu)/2
    for j in range(nseg):
        nu0=nu[2*j]
        nu1=nu[2*j+1]
        if (nu0<nu_max)&(nu1>nu_max):
            print('frequency segment covering max native frequency not allowed')
            return None
        if nu0>nu_max:
            nu0=2*nu_max-nu0
        if nu1>nu_max:
            nu1=2*nu_max-nu1
        if nu0>nu1:
            tmp=nu1
            nu1=nu0
            nu0=tmp
        ch_min=np.int(np.floor(nu0*1.0/nu_max*nchan))
        ch_max=np.int(np.ceil(nu1*1.0/nu_max*nchan))
        mynchan=ch_max-ch_min+1
        if verbose:
            print(j,nu0,nu1,ch_min,ch_max,mynchan)
        if nbit==0:
            if mynchan&1==1:
                if verbose:
                    print('padding 1-bit requested data to have even # of channels')
                mynchan=mynchan+1
        if nbit==0:
            myvec=np.arange(mynchan/2,dtype=dtype)*2+ch_min
        if nbit==1:
            myvec=np.arange(mynchan,dtype=dtype)+ch_min
        if nbit==2:
            myvec=np.arange(mynchan*2,dtype=dtype)/2+ch_min
        if j==0:
            ch_vec=myvec
        else:
            ch_vec=np.append(ch_vec,myvec)
        ch_vec=np.asarray(ch_vec,dtype=dtype)
        print(ch_vec)
    return ch_vec

def get_channels_from_freq_old(nu0=0,nu1=30,nbit=0,nu_max=125,nchan=2048,dtype='>i2'):
    mylen=1
    try:
        mylen=len(nu0)
    except:
        pass
    if mylen>1:
        if len(nu1)!=mylen:
            print('length of nu0 and nu1 in get_channels_from_freq do not match.')
            return None
        for j in range(mylen):
            tmp=get_channels_from_freq(nu0[j],nu1[j],nbit,nu_max,nchan,dtype)
            if j==0:
                ch_vec=tmp
            else:
                ch_vec=np.append(ch_vec,tmp)
        return np.asarray(ch_vec,dtype=dtype)

    ch_min=np.int(np.floor(nu0*1.0/nu_max*nchan))
    ch_max=np.int(np.ceil(nu1*1.0/nu_max*nchan))
    nchan=ch_max-ch_min+1
    #print(ch_min,ch_max,nchan)
    if nbit==0:
        if nchan&1==1:
            print('padding 1-bit requested data to have even # of channels')
            nchan=nchan+1
    if nbit==0:
        ch_vec=np.arange(nchan/2,dtype=dtype)*2+ch_min
    if nbit==1:
        ch_vec=np.arange(nchan,dtype=dtype)+ch_min
    if nbit==2:
        ch_vec=np.arange(nchan*2,dtype=dtype)/2+ch_min
    ch_vec=np.asarray(ch_vec,dtype=dtype)
    return ch_vec

def get_nspec(chans,max_nbyte=1380):
    nspec=np.int(np.floor(max_nbyte/len(chans)))
    if nspec>30:
        nspec=30
    return nspec

def find_emptiest_drive(tag='media'):
    """Find the entry in df with the most free space that included tag in its path."""
    mystr=subprocess.check_output(['df','-k']).decode('utf-8')
    lines=mystr.split('\n')
    best_free=0
    for ll in lines:
        #print(ll)
        tags=ll.split()
        if len(tags)>1:
            #print(tags[-1])
            if tags[-1].find(tag)>=0:
                myfree=float(tags[3])
                #print('possible drive is ',tags[-1],myfree)
                if myfree>best_free:
                    best_free=myfree
                    best_dir=tags[-1]
    #print('best directory is ',best_dir,' with ',best_free/1024./1024.,' free GB')
    if best_free>0:
        return best_dir
    else:
        return None

def parse_str2list(string, delimiter):
    string = re.sub(delimiter+"\s+", delimiter, string)
    return string.split(delimiter)

def get_lsblk(drive_models):
    '''
    Find drives in lsblk that match a given list of drive models and returns device name, partition size, and drive model for every drive found.
    Returned list is organized such that each drive is a separate list and contains info for all corresponding partitions in separate dictionaries.
    i.e. [[{/dev/sda1 info}, {/dev/sda2 info}], [{/dev/sdb1 info}], [{/dev/sdc1 info}, {/dev/sdc2 info}, {/dev/sdc3 info}]]
    If no matching drives found, returns an empty list [].

    drive_models: list
        list of potential drive models to search for
    '''

    if not isinstance(drive_models, list): # if drive_models is not list (e.g. string), attempt to make it into a list
        drive_models = parse_str2list(drive_models, delimiter=",")

    lsblk = subprocess.check_output(['lsblk','-bo','NAME,SIZE,MODEL']).decode('utf-8')
    lines = lsblk.splitlines()
    drives = []
    for i, line in enumerate(lines):
        for drive_model in drive_models:
            if drive_model in line:
                tags = line.split()
                sdx = tags[0]
                model = " ".join(tags[2:])
                partitions = []
                for j in range(i+1,len(lines)):
                    if lines[j].startswith(u'\u2514\u2500'+sdx) or lines[j].startswith(u'\u251c\u2500'+sdx):
                        name, size = lines[j].split()
                        # remove formatted unicode characters at beginning and extra whitespace at end of line
                        name = name.replace(u'\u2514','')
                        name = name.replace(u'\u2500','')
                        name = name.replace(u'\u251c','')
                        partitions.append({'Name': '/dev/'+name, 'Size': int(size), 'Model': model})
                    else:
                        break
                if partitions:
                    drives.append(partitions)
    return drives

def isthere(diskid):
    stuff=subprocess.check_output(['lsblk']).decode('utf-8')
    if diskid in stuff:
        return True
    else:
        return False

def get_mountpoint(diskid):
    '''
    running df to check whether the drive is there
    '''
    df=subprocess.check_output(['df','-h']).decode('utf-8')
    lines=df.splitlines()
    for line in lines:
        if diskid in line:
            tags=line.split()
            if  diskid in tags[0]:
                ind=line.find(diskid)
                tmp=line[ind+len(diskid):]
                ind2=tmp.find('/')
                mount_point=tmp[ind2:]
                return mount_point
    return None #if disk is not mounted

def ismounted(tag):
    '''
    Check df to see if tag is mounted.
    tag may be either the device name (e.g. /dev/sda1) or mountpoint (e.g. /media/pi/BASEBAND) and must exactly match the full device name or mountpoint in df.
    Return True if tag is found, otherwise return False.
    '''
    df = subprocess.check_output('df').decode('utf-8')
    lines = df.splitlines()
    for line in lines:
        if tag in line:
            s = line.split(None, 5) # set maxsplit=5 for cases when there is whitespace in mountpoint
            dev = s[0]
            mountpoint = s[-1]
            if tag == dev or tag == mountpoint:
                return True
    return False

def rename_used_mountpoint(mount_point):
    '''
    If a mount point is already in use, rename it.
    e.g. /media/pi/BASEBAND --> /media/pi/BASEBAND1
    '''
    c = 0
    while ismounted(mount_point): # if mount_point already in use, try altering mount_point slightly.
        c += 1
        if c == 1:
            mount_point = mount_point + str(c)
        else:
            mount_point = mount_point[:-len(str(c-1))] + str(c)
    return mount_point

def safe_mount(device, mount_point):
    '''
    Command to safely mount device (e.g. /dev/sda1) to mount_point.
    '''
    # Rename mount_point if it is already in use by another drive.
    mp_available = rename_used_mountpoint(mount_point)
    # If mount point directory does not exist, make it now.
    if not os.path.isdir(mp_available):
        os.makedirs(mp_available)

    # Simple first stab at this using os.system()
    os.system('sudo mount '+ device +' '+ mp_available)
    # Should probably do something better that waits for return code

def safe_unmount(tag):
    '''
    Command to safely unmount device or mount point.
    tag may be either device name (e.g. /dev/sda1) or mount_point of drive to unmount.
    '''
    # Simple first stab at this using os.system()
    os.system('sudo umount '+tag)
    # Should probably do something better that safely removes or powers off drive.

def mount_drives(drive_models, mount_point, timeout=120, dt=2, extra_search_time=10, logger=None):
    '''
    Mounts the largest partition for every drive found to match a model given in a list of drive_models.
    If many drives are found, mount_point for successive drives is iterated as MOUNTPOINT1,2,3,...
    Returns success = True upon completion or success = False on failure.
    '''
    success = False
    # Wait for drive to appear on lsblk
    lprint("Waiting for drive(s)...", logger)
    to_mount = [] # list of found device names to mount i.e. [/dev/sda1, /dev/sdb1]
    ndrives = len(to_mount) # number of drives found to mount
    t1=time.time()
    while True:
        try:
            drives = get_lsblk(drive_models)
            for drive in drives:
                max_size_partition = max(drive, key=lambda x: x["Size"]) # only need to mount the largest partition in each drive (if there are multiple)
                dev = max_size_partition["Name"] # e.g. /dev/sda1
                if dev not in to_mount:
                    lprint('Found {} on {} after {} s.'.format(max_size_partition["Model"], dev, round(time.time()-t1,3)), logger)
                    to_mount.append(dev)
            # Multiple drives may not appear on lsblk at the exact same time so wait extra_search_time in case another drive shows up.
            if len(to_mount) > ndrives: # new drive was found so start/restart extra_search_time timer
                ndrives = len(to_mount)
                t2 = time.time()
                lprint('Waiting {:d} more seconds in case there are more drives...'.format(extra_search_time), logger)
            # If enough time has passed since last drive was found, consider drive search completed.
            if ndrives > 0:
                if time.time()-t2 > extra_search_time:
                    lprint('Done searching for drive(s).', logger)
                    break
            # If no drives found within timeout time, return success=False
            else:
                if time.time()-t1 > timeout:
                    lprint('Timeout waiting for drive!', logger, 40)
                    return success
        except:
            lprint('Error finding drive!', logger, 40)
            return success
        time.sleep(dt)

    time.sleep(dt)

    for dev in to_mount:
        # Check if drive automounted.
        mp=get_mountpoint(dev) # mp means mount point
        if mp is not None:
            lprint('{} automounted at {}.'.format(dev, mp), logger)
            success = True
        # Otherwise, mount drive manually.
        else:
            lprint('Mounting {}...'.format(dev), logger)
            try:
                safe_mount(dev, mount_point)
            except:
                lprint('Exception while attempting to mount drive!', logger, 30)
                return success
            t1=time.time()
            while True:
                mp=get_mountpoint(dev)
                if mp is not None:
                    lprint('{} mounted at {} after {} s.'.format(dev, mp, round(time.time()-t1,3)), logger)
                    success = True
                    break
                if time.time()-t1 > timeout:
                    lprint('Timeout mounting drive!', logger, 40)
                    success = False
                    return success
                time.sleep(dt)
    return success

def list_drives_to_write_too(drive_models):
    # Find connected drives using lsblk search and allowed drive_models.
    find_drives = get_lsblk(drive_models)
    max_size_partitions = [max(drive, key=lambda x: x["Size"])["Name"] for drive in find_drives]
    # Get more drive info from df.
    df_output=subprocess.check_output(['df','-k', '--block-size=1']).decode('utf-8')
    lines=df_output.splitlines()
    drives=[]
    for line in lines:
        tags=line.split(None, 5) # set maxsplit=5 to avoid splitting mountpoint if it has a space
        if tags[0] in max_size_partitions:
            drives.append({"Partition name":tags[-1].split("/")[-1], "Device":tags[0], "Blocks":int(tags[1]), "Used":int(tags[2]), "Available":int(tags[3]), "Use%":int(tags[4][:-1]), "Mounted on":tags[5]})
    drive_free_bytes=[]
    for drive in drives:
        drive_free_bytes.append(drive["Use%"])
    new_drives=[]
    for i in range(len(drive_free_bytes)):
        max_index, max_value=max(enumerate(drive_free_bytes), key=operator.itemgetter(1))
        new_drives.append(drives.pop(max_index))
        drive_free_bytes.pop(max_index)
    return new_drives

def num_files_can_write(drive_path, safety, file_size):
    st=os.statvfs(drive_path)
    used_bytes=st.f_blocks*st.f_bsize-st.f_bfree*st.f_bsize
    free_bytes=st.f_bsize*st.f_bavail
    total=used_bytes+free_bytes
    nfile_targ=int(math.floor((safety/100.*total-used_bytes)/(1.024e9*file_size)))
    return nfile_targ

def find_mac():
    mystr=subprocess.check_output('ifconfig').decode('utf-8')
    lines=mystr.splitlines()
    targ='192.168.2.200'
    mac=""
    for i in range(len(lines)):
        ll=lines[i]
        if ll.find(targ)>0:
            #print('found target in line ',ll)
            #print('previous line was ',lines[i-1])
            tags=lines[i-1].split()
            mac='0x'+tags[0][3:-1]
    return mac

def read_ifconfig(interface='eth0'):
    ip = None
    port = None
    mac = None
    ifconfig = subprocess.check_output('ifconfig').decode('utf-8')
    lines = ifconfig.split('\n') # use split('\n') rather than splitlines() because want to know when there are empty lines
    for i, line in enumerate(lines):
        if line.startswith(interface):
            port = line.split('<')[0].split(interface+': flags=')[-1]
            break
    for j in range(i+1,len(lines)):
        if lines[j]:
            tags = lines[j].split()
            if tags[0] == 'inet':
                ip = tags[1]
            if tags[0] == 'ether':
                mac = '0x'+tags[1].replace(':', '')
        else: # If string is empty, stop reading as the last ifconfig line relevant to `interface` has been reached.
            break
    return ip, port, mac

def gps_time_from_rtc():
    utc=datetime.datetime.now()
    datetimeformat="%Y-%m-%d %H:%M:%S"
    epoch=datetime.datetime.strptime("1980-01-06 00:00:00",datetimeformat)
    tdiff=utc-epoch
    gpsweek=tdiff.days//7 
    gpsdays=tdiff.days-7*gpsweek
    gpsseconds=tdiff.seconds+86400*(tdiff.days-7*gpsweek)
    return {"week":gpsweek, "seconds":gpsseconds}

def get_config_parameter(configfile, parameter, section="albatros2"):
    config_file = configparser.SafeConfigParser()
    config_file.read(configfile)
    return config_file.get(section, parameter)

from struct import unpack, pack
from numpy import array
import matplotlib.image
import os
import math

#functions
def getPayload(payload):
    """
    check what payload was used
    """
    if payload == 1:
        return "SMIV"
    elif payload == 2:
        return "SMIN"
    elif payload == 3:
        return "HPTR"
    elif payload == 4:
        return "HPTG"
    elif payload == 5:
        return "HPTB"
    elif payload == 6:
        return "HPTN"
    elif payload == 7:
        return "WFC"
    else:
        return "MFC"

def binDateToInt(astring):
    temp = ' '.join(format(ord(i),'b').zfill(8) for i in astring)
    temp1 = temp[0:4]
    temp1 = int(temp1,2)
    temp2 = temp[4:8]
    temp2 = int(temp2,2)
    temp = (temp1*10)+temp2
    if temp<10:
        temp = "0"+str(temp)
    else:
        temp = str(temp)
    return temp

def binToImage(filename, imagename):
    with open(filename, "rb") as img:
        img.seek(200)
        data = img.read(504*692*2)
        data = array(unpack(">"+"H"*(504*692),data)).reshape(504,692)
        matplotlib.image.imsave(imagename, data, cmap="gray", format="png")

#input
#Large TLM file input
binfile = "F20160907111258.bin"

#get number of bytes in binfile
bytesize = int(os.path.getsize(binfile))
print "TLM file size of "+binfile+" is "+str(bytesize)+" bytes."

#cursor for binary reading
cursor = 0

#image counter
imagenumber = 0
print "Reading bin files...\n"
#main
with open(binfile, "rb") as f:
    while cursor<=bytesize-4:
        f.seek(cursor)
        byte = f.read(2)
        byte = unpack(">H", byte)[0]

        #64243 corresponds to FA F3
        if byte == 64243:
            f.seek(cursor+14)
            shu_id = f.read(2)
            shu_id = unpack(">H", shu_id)[0]

            f.seek(cursor+16)
            payload_id = f.read(2)
            payload_id = unpack(">H",payload_id)[0]

            if (shu_id == 8) and (payload_id < 9):
                print "Image found... extracting..."
                
                #create a temp bin file
                tempbinfile = open("temp.bin", "wb") 
                
                #set cursor pointer at shu id location -> 00 08
                cursor=cursor+14
                
                #extract bin file of the image

                #count the number of line of the bin file
                #1 line = 120 bytes of data, there are 5814 total lines
                linecount = 0

                #counts the number of bytes written
                bytecount = 0
                
                while linecount<=5814:
                    #check if theres no data interruption = AA AA
                    f.seek(cursor)
                    checkbyte=f.read(2)
                    checkbyte=unpack(">H", checkbyte)[0]
                    
                    if checkbyte==43690:
                        cursor+=138
                    else:
                        #check line number
                        f.seek(cursor+120)
                        linenumber = f.read(2)
                        linenumber = unpack(">H", linenumber)[0]

                        #check error 01 4B at 120th byte
                        f.seek(cursor+118)
                        hexval = f.read(2)
                        hexval = unpack(">H", hexval)[0]

                        #weird error catch 119 and 120 byte - 01 4B > should be 00 23
                        if (hexval== 331) and (linenumber!=linecount):
                            data120 = 118
                            sync18 = 20
                            linenumber=linecount

                        else:
                            data120 = 120
                            sync18 = 18

                        #when last line number is read, theres only 56 bytes of data left
                        if linenumber==5814:
                            data120 = 56
                            sync = 82
                        
                        if linenumber==linecount:
                            f.seek(cursor)
                            for i in range(data120):
                                imgbyte=f.read(1)
                                tempbinfile.write(imgbyte)
                                bytecount+=1
                                cursor+=1

                                #get information on image
                                #year
                                if (linenumber==0) and (bytecount==89):
                                    year = str(int(binDateToInt(imgbyte))+2000)

                                #month                            
                                if (linenumber==0) and (bytecount==90):
                                    month = str(int(binDateToInt(imgbyte))).zfill(2)

                                #day
                                if (linenumber==0) and (bytecount==91):
                                    day = str(int(binDateToInt(imgbyte))).zfill(2)

                                #hour
                                if (linenumber==0) and (bytecount==92):
                                    hour = str(int(binDateToInt(imgbyte))).zfill(2)

                                #minute                            
                                if (linenumber==0) and (bytecount==93):
                                    minute = str(int(binDateToInt(imgbyte))).zfill(2)

                                #sec
                                if (linenumber==0) and (bytecount==94):
                                    sec = str(int(binDateToInt(imgbyte))).zfill(2)
                            
                            if data120 == 118:
                                tempbinfile.write(pack('i',0))
                                tempbinfile.write(pack('i',35))
                            #skips sync code
                            cursor+=sync18
                            linecount+=1

                        else:
                            while linecount<linenumber:
                                #fill packetloss with 00 bytes:
                                for j in range(120):
                                    tempbinfile.write(pack('i',0))
                                linecount+=1
                                
                            

                #get payload source
                payload = getPayload(payload_id)
                tempbinfile.close()
                filename = payload+"_CAP"+year+month+day+"_"+hour+minute+sec+".bin"
                imagename = payload+"_CAP"+year+month+day+"_"+hour+minute+sec+".png"
                if os.path.exists(filename):
                    print "File already exist...deleting temp file..."
                    os.remove("temp.bin")
                else:
                    os.rename("temp.bin", filename)
                    print payload+"_CAP"+year+month+day+"_"+hour+minute+sec+".bin created.\n"
                    #create image file
                    binToImage(filename,imagename)
                    imagenumber+=1
                
            else:
                cursor+=1                
        else:
            cursor+=1
print "Total of "+str(imagenumber)+" images extracted."

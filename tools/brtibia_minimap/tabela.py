import struct,sys
dat,otb,dump,out=sys.argv[1:5]
items=struct.unpack('<IH',open(dat,'rb').read(6))[1]
o=open(otb,'rb').read(); i=4; m={}
def props(i):
    r=bytearray()
    while True:
        b=o[i]
        if b==0xFD: r.append(o[i+1]); i+=2; continue
        if b in (0xFE,0xFF): return bytes(r),i
        r.append(b); i+=1
i+=1; _,i=props(i)
while o[i]==0xFE:
    i+=1; p,i=props(i); j=5; sid=cid=None
    while j<len(p):
        a=p[j]; L=struct.unpack_from('<H',p,j+1)[0]; v=p[j+3:j+3+L]; j+=3+L
        if a==0x10: sid=struct.unpack('<H',v[:2])[0]
        elif a==0x11: cid=struct.unpack('<H',v[:2])[0]
    if sid is not None and cid: m[sid]=cid
    i+=1
info={}
for l in open(dump):
    c,*r=map(int,l.split()); info[c]=r
falt=0
with open(out,'w') as f:
    for sid,cid in sorted(m.items()):
        if cid>items or cid not in info: falt+=1; continue
        f.write(' '.join(map(str,[sid]+info[cid]))+'\n')
print('otb',len(m),'sem dat',falt)

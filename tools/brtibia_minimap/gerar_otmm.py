import numpy as np, zlib, struct, sys
src,dst=sys.argv[1:3]
a=np.fromfile(src,dtype=np.dtype([('x','<u2'),('y','<u2'),('z','u1'),('c','u1'),('f','u1'),('s','u1')]))
bk=(a['z'].astype(np.int64)<<32)|((a['y'].astype(np.int64)//64)<<16)|(a['x'].astype(np.int64)//64)
o=np.argsort(bk,kind='stable'); a=a[o]; bk=bk[o]
u,st=np.unique(bk,return_index=True); st=list(st)+[len(a)]
out=bytearray(struct.pack('<IHHI',0x4D4D544F,0,1,0)); desc=b'OTMM 1.0'; out+=struct.pack('<H',len(desc))+desc
start=len(out); struct.pack_into('<H',out,4,start)
for i,key in enumerate(u):
    t=a[st[i]:st[i+1]]
    blk=np.zeros((64*64,3),dtype=np.uint8); blk[:,1]=255; blk[:,2]=10
    idx=(t['y']%64).astype(np.int64)*64+(t['x']%64)
    blk[idx,0]=t['f']; blk[idx,1]=t['c']; blk[idx,2]=t['s']
    z=int(key>>32); by=int((key>>16)&0xFFFF)*64; bx=int(key&0xFFFF)*64
    c=zlib.compress(blk.tobytes(),6)
    out+=struct.pack('<HHBH',bx,by,z,len(c))+c
out+=struct.pack('<HHB',65535,65535,255)
open(dst,'wb').write(out)
print('blocos',len(u),'tamanho',len(out))

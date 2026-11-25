// le um OTBM e grava, por tile: x(u16) y(u16) z(u8) cor(u8) flags(u8) speed(u8)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
typedef struct { int col, nw, np, pr, sp, ok; } Info;
static Info tab[65536];
static unsigned char *d; static size_t n, pos;
static FILE *fo; static long ntiles, nunknown;
static unsigned char pb[1<<20]; static size_t pl;
static int readprops(void){ pl=0; while(pos<n){ unsigned char b=d[pos]; if(b==0xFD){ if(pl<sizeof pb) pb[pl++]=d[pos+1]; pos+=2; continue;} if(b==0xFE||b==0xFF) return 1; if(pl<sizeof pb) pb[pl++]=b; pos++; } return 0; }
static void skipnode(void){ int dd=1; while(pos<n&&dd>0){ unsigned char c=d[pos]; if(c==0xFD){pos+=2;continue;} if(c==0xFE)dd++; else if(c==0xFF)dd--; pos++; } }
static int bx, by, bz;
static void emit(int x,int y,int z,int *ids,int cnt){
  int color=255, flags=1, speed=10, hasground=0, nw=0, np=0;
  // ordem do cliente: itens de prioridade 0..3 em ordem, depois comuns; cor = de tras pra frente, ignorando comuns
  int idx[512]; int k=0;
  for(int p=0;p<=3;p++) for(int i=0;i<cnt;i++){ Info*t=&tab[ids[i]]; if(t->ok&&t->pr==p) idx[k++]=i; }
  for(int i=0;i<cnt;i++){ Info*t=&tab[ids[i]]; if(!t->ok){nunknown++;continue;} if(t->nw) nw=1; if(t->np) np=1; }
  if(k>0 && tab[ids[idx[0]]].pr==0){ hasground=1; int gs=tab[ids[idx[0]]].sp; speed=(int)ceil(gs/10.0); if(speed>255)speed=255; }
  else speed=10;
  for(int j=k-1;j>=0;j--){ int c=tab[ids[idx[j]]].col; if(c!=0){ color=c; break; } }
  if(nw||!hasground) flags|=4;
  if(np) flags|=2;
  unsigned char r[8]={x&255,x>>8,y&255,y>>8,z,color,flags,speed};
  fwrite(r,1,8,fo); ntiles++;
}
// pos aponta logo apos o 0xFE de um no TILE/HOUSETILE
static void tile(int type){
  readprops(); size_t q=0; int tx=pb[0], ty=pb[1]; q=2; if(type==14) q+=4;
  int ids[512]; int cnt=0;
  while(q<pl){ int a=pb[q++]; if(a==3){ q+=4; } else if(a==9){ if(cnt<512) ids[cnt++]=pb[q]|pb[q+1]<<8; q+=2; } else break; }
  while(pos<n){
    if(d[pos]==0xFE){ pos++; int t=d[pos]; size_t save=pos; (void)save;
      if(t==6){ pos++; readprops(); if(pl>=2&&cnt<512) ids[cnt++]=pb[0]|pb[1]<<8;
        // filhos (itens dentro de container) sao ignorados
        while(pos<n&&d[pos]==0xFE){ pos++; skipnode(); }
        pos++; }
      else { pos++; skipnode(); }
    } else if(d[pos]==0xFF){ pos++; break; } else pos++;
  }
  emit(bx+tx, by+ty, bz, ids, cnt);
}
static void area(void){
  readprops(); bx=pb[0]|pb[1]<<8; by=pb[2]|pb[3]<<8; bz=pb[4];
  while(pos<n){
    if(d[pos]==0xFE){ pos++; int t=d[pos]; if(t==5||t==14){ pos++; tile(t);} else { pos++; skipnode(); } }
    else if(d[pos]==0xFF){ pos++; return; } else pos++;
  }
}
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"rb"); fseek(f,0,2); n=ftell(f); fseek(f,0,0); d=malloc(n); fread(d,1,n,f); fclose(f);
  FILE*t=fopen(argv[2],"r"); int s,c,nw,np,pr,sp; while(fscanf(t,"%d %d %d %d %d %d",&s,&c,&nw,&np,&pr,&sp)==6){ tab[s]=(Info){c,nw,np,pr,sp,1}; } fclose(t);
  fo=fopen(argv[3],"wb");
  pos=4; if(d[pos]!=0xFE){fprintf(stderr,"nao e OTBM\n");return 1;}
  pos++; pos++; readprops(); // root
  while(pos<n){
    if(d[pos]==0xFE){ pos++; int t=d[pos]; pos++;
      if(t==2){ readprops(); // MAP_DATA
        while(pos<n){ if(d[pos]==0xFE){ pos++; int tt=d[pos]; pos++; if(tt==4) area(); else skipnode(); } else if(d[pos]==0xFF){ pos++; break; } else pos++; }
      } else skipnode();
    } else pos++;
  }
  fclose(fo); fprintf(stderr,"tiles %ld itens desconhecidos %ld\n",ntiles,nunknown); return 0;
}

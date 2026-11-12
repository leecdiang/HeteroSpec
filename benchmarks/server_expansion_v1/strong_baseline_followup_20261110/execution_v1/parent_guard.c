#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <unistd.h>
// Linux-only, no GPU/library initialization. Protect against parent loss even
// when the native worker has its own session/process group.
int main(int argc,char**argv){
    if(argc<5||strcmp(argv[1],"--parent")||strcmp(argv[3],"--"))return 125;
    char* end=NULL;errno=0;long parent=strtol(argv[2],&end,10);
    if(errno||!end||*end||parent<=1||parent>INT_MAX)return 125;
    if(prctl(PR_SET_PDEATHSIG,SIGTERM)!=0){perror("PR_SET_PDEATHSIG");return 125;}
    if(getppid()!=(pid_t)parent){raise(SIGTERM);return 125;}
    execvp(argv[4],argv+4);perror("exec registered worker");return 126;
}

/* Diagnostic only. Sample the interrupted instruction pointer of this process.
 * No ptrace/perf privilege, stack unwind, memory inspection or foreign attach.
 * The handler uses only the supplied signal context and async-safe write.
 */
#define _GNU_SOURCE
#include <signal.h>
#include <sys/time.h>
#include <sys/syscall.h>
#include <ucontext.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
static int sample_fd=-1;
static void sample(int sig,siginfo_t*info,void*context){
 (void)sig;(void)info;
 uint64_t record[2]={(uint64_t)syscall(SYS_gettid),(uint64_t)((ucontext_t*)context)->uc_mcontext.gregs[REG_RIP]};
 if(sample_fd>=0)(void)write(sample_fd,record,sizeof(record));
}
static void maps(const char*name){
 const char*dir=getenv("Q32_OWN_SAMPLE_DIRECTORY");if(!dir)return;
 char path[4096];snprintf(path,sizeof(path),"%s/%s",dir,name);
 int in=open("/proc/self/maps",O_RDONLY),out=open(path,O_CREAT|O_EXCL|O_WRONLY,0600);
 if(in>=0&&out>=0){char data[8192];ssize_t n;while((n=read(in,data,sizeof(data)))>0)(void)write(out,data,(size_t)n);}
 if(in>=0)close(in);if(out>=0)close(out);
}
__attribute__((constructor))static void begin(void){
 const char*dir=getenv("Q32_OWN_SAMPLE_DIRECTORY");if(!dir)return;
 char path[4096];snprintf(path,sizeof(path),"%s/instruction-pointers.bin",dir);
 sample_fd=open(path,O_CREAT|O_EXCL|O_WRONLY,0600);if(sample_fd<0)return;
 maps("maps-before.private.txt");
 struct sigaction action={0};action.sa_sigaction=sample;action.sa_flags=SA_SIGINFO|SA_RESTART;sigemptyset(&action.sa_mask);
 if(sigaction(SIGPROF,&action,0)){close(sample_fd);sample_fd=-1;return;}
 struct itimerval timer={{0,10000},{0,10000}};setitimer(ITIMER_PROF,&timer,0);
}
__attribute__((destructor))static void end(void){
 if(sample_fd<0)return;struct itimerval timer={{0,0},{0,0}};setitimer(ITIMER_PROF,&timer,0);
 maps("maps-after.private.txt");close(sample_fd);sample_fd=-1;
}

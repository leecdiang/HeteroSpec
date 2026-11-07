// CPU-only bounded capture used by the actual PowerShell launcher.
// Redirected pipes provide back-pressure. A soft-limit breach terminates the
// owned Windows job before further reads, then drains all remaining pipe bytes.
using System;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.Threading;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
using System.Security.Cryptography;
using System.Collections.Generic;

public sealed class B570Capture {
    [StructLayout(LayoutKind.Sequential)] struct BASIC { public long PerProcessUserTimeLimit,PerJobUserTimeLimit; public uint LimitFlags; public UIntPtr MinimumWorkingSetSize,MaximumWorkingSetSize; public uint ActiveProcessLimit; public UIntPtr Affinity; public uint PriorityClass,SchedulingClass; }
    [StructLayout(LayoutKind.Sequential)] struct IO { public ulong ReadOperationCount,WriteOperationCount,OtherOperationCount,ReadTransferCount,WriteTransferCount,OtherTransferCount; }
    [StructLayout(LayoutKind.Sequential)] struct EXTENDED { public BASIC BasicLimitInformation; public IO IoInfo; public UIntPtr ProcessMemoryLimit,JobMemoryLimit,PeakProcessMemoryUsed,PeakJobMemoryUsed; }
    [StructLayout(LayoutKind.Sequential)] struct ACCOUNT { public long TotalUserTime,TotalKernelTime,ThisPeriodTotalUserTime,ThisPeriodTotalKernelTime; public uint TotalPageFaultCount,TotalProcesses,ActiveProcesses,TotalTerminatedProcesses; }
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr a,string n);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr h,int c,ref EXTENDED p,uint s);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr h,IntPtr p);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr h,uint e);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr h,int c,out ACCOUNT p,uint s,IntPtr ret);
    [DllImport("kernel32.dll",EntryPoint="QueryInformationJobObject",SetLastError=true)] static extern bool QueryIds(IntPtr h,int c,IntPtr p,uint s,IntPtr ret);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetNamedPipeInfo(IntPtr h,out uint flags,out uint outSize,out uint inSize,out uint maxInstances);
    [DllImport("kernel32.dll")] static extern IntPtr GetStdHandle(int n);
    [DllImport("kernel32.dll")] static extern uint GetFileType(IntPtr h);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern uint GetFinalPathNameByHandle(IntPtr h,StringBuilder b,uint n,uint f);
    const int Chunk=4096;
    const long HardLog=2*1024*1024,JournalCap=8*1024*1024;
    readonly object gate=new object(); readonly JavaScriptSerializer json=new JavaScriptSerializer();
    FileStream journal,stdout,stderr,initial; Process child; IntPtr job; string reason,error; long outBytes,errBytes; long soft; long start; string directory;
    int streamDone; uint pipeOut,pipeErr; string[] roots;
    static long Now(){ return (long)((decimal)Stopwatch.GetTimestamp()*1000000000m/Stopwatch.Frequency); }
    static void Need(bool b,string s){if(!b)throw new InvalidOperationException(s+" [Win32="+Marshal.GetLastWin32Error()+"]");}
    static bool Inside(string p,string r){p=Path.GetFullPath(p).TrimEnd('\\');r=Path.GetFullPath(r).TrimEnd('\\');return p.Equals(r,StringComparison.OrdinalIgnoreCase)||p.StartsWith(r+"\\",StringComparison.OrdinalIgnoreCase);}
    public static void ValidateOuterHandles(string[] roots){
        foreach(int n in new int[]{-11,-12}){IntPtr h=GetStdHandle(n);if(GetFileType(h)!=1)continue;
            StringBuilder b=new StringBuilder(32768);Need(GetFinalPathNameByHandle(h,b,(uint)b.Capacity,0)>0,"outer redirection path unavailable");
            string p=b.ToString();if(p.StartsWith("\\\\?\\"))p=p.Substring(4);
            foreach(string r in roots)Need(!Inside(p,r),"PowerShell stdout/stderr redirects into protected root: "+p);
        }
    }
    FileStream NewFile(string n){return new FileStream(Path.Combine(directory,n),FileMode.CreateNew,FileAccess.Write,FileShare.Read);}
    void Event(string name,object data){
        byte[] b=Encoding.UTF8.GetBytes(json.Serialize(new {event_name=name,ns=Now(),utc=DateTime.UtcNow.ToString("o"),data=data})+"\n");
        Need(journal.Length+b.Length<=JournalCap,"bounded launch journal exhausted");journal.Write(b,0,b.Length);journal.Flush();
    }
    uint PipeSize(Stream s){
        FileStream f=s as FileStream;Need(f!=null,"unsupported redirected pipe stream; HOLD");
        uint flags,a,b,c;Need(GetNamedPipeInfo(f.SafeFileHandle.DangerousGetHandle(),out flags,out a,out b,out c),"pipe capacity unavailable; HOLD");
        Need((ulong)a+b<=65536 && (ulong)a+b>0,"unregistered pipe capacity; HOLD");return a+b;
    }
    uint Active(){ACCOUNT a;Need(QueryInformationJobObject(job,1,out a,(uint)Marshal.SizeOf(typeof(ACCOUNT)),IntPtr.Zero),"job accounting");return a.ActiveProcesses;}
    object Members(){
        IntPtr b=Marshal.AllocHGlobal(8+4096*IntPtr.Size);
        try{Need(QueryIds(job,3,b,(uint)(8+4096*IntPtr.Size),IntPtr.Zero),"job process IDs");int n=Marshal.ReadInt32(b,4);Need(n>=0&&n<=4096,"bounded job IDs");
            var members=new List<object>();for(int i=0;i<n;i++){int pid=(int)Marshal.ReadIntPtr(b,8+i*IntPtr.Size);string name=null;try{name=Process.GetProcessById(pid).ProcessName;}catch(ArgumentException){}catch(InvalidOperationException){}members.Add(new {pid=pid,name=name});}return members;
        }finally{Marshal.FreeHGlobal(b);}
    }
    void Abort(string why){
        if(reason!=null)return;reason=why;
        Event("TERMINATE_OWNED_JOB",new {reason=why});
        Need(TerminateJobObject(job,91),"terminate owned job failed");
        long deadline=Now()+3000000000L;
        while(Active()!=0 && Now()<deadline)Thread.Sleep(5);
        Need(Active()==0,"owned process cleanup timed out");
    }
    void Read(Stream source,FileStream dest,bool isOut){
        byte[] buffer=new byte[Chunk];
        try {
            while(true){int n=source.Read(buffer,0,buffer.Length);if(n==0)break;
                lock(gate){long current=isOut?outBytes:errBytes;
                    if(reason==null && current+n>soft)Abort((isOut?"stdout":"stderr")+" soft byte ceiling exceeded");
                    // At most the soft limit + one in-flight chunk + the
                    // measured pipe capacity can have been produced by this
                    // stream. The 2MiB hard reservation is larger than that.
                    Need(current+n<=HardLog,"capture hard reserve violated; evidence invalid");
                    dest.Write(buffer,0,n);dest.Flush();if(isOut)outBytes+=n;else errBytes+=n;
                }
            }
        } catch(Exception ex){lock(gate){error=ex.ToString();try{Abort("capture reader failure");}catch(Exception e){error+="\n"+e;}}}
        finally{Interlocked.Increment(ref streamDone);}
    }
    static string Hash(string p){using(SHA256 h=SHA256.Create())using(FileStream f=File.OpenRead(p)){return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}}
    object CpuModules(){var list=new List<object>();foreach(ProcessModule m in Process.GetCurrentProcess().Modules){string n=m.ModuleName.ToLowerInvariant();Need(!n.Contains("vulkan")&&!n.Contains("cuda")&&!n.Contains("igvk")&&!n.Contains("nvoglv")&&!n.StartsWith("ggml"),"GPU/numerical library in launcher");list.Add(new {path=m.FileName,sha256=Hash(m.FileName)});}return list;}
    public int Run(string executable,string arguments,string dir,string[] protectedRoots,int seconds,long softBytes,long launcherBeginNs){
        start=launcherBeginNs;directory=Path.GetFullPath(dir);roots=protectedRoots;soft=softBytes;
        Need(seconds>0 && seconds<=1260 && soft>0 && soft<=1024*1024,"registered launcher ceilings");
        Need(0<=Now()-start && Now()-start<seconds*1000000000L,"prelaunch engineering deadline");
        ValidateOuterHandles(roots);foreach(string r in roots)Need(!Inside(directory,r)&&!Inside(r,directory),"external logs must be disjoint from protected roots");
        Need(!Directory.Exists(directory),"external log ownership already exists; no restart");Directory.CreateDirectory(directory);
        Thread ot=null,et=null;int code=-1;
        try {
            journal=NewFile("LAUNCH_EVENTS.jsonl");stdout=NewFile("CONTROLLER.stdout.log");stderr=NewFile("CONTROLLER.stderr.log");initial=NewFile("INITIAL.json");
            byte[] ib=Encoding.UTF8.GetBytes(json.Serialize(new {launcher_pid=Process.GetCurrentProcess().Id,owner_sid=System.Security.Principal.WindowsIdentity.GetCurrent().User.Value,directory=directory,executable=executable,arguments=arguments,protected_roots=roots,log_soft_bytes=soft,log_hard_bytes=HardLog,journal_hard_bytes=JournalCap,external_reserved_bytes=16*1024*1024,external_plus_export_reserved_bytes=32*1024*1024,created_ns=Now(),utc=DateTime.UtcNow.ToString("o"),ownership="exclusive CreateNew handles, FileShare.Read, job owns gated controller and descendants",cpu_modules=CpuModules()}));Need(ib.Length<=131072,"initial receipt cap");initial.Write(ib,0,ib.Length);initial.Flush();
            Event("LOG_FILES_CREATED",new {stdout_bytes=0,stderr_bytes=0});
            job=CreateJobObject(IntPtr.Zero,null);Need(job!=IntPtr.Zero,"job create");EXTENDED lim=new EXTENDED();lim.BasicLimitInformation.LimitFlags=0x2000;
            Need(SetInformationJobObject(job,9,ref lim,(uint)Marshal.SizeOf(typeof(EXTENDED))),"job kill-on-close");
            ProcessStartInfo psi=new ProcessStartInfo(executable,arguments);psi.UseShellExecute=false;psi.CreateNoWindow=true;
            psi.RedirectStandardOutput=true;psi.RedirectStandardError=true;psi.RedirectStandardInput=true;
            psi.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"]="1";psi.EnvironmentVariables["PYTHONUNBUFFERED"]="1";psi.EnvironmentVariables["PYTHONIOENCODING"]="utf-8";
            child=new Process();child.StartInfo=psi;Need(child.Start(),"controller start");
            // Its entry waits on LAUNCH_GO before importing execution code.
            Need(AssignProcessToJobObject(job,child.Handle),"job ownership; controller remains gated");
            pipeOut=PipeSize(child.StandardOutput.BaseStream);pipeErr=PipeSize(child.StandardError.BaseStream);
            Event("CONTROLLER_ASSIGNED_GATED",new {pid=child.Id,creation_utc=child.StartTime.ToUniversalTime().ToString("o"),stdout_pipe_capacity=pipeOut,stderr_pipe_capacity=pipeErr,chunk=Chunk});
            ot=new Thread(()=>Read(child.StandardOutput.BaseStream,stdout,true));et=new Thread(()=>Read(child.StandardError.BaseStream,stderr,false));ot.Start();et.Start();
            child.StandardInput.WriteLine("LAUNCH_GO");child.StandardInput.Flush();child.StandardInput.Close();Event("LAUNCH_GO_SENT",new {pid=child.Id});
            while(!child.WaitForExit(100)){
                lock(gate){
                    if(Now()-start>seconds*1000000000L)Abort("whole launcher engineering timeout");
                    if(Process.GetCurrentProcess().WorkingSet64>8L*1024*1024*1024)Abort("launcher RSS ceiling");
                    foreach(string p in Directory.GetFileSystemEntries(directory)){
                        string n=Path.GetFileName(p);if(n!="INITIAL.json"&&n!="LAUNCH_EVENTS.jsonl"&&n!="CONTROLLER.stdout.log"&&n!="CONTROLLER.stderr.log")Abort("unknown external log-area write: "+n);
                    }
                    Event("LOG_APPEND_OBSERVATION",new {stdout_bytes=outBytes,stderr_bytes=errBytes,active_processes=Active()});
                }
            }
            child.WaitForExit();code=child.ExitCode;
            lock(gate){Event("CONTROLLER_EXIT_OBSERVED",new {exit_code=code,remaining_job_members=Members()});}
            // Kernel job accounting/console cleanup can lag process-handle exit.
            // This is bounded post-exit cleanup, not repaired runtime coverage.
            long cleanupDeadline=Now()+3000000000L;
            while(Active()!=0 && Now()<cleanupDeadline)Thread.Sleep(5);
            lock(gate){if(Active()!=0)Abort("controller exit left owned descendants after3s cleanup");}
        }catch(Exception ex){error=ex.ToString();lock(gate){try{if(job!=IntPtr.Zero && child!=null)Abort("launcher exception");}catch(Exception e){error+="\n"+e;} if(child!=null && !child.HasExited){child.Kill();child.WaitForExit(3000);}}}
        finally {
            if(ot!=null && !ot.Join(3000))error=(error??"")+" stdout drain timeout";
            if(et!=null && !et.Join(3000))error=(error??"")+" stderr drain timeout";
            if(job!=IntPtr.Zero)CloseHandle(job);
            if(journal!=null){lock(gate){Event("LOG_CAPTURE_CLOSED",new {controller_pid=child==null?(int?)null:child.Id,controller_exit_code=code,reason=reason,error=error,stdout_bytes=outBytes,stderr_bytes=errBytes,readers_completed=streamDone});}}
            if(stdout!=null)stdout.Dispose();if(stderr!=null)stderr.Dispose();if(initial!=null)initial.Dispose();if(journal!=null)journal.Dispose();
        }
        var files=new List<object>();long bytes=0;
        foreach(string p in Directory.GetFiles(directory)){long n=new FileInfo(p).Length;bytes+=n;files.Add(new {name=Path.GetFileName(p),bytes=n,sha256=Hash(p)});}
        Need(bytes+131072<=16*1024*1024,"external total cap");
        if(Now()-start>seconds*1000000000L)reason=reason??"whole launcher budget exceeded through close";
        using(FileStream receipt=NewFile("CLOSED.json")){
            byte[] b=Encoding.UTF8.GetBytes(json.Serialize(new {status=reason==null&&error==null&&code==0?"CLOSED_SUCCESS":"FAILED",controller_pid=child==null?(int?)null:child.Id,controller_exit_code=code,stop_reason=reason,error=error,files=files,stdout_bytes=outBytes,stderr_bytes=errBytes,stdout_pipe_capacity=pipeOut,stderr_pipe_capacity=pipeErr,readers_completed=streamDone,external_actual_bytes_before_receipt=bytes,external_reserved_bytes=16*1024*1024,external_plus_export_reserved_bytes=32*1024*1024,engineering_ns=Now()-start,closed_utc=DateTime.UtcNow.ToString("o"),processes_owned_as_job=true,soft_limit_terminates_job_then_drains=true}));Need(b.Length<=131072,"closing receipt cap");receipt.Write(b,0,b.Length);
        }
        return reason==null&&error==null&&code==0?0:90;
    }
}

"""After rehydration, place bound executables/DLLs without replacing different bytes."""
import shutil
from close_base import HERE,ASSET,read,sha

def copy_verified(source,destination,expected):
    assert sha(source)==expected
    if destination.exists():assert sha(destination)==expected;return
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination);assert sha(destination)==expected

def main():
    build=read(HERE/'generated/C_BUILD_IDENTITY.json');dest=HERE/'generated/c-build/bin'
    for name,key in [('llama-cli.exe','frontend_sha256'),('llama-server.exe','server_sha256')]:copy_verified(HERE/'current-binaries'/name,dest/name,build[key])
    for name,h in read(HERE/'SOURCE_BINDINGS.json')['assets_pre']['runtime_dlls'].items():copy_verified(ASSET/'tools/llama-b10839'/name,dest/name,h)
    if (HERE/'generated/CROSS_BUILD_IDENTITY.json').exists():
        x=read(HERE/'generated/CROSS_BUILD_IDENTITY.json');xdest=HERE/'generated/x-build/bin'
        for name,key in [('llama-cli','frontend_sha256'),('llama-server','server_sha256')]:copy_verified(HERE/'current-binaries'/(name+'-cross.exe'),xdest/(name+'.exe'),x[key])
        for name,h in read(HERE/'SOURCE_BINDINGS.json')['assets_pre']['runtime_dlls'].items():copy_verified(ASSET/'tools/llama-b10839'/name,xdest/name,h)
    print('Exact private executables and bound published DLLs restored; weights remain in configured asset root. No inference.',flush=True)

if __name__=='__main__':main()

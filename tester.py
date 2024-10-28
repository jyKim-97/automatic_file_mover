import os
import time

SRC = "./test_src"
DST = "./test_dst"
FORMAT = ".avi"

DUR = 12
nstack = 1

def gen_files():
    global nstack
    
    while True:        
        with open(os.path.join(SRC, "test%d%s"%(nstack, FORMAT)), "w") as fp:
            fp.write("test")
            time.sleep(DUR)
            
        nstack += 1


if __name__=="__main__":
    gen_files()

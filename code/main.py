# -*- coding: utf-8 -*-
import sys
import os
#公共库
libpath = os.path.abspath("./lib")
sys.path.append(libpath)




def main(config_file):
    pass



if __name__ == "__main__":

    conf_file = None
    if  len(sys.argv) >= 2:
        conf_file = sys.argv[1]
    main(conf_file)

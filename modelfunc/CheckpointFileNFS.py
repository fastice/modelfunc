#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 10:07:12 2025

@author: ian
"""

from firedrake import CheckpointFile
import shutil
import tempfile
import os

class CheckpointFileNFS(CheckpointFile):
    '''
    This is a subclass of CheckpointFile designed to get around the problem of HDF not
    being able to write to NFS mounted filed systems by writing to an intermediate tmp file
    on the local file system. It will work for either NFS or regular file systems, incurring
    the unnecessary delay of file mv for the latter. On the other hand, its use makes the 
    code file system agnostic.
    '''
    def __init__(self, *args, tmpDir="/var/tmp", **kwargs):
        # Create a temporary file name in for /var/tmp
        if args[1] == 'r':
            self.tempFile = None
            super().__init__(*args, **kwargs)
            return
        #
        TF = tempfile.NamedTemporaryFile(dir="/var/tmp", delete=False)
        TF.close()
        self.tempFile = TF.name
        self.originalFile = args[0]
        #
        if args[1] == 'a':
            if os.path.exists(self.originalFile):
                shutil.copy(self.originalFile, self.tempFile)
        #
        # Make a link so file visible during along run
        self.removeOriginal()
        print(f'linking {self.tempFile} {self.originalFile}')
        os.symlink(self.tempFile, self.originalFile)
        # modify args to use the tmp file
        newArgs = [self.tempFile, *args[1:]]
        # CheckpointFile init
        super().__init__(*newArgs, **kwargs)   

    def removeOriginal(self):
        if os.path.exists(self.originalFile):
            print(f'Removing {self.originalFile}')
            os.remove(self.originalFile)
            
    def close(self, *args, **kwargs):
        # Call the original close method
        super().close(*args, **kwargs)
        # move the tmp file to the desired location
        if self.tempFile is not None:
            self.removeOriginal()
            shutil.move(self.tempFile, self.originalFile)
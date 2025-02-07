#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 10:07:12 2025

@author: ian
"""

from firedrake import CheckpointFile
import shutil
import tempfile

class CheckpointFileNFS(CheckpointFile):
    '''
    This is a subclass of CheckpointFile designed to get around the problem of HDF not
    being able to write to NFS mounted filed systems by writing to an intermediate tmp file
    on the local file system. It will work for either NFS or regular file systems, incurring
    the unnecessary delay of file mv for the latter. On the other hand, its use makes the 
    code file system agnostic.
    '''
    def __init__(self, *args, tmpDir="/var/tmp", **kwargs):
        # Create a temporary file name in for /far/tmp
        TF = tempfile.NamedTemporaryFile(dir="/var/tmp", delete=False)  # Set delete=False if you want to keep it
        TF.close()
        #
        self.tempFile = TF.name
        newArgs = [self.tempFile, *args[1:]]
        # CheckpointFile init
        super().__init__(*newArgs, **kwargs)
        # save the original name
        self.originalFile = args[0]

    def close(self, *args, **kwargs):
        # Call the original close method
        super().close(*args, **kwargs)
        # move the tmp file to the desired location
        shutil.move(self.tempFile, self.originalFile)
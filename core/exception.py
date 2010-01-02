# Created By: Virgil Dupras
# Created On: 2008-02-15
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from __future__ import unicode_literals

class FileFormatError(Exception):
    pass

class FileLoadError(Exception):
    pass

class DuplicateAccountNameError(Exception):
    pass

class OperationAborted(Exception):
    message = '' # It's redundant with __init__, but it's to get around deprecation warnings
    
    def __init__(self, message=''):
        Exception.__init__(self)
        self.message = message
    

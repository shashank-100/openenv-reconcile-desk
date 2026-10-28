"""Protected, data-only verifier; never imports or executes model files."""
import csv
import io
import os
import re
import stat
from decimal import Decimal
from .tasks import HEADER
MONEY=re.compile(r'-?(?:0|[1-9][0-9]*)\.[0-9]{2}\Z')

def grade_bytes(data,expected):
    try:
        rows=list(csv.reader(io.StringIO(data.decode('utf-8')),strict=True))
        if not rows or rows[0]!=HEADER: return False,'Header must exactly match the required columns.'
        if len(rows)!=len(expected)+1: return False,'Wrong number of supplier rows.'
        for index,(actual,wanted) in enumerate(zip(rows[1:],expected),1):
            if len(actual)!=5 or actual[0]!=wanted[0]: return False,f'Wrong supplier or column count on row {index}.'
            if not all(MONEY.fullmatch(v) for v in actual[1:]): return False,f'Invalid money format on row {index}.'
            if any(Decimal(a)!=Decimal(b) for a,b in zip(actual[1:],wanted[1:])):
                return False,f'Spending values do not reconcile on row {index}.'
        return True,'All supplier totals reconcile.'
    except (ValueError,UnicodeError,csv.Error,ArithmeticError):
        return False,'Output is not a valid UTF-8 results CSV.'

def grade_file(workspace,expected):
    fd=None;directory=None
    try:
        directory=os.open(workspace,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        fd=os.open('supplier_spend.csv',os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW,dir_fd=directory)
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size>65536 or info.st_nlink!=1:
            return False,'Output must be a regular file smaller than 64 KiB.'
        data=os.read(fd,65537)
        return grade_bytes(data,expected)
    except OSError:
        return False,'Could not safely read supplier_spend.csv.'
    finally:
        if fd is not None: os.close(fd)
        if directory is not None: os.close(directory)

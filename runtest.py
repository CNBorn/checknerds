import urllib
import sys

ret = 0
for line in urllib.urlopen('http://localhost:8080/test?format=plain'):
    print line,
    if 'FAILED (' in line:
        ret = 1
        
sys.exit(ret)

# --------- upload_file.py ----------------
# upload binary file with pycurl by http post
import pycurl
c = pycurl.Curl()
c.setopt(c.POST, 1)
c.setopt(c.URL, "http://127.0.0.1:8000/receive/")
c.setopt(c.HTTPPOST, [("file1", (c.FORM_FILE, "c:\\tmp\\download\\test.jpg"))])
#c.setopt(c.VERBOSE, 1)
c.perform()
c.close()
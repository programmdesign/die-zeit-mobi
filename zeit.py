import os
import ConfigParser
import socket, urllib
import time
from mechanize import Browser

from smtplib import SMTP
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

class MailEntity:
        def __init__(self, empfaenger, absender, smtp_server, smtp_user, smtp_passwort):
                self.EMPFAENGER = empfaenger
                self.ABSENDER = absender
                self.SMTP_SERVER = smtp_server
                self.SMTP_USER = smtp_user
                self.SMTP_PASSWORT = smtp_passwort
                self.SMTP_EMFAENGER = empfaenger
				
        def sendAttachment(self, file):
        	msg = MIMEMultipart()
        	msg['Subject'] = os.path.basename(file) 
        	msg['From'] = self.ABSENDER
        	msg['To'] = self.EMPFAENGER

        	part = MIMEBase('application', "octet-stream")
        	part.set_payload(open(file, "rb").read())
        	Encoders.encode_base64(part)
        	part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file))
        	msg.attach(part)				
        		
        	smtp = SMTP()
        	smtp.connect(self.SMTP_SERVER, 25)				
        	smtp.login(self.SMTP_USER, self.SMTP_PASSWORT)
        	smtp.sendmail(self.ABSENDER, self.EMPFAENGER, msg.as_string())
        	
        	print 'E-Mail erfolgreich an "%s" gesendet\n' % self.EMPFAENGER
        	
        	if os.path.exists(file):
        		os.remove(file)
        		print "Datei %s wurde geloescht\n" % file


class ZeitEntity:
        config = ConfigParser.RawConfigParser()
        config.read('./zeit.cfg')
        ZEIT_URL = config.get('Zeit', 'URL')

        def __init__(self, username, password):
                self.username = username
                self.password = password

                socket.setdefaulttimeout(60)
                self.browser = Browser()
			
        def fetchMobiLinks(self):
                MobiLinks = []

                for recordingLink in self.browser.links(url_regex=".*die_zeit-abo-mobi.*"):
		      MobiLinks.append(recordingLink.absolute_url)
		      print "Download-Link: %s\n" % recordingLink.absolute_url
                return list(set(MobiLinks))

        def initialiseLogin(self):
                self.browser.open(self.ZEIT_URL)
                self.browser.select_form(nr=2)
                self.browser["name"] = self.username
                self.browser["pass"] = self.password
                self.browser.submit()			

class ZeitDownloadWorker:
        """
        Inspired by: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/83208
        """

        def __init__(self, pUrl, pDdirectory):
				self.dnldUrl = pUrl
				self.download_directory = pDdirectory
				
        def download(self):
                myUrlclass = urllib.FancyURLopener()
                socket.setdefaulttimeout(60)
                webPage = myUrlclass.open(self.dnldUrl)

                try:
		      contentDisposition = webPage.headers['Content-Disposition']
		      filename = contentDisposition.split("filename=")[1]
                except:
		      filename = self.dnldUrl.split("/")
		      filename = filename[len(filename)-1]
				
                webPage.close()
                self.originalFilename = filename
                filename = filename.replace('"', '')
                				
                if os.path.exists(filename):
		      os.remove(self.download_directory + filename)
                
                urllib.urlretrieve(self.dnldUrl, self.download_directory + filename)
                				
                print 'Download der Datei "%s"  abgeschlossen\n' % (self.download_directory + filename)
                
                return self.download_directory + filename				

class ZeitDownloader:
        def readConfiguration(self):
                config = ConfigParser.RawConfigParser()
                config.read('./zeit.cfg')

                self.ZEIT_USERNAME = config.get('Zeit', 'Benutzername')
                self.ZEIT_PASSWORD = config.get('Zeit', 'Passwort')
                self.DOWNLOAD_DIRECTORY = os.path.normpath(config.get('System', 'Zielverzeichnis')) + os.sep
                self.EMPFAENGER = config.get('EMail', 'Empfaenger')
                self.ABSENDER = config.get('EMail', 'Absender')
                self.SMTP_SERVER = config.get('EMail', 'SMTP_Server')
                self.SMTP_USER = config.get('EMail', 'SMTP_User')
                self.SMTP_PASSWORT = config.get('EMail', 'SMTP_Passwort')
				
        def doDownload(self):
        	zE = ZeitEntity(self.ZEIT_USERNAME, self.ZEIT_PASSWORD)
        	zE.initialiseLogin()
        	dlLinks = zE.fetchMobiLinks()
        	for link in dlLinks:
        			downloader = ZeitDownloadWorker(link, self.DOWNLOAD_DIRECTORY)
        			file_complete = downloader.download()
        			mE = MailEntity(self.EMPFAENGER,self.ABSENDER, self.SMTP_SERVER, self.SMTP_USER, self.SMTP_PASSWORT)
        			mE.sendAttachment(file_complete)
				
if __name__ == "__main__":

        print time.strftime("%d.%m.%Y %H:%M:%S")
        downloader = ZeitDownloader()
        downloader.readConfiguration()
        downloader.doDownload()
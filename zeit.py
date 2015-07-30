# -*- coding: utf-8 -*-

import os
import time
import settings
import tempfile

import requests
import smtplib

from requests.auth import HTTPBasicAuth
from os.path import basename
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Zeit:

    def __init__(self):

        # Initialize selenium browser
        self.browser = webdriver.PhantomJS(settings.PHANTOMJS_BINARY)


    def login(self):
        try:
            self.browser.get(settings.URL)
            try:
                element = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))
                )
            finally:
                self.browser.find_element_by_id('login_email').send_keys(settings.USER)
                self.browser.find_element_by_id('login_password').send_keys(settings.PASSWORD)
                self.browser.find_element_by_xpath("//input[@type='submit']").click()
        except Exception as e:
            return False

        print "Logged in to: {0}.".format(settings.URL)
        return True

    def get_mobi(self):

        try:
            element = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, settings.MOBI_LINK_TEXT))
            )
        finally:
            mobi_link = self.browser.find_element_by_link_text(settings.MOBI_LINK_TEXT).get_attribute("href")
            print "Downloading: {0}".format(mobi_link)

            local_filename = "die_zeit.mobi"
            r = requests.get(mobi_link, stream=True, auth=HTTPBasicAuth(settings.USER, settings.PASSWORD))
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
        return local_filename


    def send_mobi(self, file_name):

        print "Sending file to: {0}.".format(settings.EMAIL_TO)

        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = COMMASPACE.join(settings.EMAIL_TO)
        msg['Subject'] =settings.EMAIL_SUBJECT

        with open(file_name, "rb") as f:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(file_name)))
            msg.attach(part)

        smtp = smtplib.SMTP(settings.SMTP_SERVER)
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.EMAIL_FROM, settings.EMAIL_TO, msg.as_string())
        smtp.close()

        print 'Email successfully sent!'

       	if os.path.exists(file_name):
            os.remove(file_name)
            print "File {0} deleted.".format(file_name)


if __name__ == "__main__":

    print time.strftime("%d.%m.%Y %H:%M:%S")

    zeit = Zeit()

    try:
    	zeit.login()
    	file_name = zeit.get_mobi()
    	zeit.send_mobi(file_name)
    except Exception as e:
    	print "Error {0}".format(e)

    zeit.browser.close()

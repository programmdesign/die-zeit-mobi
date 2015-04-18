# -*- coding: utf-8 -*-

import os
import time
import settings
import tempfile

import requests
import smtplib

from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Zeit:

    def __init__(self):

        # Initialize selenium browser
        self.browser = webdriver.PhantomJS(settings.PHATOMJS_BINARY)


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
                    EC.presence_of_element_located((By.ID, settings.MOBI_LINK_ID))
            )
        finally:
            mobi_link = self.browser.find_element_by_id(settings.MOBI_LINK_ID).get_attribute("href")
            print "Downloading: {0}".format(mobi_link)

            local_filename = "die_zeit.mobi"
            r = requests.get(mobi_link, stream=True)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
        return local_filename


    def send_mobi(self, file_name):

        print "Sending file to: {0}.".format(settings.EMAIL_TO)

        msg = MIMEMultipart(
                From=settings.EMAIL_FROM,
                To=COMMASPACE.join(settings.EMAIL_TO),
                Date=formatdate(localtime=True),
                Subject=settings.EMAIL_SUBJECT,
            )
        msg.attach(MIMEText(settings.EMAIL_TEXT))

        with open(file_name, "rb") as f:
                msg.attach(MIMEApplication(
                f.read(),
                Content_Disposition='attachment; filename="{0}"'.format(basename(file_name))
        ))

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

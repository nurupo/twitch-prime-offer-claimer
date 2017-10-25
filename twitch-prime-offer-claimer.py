#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2017 by Maxim Biro <nurupo.contributions@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import base64
import hashlib
import json
import os
import requests
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import config as Config
import cookies as Cookies

EMAIL_HTML_HEAD = '{}\n{}\n{}\n'.format(
                           Config.EMAIL_BOUNDARY,
                           'Content-Type: text/html; charset=utf-8',
                           'Content-Transfer-Encoding: 8bit')

HTML_HEAD = '{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n'.format(
                           '<!doctype html>',
                           '<html>',
                           '<head>',
                           '<meta name="viewport" content="width=device-width" />',
                           '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />',
                           '<title>Twitch Prime Offer Claimer Report</title>',
                           '</head>',
                           '<body>')

# Doesn't include the ending boundary since more sections might follow
HTML_TAIL = '{}\n{}\n'.format(
                           '</body>',
                           '</html>')

def exit_with_error(message):
  if Config.GENERATE_REPORT:
    if Config.REPORT_IN_EMAIL_FORMAT:
      print(EMAIL_HTML_HEAD, file=sys.stderr)

    print(HTML_HEAD, file=sys.stderr)
    print('{}\n{}\n{}\n'.format('<p style="color:red;"><b>', message, '</b></p>'), file=sys.stderr)
    print(HTML_TAIL, file=sys.stderr)

    if Config.REPORT_IN_EMAIL_FORMAT:
      print('{}--'.format(Config.EMAIL_BOUNDARY), file=sys.stderr)
  else:
    print(message, file=sys.stderr)

  sys.exit(1)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
for arg in Config.CHROME_EXTRA_ARGS:
  chrome_options.add_argument(arg)
chrome_options.binary_location = Config.CHROME_PATH

driver = webdriver.Chrome(executable_path=Config.CHROMEDRIVER_PATH, chrome_options=chrome_options)
try:
  authentication_tries = 0
  authenticated = False
  while not authenticated:
    try:
      authentication_tries += 1

      # Using cookies instead of authenticating with username/password through the
      # login form because the login form has captcha.
      # Selenium requires getting a page before any cookies can be added. The About
      # page seems to be rather low-traffic, so we use it.
      driver.get('https://www.twitch.tv/p/about')
      driver.delete_all_cookies()
      for cookie in Cookies.COOKIES:
        driver.add_cookie(cookie)

      # Authenticate!
      driver.get('https://www.twitch.tv/')

      # Make sure we sucessfully authenticated. There should be our username
      # displayed
      try:
        driver.find_element_by_css_selector('#user_display_name')
        authenticated = True
      except:
        if authentication_tries < Config.MAX_AUTHENTICATION_TRIES:
          continue
        driver.quit()
        exit_with_error("Error: Couldn't authenticate. Make sure your cookies didn't expire -- update the cookies and try again.")
    except:
      if authentication_tries < Config.MAX_AUTHENTICATION_TRIES:
        continue
      else:
        raise

  # Click on the Twitch Prime button to trigger JavaScript code to load offer
  # information
  driver.find_element_by_css_selector('button.top-nav__prime-link').send_keys(Keys.RETURN)

  # Iterate over offers, collecting information about them and claiming the
  # claimable ones
  offer_list = driver.find_element_by_css_selector('div.offer-list__container')
  offers = []
  for offer in offer_list.find_elements_by_css_selector('div.offer-item'):
    heading = None
    try:
      heading = offer.find_element_by_css_selector('h4').text
    except:
      driver.quit()
      exit_with_error("Error: Couldn't find any headings in an offer")

    image = None
    try:
      image = offer.find_element_by_css_selector('figure.offer-item__img').find_element_by_css_selector('img').get_attribute('src')
    except:
      pass
    if image == None:
      driver.quit()
      exit_with_error("Error: Couldn't find an image in {} offer".format(heading))

    descriptions = []
    for description in offer.find_elements_by_css_selector('p:not(.hint)'):
      if len(description.get_attribute('innerHTML')) > 0:
        descriptions.append(description.get_attribute('innerHTML'))
    if len(descriptions) == 0:
      driver.quit()
      exit_with_error("Error: Couldn't find any descriptions in {} offer".format(heading))

    claim = None
    for button in offer.find_elements_by_css_selector('.button'):
      # I hate to rely on the exact wording, but there doesn't seem to be a
      # better way of doing this, the button attributes are not distinctive
      # enough
      if button.text == 'Claim Offer':
        button.send_keys(Keys.RETURN)
        claim = 'The offer was claimed'
      elif button.text == 'Get Code':
        button.send_keys(Keys.RETURN)
        copy_button = offer.find_element_by_css_selector('button.copy-btn')
        # The data-clipboard-text attribute seems to appear only after some
        # time passes, likely set by JavaScript triggered by clicking on the
        # button
        while copy_button.get_attribute('data-clipboard-text') == None:
          time.sleep(0.2)
        code = copy_button.get_attribute('data-clipboard-text')
        claim = 'Code: {}'.format(code)
      elif button.text == 'Learn More':
        link = button.get_attribute('href')
        claim = 'Visit: {}'.format(link)
    if claim == None:
      driver.quit()
      exit_with_error("Error: Couldn't claim the offer")

    offers.append({'heading':heading, 'image':image, 'descriptions':descriptions, 'claim':claim})

  driver.quit()
except SystemExit:
  raise
except Exception as e:
  driver.quit()
  exit_with_error('Error:\n{}'.format(str(e)))

try:
  # Don't produce a report if it's no different from the last report
  if Config.GENERATE_REPORT and Config.GENERATE_REPORT_ONLY_ON_CHANGE:
    sha256 = hashlib.sha256(json.dumps(offers, sort_keys=True).encode('utf-8')).hexdigest()
    try:
      hash_file = open('hash.sha256', 'r')
      read_hash = hash_file.read()
      hash_file.close()
      if sha256 == read_hash:
        sys.exit(0)
    except SystemExit:
      raise
    except:
      pass

    with open('hash.sha256', 'w+') as hash_file:
      hash_file.write(sha256)

  # Generate a html report, either as a regular html page or as an email.
  # The difference is that for email we generate email headers and print images
  # differently, because for god knows what reason, inlining base64 images in
  # <img> tag is not allowed in emails, you have to jump through the hoops of
  # creating a multipart email, with each image being a separate part, and
  # referencing images in your html text using content ids. This is madness.
  if Config.GENERATE_REPORT:
    report = ''
    if Config.REPORT_IN_EMAIL_FORMAT:
      report += '{}\n'.format(EMAIL_HTML_HEAD)
    report += HTML_HEAD
    report += '<h1>Twitch Prime Offer Claimer Report</h1>\n'
    i = 0
    for offer in offers:
      report += '<h2>{}</h2>\n'.format(offer['heading'])
      if Config.INCLUDE_IMAGES_IN_REPORT:
        if Config.REPORT_IN_EMAIL_FORMAT:
          report += '<img src="cid:{}">\n'.format(i)
        else:
          report += '<img src="data:image/png;base64, {}" />\n'.format(base64.b64encode(requests.get(offer['image']).content).decode('ascii'))
      report += '<h3>Claim</h3>\n'
      report += '{}\n'.format(offer['claim'])
      report += '<h3>Description</h3>\n'
      for description in offer['descriptions']:
        report += '<p>{}</p>\n'.format(description)
      i = i + 1
    report += HTML_TAIL
    if Config.REPORT_IN_EMAIL_FORMAT:
      if Config.INCLUDE_IMAGES_IN_REPORT:
        i = 0
        for offer in offers:
          if offer['image'] != None:
            report += '{}\n'.format(Config.EMAIL_BOUNDARY)
            report += 'Content-Type: image/png; name="{}.png"\n'.format(i)
            report += 'Content-Disposition: inline; filename="{}.png"\n'.format(i)
            report += 'Content-Transfer-Encoding: base64\n'
            report += 'Content-ID: <{}>\n'.format(i)
            report += '\n'
            report += base64.b64encode(requests.get(offer['image']).content).decode('ascii')
            report += '\n'
          i = i + 1
      report += '{}--'.format(Config.EMAIL_BOUNDARY)
    print(report)
except SystemExit:
  raise
except Exception as e:
  exit_with_error('Error:\n{}'.format(str(e)))

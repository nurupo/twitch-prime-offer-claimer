CHROME_PATH = '/usr/bin/chromium'

CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'

# Any extra arguments you want to call Chrome with.
# --no-sandbox is quite dangerous security-wise, I use it only beacause Chrome
# doesn't work in Docker without it.
CHROME_EXTRA_ARGS = ['--no-sandbox']

# Write a html report to stdout.
GENERATE_REPORT = True

# Whether to generate an email-friendly (True) or a browser-friendly (False)
# html report. Email-friendly report contains email headers and other stuff,
# and it also requires you to specify the correct Content-Type and the boundary,
# which is already done for you in the default cron file.
REPORT_IN_EMAIL_FORMAT = True

# Boundary between each email part. This default should work just fine.
EMAIL_BOUNDARY = '--uUz_cCeh8ZzHgF4B5qvz2_WRszYFmr8jHI1gCLC1BxTNQs4Uagd_A_VgaMSPQxEp'

# Include images in the report.
INCLUDE_IMAGES_IN_REPORT = True

# Generate a report only if it's different from the last report.
GENERATE_REPORT_ONLY_ON_CHANGE = True

# PROJECT DISCONTINUED
Unfortunetly I have lost the interest in the project after the October 2017 Twitch website redesign, which would require me to rewrite most of the code and at which point I was frequenting Twitch enough as not to need this script anymore.
The project was written mostly for myself and it had 0 stars on GitHub for over a year, so since I don't need it anymore and no one else seems to be using it, it doesn't make sense to support it.
If it turns out that more people are interested in this project than I have thought, I might bring the project back.

The script doesn't work against the current Twitch website, it's coded against the website before the October 2017 redesign.

# Twitch Prime Offer Claimer
A script that claims Twitch Prime offers. Cron it and you won't miss on any Twitch Prime offers.

## Motivation
Twitch Prime offers free games, which you can claim in order to have them added to your game library.
The issue is that the offers are available for a limited time, generally for several days, so it's easy to miss them if you don't visit Twitch website often to claim them.
Well, what do we do in situations like this? Yes, we script it.

## How it works
Using Selenium, the script interacts with a headless Chromium instance.
It sets your cookies, opens Twitch website, pulls up the Twitch Prime offers panel and clicks on each offer, claiming right away the claimable ones (e.g. a free game), and recording codes for code redeemable ones.
At the end it produces [an HTML report of all offers](https://jsfiddle.net/949dLjm8/).
If an error occurs, the script will either note it in the HTML report in red, or will generate an error message instead of the HTML report.
Because the script is very tied to the website's HTML, any slight change in the website design might break the script, though fixing it should be trivial.

## Usage
Chromium has many Xorg dependencies, so in order to not sprinkle our headless Linux system with Xorg, we run the script in a Docker container.

[Get Docker on your system](https://docs.docker.com/engine/installation/linux/).
Note that some versions of
[Debian](https://packages.debian.org/search?suite=all&searchon=names&keywords=docker.io)
and [Ubuntu](http://packages.ubuntu.com/search?suite=all&searchon=names&keywords=docker.io)
have it in their package repository.

Create a directory accessible only by root
```sh
mkdir /var/lib/twitch-prime-offer-claimer
chown root:root /var/lib/twitch-prime-offer-claimer
chmod 700 /var/lib/twitch-prime-offer-claimer
```

Copy the scripts from this repository in there
```sh
cp *.py /var/lib/twitch-prime-offer-claimer
cp Dockerfile /var/lib/twitch-prime-offer-claimer
```

Provide values for the cookies in `/var/lib/twitch-prime-offer-claimer/cookies.py` file.
The cookies should be updated periodically as they do expire.
It's not known yet for how long they are valid, Twitch website doesn't set an explicit expiration date for them.

Build Docker image
```
docker build -t twitch-prime-offer-claimer /var/lib/twitch-prime-offer-claimer/
```

Setup cronjob
```
cp etc/cron.d/twitch-prime-offer-claimer /etc/cron.d/twitch-prime-offer-claimer
service cron reload
```

That's it.
Once a day, at midnight, cron would run the script in a Docker container, generating an html report of how successful (or unsuccessful) the script ran.
By default, the report would be generated only if it differs from the last report, so you should receive reports only on changes.
Also, by default, the html report would be in email format.
It might be worth configuring cron to email the html report.

# License
MIT

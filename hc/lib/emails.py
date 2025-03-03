import smtplib
from threading import Thread
import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string as render


class EmailThread(Thread):
    MAX_TRIES = 3

    def __init__(self, message):
        Thread.__init__(self)
        self.message = message

    def run(self):
        for attempt in range(0, self.MAX_TRIES):
            try:
                # Make sure each retry creates a new connection:
                self.message.connection = None
                self.message.send()
                # No exception--great, return from the retry loop
                return
            except smtplib.SMTPServerDisconnected as e:
                if attempt + 1 == self.MAX_TRIES:
                    # This was the last attempt and it failed:
                    # re-raise the exception
                    raise e

                # Wait 1s before retrying
                time.sleep(1)


def send(name, to, ctx, headers={}, from_email=None):
    ctx["SITE_ROOT"] = settings.SITE_ROOT

    subject = render("emails/%s-subject.html" % name, ctx).strip()
    body = render("emails/%s-body-text.html" % name, ctx)
    html = render("emails/%s-body-html.html" % name, ctx)

    msg = EmailMultiAlternatives(subject, body, to=(to,), headers=headers)
    msg.attach_alternative(html, "text/html")
    if from_email:
        msg.from_email = from_email

    t = EmailThread(msg)
    if hasattr(settings, "BLOCKING_EMAILS"):
        # In tests, we send emails synchronously
        # so we can inspect the outgoing messages
        t.run()
    else:
        # Outside tests, we send emails on thread,
        # so there is no delay for the user.
        t.start()


def login(to, ctx):
    send("login", to, ctx)


def transfer_request(to, ctx):
    send("transfer-request", to, ctx)


def alert(to, ctx, headers={}):
    send("alert", to, ctx, headers=headers)


def verify_email(to, ctx):
    send("verify-email", to, ctx)


def report(to, ctx, headers={}):
    send("report", to, ctx, headers=headers)


def deletion_notice(to, ctx, headers={}):
    send("deletion-notice", to, ctx, headers=headers)


def sms_limit(to, ctx):
    send("sms-limit", to, ctx)


def call_limit(to, ctx):
    send("phone-call-limit", to, ctx)


def sudo_code(to, ctx):
    send("sudo-code", to, ctx)

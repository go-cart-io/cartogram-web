import string
import random
import validate_email
import smtplib
import email.mime.text
import socket

from flask import request, session, flash, redirect, render_template, url_for
from views import tracking, custom_captcha
import settings

# This function returns a random string containg lowercase letters and numbers that is *length* characters long.
# This is used to generate the unique string key associated with each cartogram.
def get_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(length))

def contact():
    if request.method == 'GET':
        csrf_token = get_random_string(50)
        session['csrf_token'] = csrf_token

        captcha = custom_captcha.generate_captcha()
        session['captcha_hashed'] = captcha['captcha_hashed']

        return render_template('contact.html', page_active='contact', name='', message='', email_address='', subject='',
                               csrf_token=csrf_token, tracking=tracking.determine_tracking_action(request),
                               captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])
    else:

        name = request.form.get('name', '')
        email_address = request.form.get('email', '')
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        csrf = request.form.get('csrftoken', '')
        captcha = custom_captcha.generate_captcha()

        if 'csrf_token' not in session:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Invalid CSRF token.', 'danger')
            csrf_token = get_random_string(50)
            session['csrf_token'] = csrf_token
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        if session['csrf_token'] != csrf or len(session['csrf_token'].strip()) < 1:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Invalid CSRF token.', 'danger')
            csrf_token = get_random_string(50)
            session['csrf_token'] = csrf_token
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        csrf_token = get_random_string(50)
        session['csrf_token'] = csrf_token

        if len(name.strip()) < 1 or len(subject.strip()) < 1 or len(message.strip()) < 1:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('You must fill out all of the form fields', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        if not validate_email.validate_email(email_address):
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('You must enter a valid email address.', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        if 'captcha_hashed' not in session:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Please retry completing the CAPTCHA.', 'danger')
            csrf_token = get_random_string(50)
            session['csrf_token'] = csrf_token
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'],
                                   captcha_audio=captcha['captcha_audio'])

        if not custom_captcha.validate_captcha(request.form.get('captcha', ''), session['captcha_hashed']):
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Please retry completing the CAPTCHA.', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        # Escape all of the variables:
        name = name.replace('<', '&lt;')
        name = name.replace('>', '&gt;')

        subject = subject.replace('<', '&lt;')
        subject = subject.replace('>', '&gt;')

        message = message.replace('<', '&lt;')
        message = message.replace('>', '&gt;')

        # Generate the message body
        message_body = """A message was received from the go-cart.io contact form.

Name:       {}
Email:      {}
Subject:    {}

Message:

{}""".format(name, email_address, subject, message)

        mime_message = email.mime.text.MIMEText(message_body)
        mime_message['Subject'] = 'go-cart.io Contact Form: ' + subject
        mime_message['From'] = settings.SMTP_FROM_EMAIL
        mime_message['To'] = settings.SMTP_DESTINATION

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:

                if settings.SMTP_AUTHENTICATION_REQUIRED:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                smtp.send_message(mime_message)

                smtp.quit()
        # For some reason connect doesn't catch the socket error
        # *sigh*
        except (smtplib.SMTPException, socket.gaierror):
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('There was an error sending your message.', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        session['captcha_hashed'] = ''
        flash('Your message was successfully sent.', 'success')
        return redirect(url_for('contact'))
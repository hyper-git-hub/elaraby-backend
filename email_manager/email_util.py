from backend import local_settings
from .models import *
from django.core.mail import EmailMultiAlternatives
import traceback


def extractTLDfromHost(body_txt, find_val, act, request):
    if request:
        import tldextract
        ext = tldextract.extract(request.session["HOSTNAME"])
        if ext.tld:
            if act == "email_sender":
                parentdomain_url = '.'.join(ext[1:3])  # parentdomainurl.tld
                body_txt = body_txt.replace(find_val, parentdomain_url)
        else:
            body_txt = body_txt.replace(find_val, "microsoft.com")
    else:
        body_txt = body_txt.replace(find_val, "hypernymbiz.com")
    return body_txt


def evariableReplace(txt, varDic):
    for k, v in varDic.items():
        txt = txt.replace(k, v)
    return txt


from hypernet.utils import async_util


@async_util
def extended_email_with_title(title, to_list=[], cc_list=[], bcc_list=[], email_words_dict={}, request='',
                              attachment=[]):
    try:
        email_words_dict = dict(email_words_dict)
        template_obj = Template.objects.get(email_key=title)
        if template_obj.is_active:
            if not to_list:
                to_list = str(template_obj.to_list).split(',')
            if not cc_list:
                cc_list = str(template_obj.cc_list).split(',')
            if not bcc_list:
                bcc_list = str(template_obj.bcc_list).split(',')

            body = str(template_obj.email_body)

            from_email = extractTLDfromHost(str(template_obj.from_email), '[DOMAIN]', 'email_sender', request)

            subject = template_obj.subject

            #subject = evariableReplace(subject, email_words_dict)
            #email_text = evariableReplace(body, email_words_dict)
            body = evariableReplace(body, email_words_dict)
            # from_email = 'support@dincloud.com'
            msg = EmailMultiAlternatives(subject, body, from_email, to=to_list, cc=cc_list, bcc=bcc_list)
            if attachment:
                msg.attach(attachment['title'], attachment['file'], attachment['type'])

            #msg.content_subtype = "text/plain"
            msg.content_subtype = "html"
            msg.send()
            print(msg)
        if email_words_dict:
            template_obj.placeholders = '\n'.join([k for k in email_words_dict.keys()])
            template_obj.save()

    except Exception as e:
        print(traceback.print_exc(5))
        print(str(e))



def construct_url(url, id):
    url = url + '/' + id
    return str(url)


def create_default_email_template():
    try:
        email_body_text = '<body style="background:#f9f9f9;"><div style="max-width:600px; margin:auto; padding:30px; background:#ffffff; margin-top:30px;">' \
                     '<table style="width:100%;"><tr><td align="center" style="border-bottom: 1px solid #eee; padding-bottom: 20px;">' \
                     '<img src="http://www.hypernymbiz.com/img/hypernym-logo-color.png" height="80" />' \
                     '</td></tr><tr><td > <div style="font-family:Arial; font-size:24px; color:#b8a000; padding-top:50px; padding-bottom:20px; text-align:center;">Welcome to Hypernet</div>' \
                     '</td></tr><tr><td> <div style="font-family:Arial; font-size:14px; color:#555; padding-top:20px; padding-bottom:20px; text-align:center;">{text}'\
                     '<a href="http://{1}/reset_password/?reset_password={0}"> Click here to proceed.</a></div></td></tr></table></div></body>'

        email_body_text = evariableReplace(email_body_text, {'{1}':local_settings.ACTIVE_FRONT_END})

        email_template = Template()
        email_template.email_key = "create_user"
        email_template.subject = "Complete Signup to your Hypernymbiz Account"
        email_template.from_email = "no_reply@hypernymbiz.com"
        email_template.email_body = email_body_text
        email_template.save()
    except:
        traceback.print_exc()

##Email Manager V 1.0
Email manager app for managing email templates.

####install requirements
 ```
pip install -r requirements.txt
```
- Migrate Database
```
add email_manager to installed apps in settings.
python manage.py migrate email_manager

```

####Usage:
```
1- Add Email template object through Django Admin.
    - Give an identification key to an email template.
    - Add subject with a specified keyword to be replaced.
    - Add description similarly with replacable keywords.
    - Add comma seperated to_list, cc & bcc.
    - Add title and select email type.
    -save this template.
```
```
2- To Send email use function:
    extended_email_with_title(*title, to_list=[], cc_list=[], bcc_list=[], email_words_dict={}, request='',
                              attachment=[]
                                                            
3- Give title(email_key) to get your required template
4- provide other oprional arguments(to_list,cc_list & bcc_list) to replace defaults already in object.
5- To replace the keywords in subject and description, 
provide email_words_dict with keys as your selected keyword with values you want to replace it with.
```

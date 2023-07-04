Contains REST APIs for the Hypernet Project

## Requirements
- Python 3.6.0
- Django 1.11.3
- PostgreSQL 9.6.3
## Installation
- Install requirements
 ```
pip install -r requirements.txt

Setup database and add local_settings.py file in project folder with database specifics
```
- Migrate Database
```
python manage.py migrate
```

```
local_settings mandatory variables.

#PROXY SERVER DATABASE
DATABASES = {
'hypernet-proxy': {
       'ENGINE': 'django.db.backends.postgresql_psycopg2',
       'NAME': 'hypernet_proxy',
       'USER': 'hypernet',
       'PASSWORD': 'Hypernymbiz@123',
       'HOST': 'hypernet-proxy.cloudapp.net',
       'PORT': '5432',
            }
        }

#KEEP THE CURRENT FRONT END IP(DOMAIN) FOR GETTING CORRECT ACTIVATION LINK IN SIGNUP EMAIL.
FRONT_END_1 = "dev-hypernet.hypernymbiz.com:85"
FRONT_END_2 = "159.65.7.152:85"
ACTIVE_FRONT_END = FRONT_END_1

```


- Initializing commands
```
1. python manage.py hypernetsetupstatuses
2. python manage.py ioasetupstatuses
3. python manage.py iofsetupstatuses
4. python manage.py pppsetupstatuses
5. python manage.py setupmodules
6. python manage.py setuproles
7. python manage.py setupcustomer <user name> <module id>
8. python manage.py createsuperuser
9. python manage.py setupdevicetypes
10. python manage.py animalstates <no_of_animals(int)>
11. python manage.py addemailtemplate
12.

```

#####IOA dummy data generation commands
note 1 : make sure that above commands are executed before data generation commands.
note 2 : add 3 rows in user_module table. i.e. ioa,iof,ppp
```
1. python manage.py addcaretakers
2. python manage.py createdata
3. python manage.py schedule
4. python manage.py createactivities
5. python manage.py aggregate
```
Logistics Driver creation Command
python manage.py setupuser <email> <password> <customer_id> <associated_entity_id>

Run this command to add a driver user who can login via the mobile app. This user will not be able to login to the
web portal in the future.
```
## Tools
- Pycharm
- PgAdmin

## Contributors

Thanks goes to these wonderful people.
<br />
[<img src="https://avatars3.githubusercontent.com/u/17177551?v=4&u=df010f12e4f180f6df01d22b9e05667bd7ad6e50&s=400" width="100px" /><br /><sub>Muhammad Soban</sub>](https://github.com/Muhammad-Soban)<br />
[<img src="https://graph.facebook.com/v2.6/1609414447/picture?type=large" /><br /><sub>Waleed Shabbir</sub>](https://gitlab.com/waleed.metis)<br />

## License
Hypernym FZ LLC
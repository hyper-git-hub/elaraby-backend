from __future__ import unicode_literals

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import PROTECT

from user.enums import RoleTypeEnum
from backend import settings
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from customer.models import Customer
from options.models import Options

# Create your models here.


class Module(models.Model):
    name = models.CharField(unique=True, max_length=30)
    url = models.CharField(max_length=50)

    def as_json_module(self):
        return {
            "module_name": self.name,
            "module_id": self.id,
        }

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(unique=True, max_length=30)
    customer = models.ForeignKey(Customer, blank=True, null=True)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='role_modified_by', null=True, blank=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name


class RoleHistory(models.Model):
    name = models.CharField(unique=True, max_length=30)
    customer = models.ForeignKey(Customer, blank=True, null=True)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='role_modified_by_history')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    role = models.ForeignKey(Role)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.customer = Customer.objects.get(id=1)
        user.role = Role.objects.get(id=RoleTypeEnum.ADMIN)
        user.status = Options.objects.get(value='Active', key='recordstatus')
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    is_staff = models.BooleanField(_('is_staff'), default=True)
    is_active = models.BooleanField(_('active'), default=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    customer = models.ForeignKey(Customer, null=True, blank=True)
    status = models.ForeignKey(Options, related_name='user_record_status', blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_modified_by', null=True, blank=True)
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    reset_token = models.CharField(max_length=50, blank=True)
    reset_token_datetime = models.DateTimeField(blank=True, null=True)
    role = models.ForeignKey(Role, models.SET_NULL, blank=True, null=True)
    objects = UserManager()
    gender = models.ForeignKey(Options, related_name='user_gender', blank=True, null=True)
    contact_number = models.CharField(max_length=30, blank=True, null=True)
    language = models.ForeignKey(Options, related_name='user_language', blank=True, null=True)
    preferred_module = models.FloatField(default=1.0)
    associated_entity = models.ForeignKey(settings.ENTITY_MODEL, null=True, blank=True, related_name='associated_user') #When driver logs in he must know this entity id so that if he hits the APIs, he must know this id.
    one_signal_device_id = models.CharField(blank=True, null=True, max_length=100)
    android_device_info = models.TextField(null=True, blank=True)
    ios_device_info = models.TextField(null=True, blank=True)
    # TODO Migrate after specification is finailized
    # allowed_modules = JSONField(null=True, blank=True, max_length=100)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        '''
        Returns the first_name plus the last_name, with a space in between.
        '''
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        '''
        Returns the short name for the user.
        '''
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''
        Sends an email to this User.
        '''
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def natural_key(self):
        return self.email

    def user_as_json(self):
        return {
            "id": self.id,
            "name": self.first_name,
            "last_name": self.last_name,
            "role_name": self.role.name,
            "role_id": self.role.id,
            "contact_no": self.contact_number,
            'email': self.email,
            'is_active': self.is_active,
            'date_joined': str(self.date_joined.date()),
            'avatar_url': "http://www.myiconfinder.com/uploads/iconsets/256-256-b4decbe23d90ae57e986c90d1be3c838-farmer.png"
            if not self.avatar else 'http://localhost:8000'+self.avatar.url,
            #  'avatar' : self.context['request'].build_absolute_uri(self.avatar.url),
            # 'avatar_url': "http://www.myiconfinder.com/uploads/iconsets/256-256-b4decbe23d90ae57e986c90d1be3c838-farmer.png",
            'gender': None if not self.gender else self.gender.option_as_dict(),
            'language': None if not self.language else self.language.option_as_dict(),
            'status': None if not self.status else self.status.option_as_dict(),
        }



class UserAssignment(models.Model):
    name = models.CharField(max_length=50)
    child = models.ForeignKey(User, related_name='user_child')
    parent = models.ForeignKey(Role, related_name='role_parent')
    customer = models.ForeignKey(Customer)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_assignment_modified_by')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

class UserConfirmation(models.Model):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    contact_number = models.CharField(max_length=30, blank=True, null=True)
    reset_token = models.CharField(max_length=50, blank=True)
    customer = models.ForeignKey(Customer, null=True, blank=True)
    active=models.NullBooleanField(default=False,null=True, blank=True)
    
class UserAssignmentHistory(models.Model):
    name = models.CharField(max_length=50)
    child = models.ForeignKey(User, related_name='user_child_history')
    parent = models.ForeignKey(Role, related_name='role_parent_history')
    customer = models.ForeignKey(Customer)
    status = models.ForeignKey(Options)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_assignment_modified_by_history')
    modified_datetime = models.DateTimeField(blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    end_datetime = models.DateTimeField(blank=True, null=True)
    user_assignment = models.ForeignKey(UserAssignment)

    def __str__(self):
        return self.name


class ModuleAssignment(models.Model):
    customer = models.ForeignKey(Customer)
    module = models.ForeignKey(Module)
    
    def __str__(self):
        return str(self.customer)+'-'+str(self.module)





class UserManual(models.Model):
    file = models.FileField(upload_to='manual/',null=True,blank=True)

    def __str__(self):
        return self.file

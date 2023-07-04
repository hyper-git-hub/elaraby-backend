from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    CharField,
    EmailField,
    ValidationError
    )

from .models import Customer, CustomerPreferences


class CustomerCreateUpdateSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            #'id',
            'name',
            #'slug',
            'subscription_is_valid'
        ]


class CustomerDetailSerializer(ModelSerializer):
    # url = customer_detail_url
    # user = UserDetailSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = [
            # 'url',
            'id',
            'name',
            'subscription_is_valid'
        ]


class CustomerListSerializer(ModelSerializer):
    # url = customer_detail_url
    # user = UserDetailSerializer(read_only=True)
    class Meta:
        model = Customer
        fields = [
            # 'url',
            'id',
            'name',
            'subscription_is_valid'
        ]


class CustomerPreferencesSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None

    class Meta:
        model = CustomerPreferences
        fields = [

            'id',
            'customer',
            'customer_name',

            'activity_review',
            'activity_review_admin_buffer',
            'activity_accept_driver_buffer',
            'activity_start_driver_buffer',

            'activity_start',
            'activity_end',
            'activity_reject',
            'activity_accept',
            'activity_suspend',
            'activity_resume',
            'activity_abort',

            'activity_accept_reject_buffer',

            'activity_start_buffer',
            'average_activity_time',

            'enable_accept_reject',

            'shift_start',
            'shift_end',

            'bin_pickup',
            'bin_dropoff',
            'waste_collection',

            'speed_violations',
            'territory_violations',
            'speed_violation_global',

            'assets_notification',
            'value_added_tax',
            'company_name',
            'address',
            'phone_no',
            'fax_no',
            'email',
            'url',
            'shift_hours',

            'attendance_alerts',
            'site_zone_violations_alerts',
            'active_inactive_alerts',
            
            'daily_invoice',
            'weekly_invoice',
            'monthly_invoice',

            'diesel_price'
        ]


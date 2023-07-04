from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from ffp.models import Tasks, EmployeeViolations


class TaskSerializer(ModelSerializer):
    customer_name = SerializerMethodField('customer_method', allow_null=True, required=False, read_only=True)
    module_name = SerializerMethodField('module_method', required=False, allow_null=True)
    task_status_label = SerializerMethodField('status_method', required=False, allow_null=True)
    assignee_name = SerializerMethodField('assignee_method', allow_null=True, required=False, read_only=True)
    responsible_name = SerializerMethodField('responsible_method', allow_null=True, required=False, read_only=True)
    site_name = SerializerMethodField('site_method', allow_null=True, required=False, read_only=True)
    zone_name = SerializerMethodField('zone_method', allow_null=True, required=False, read_only=True)

    def assignee_method(self, obj):
        if obj.assignee:
            return obj.assignee.name
        else:
            return None

    def site_method(self, obj):
        if obj.site:
            return obj.site.name
        else:
            return None

    def zone_method(self, obj):
        if obj.zone:
            return obj.zone.name
        else:
            return None

    def responsible_method(self, obj):
        if obj.responsible:
            return obj.responsible.name
        else:
            return None

    def customer_method(self, obj):
        if obj.customer:
            return obj.customer.name
        else:
            return None

    def status_method(self, obj):
        if obj.task_status:
            stat = obj.task_status.label
            return stat
        else:
            return None

    def module_method(self, obj):
        if obj.module:
            mod = obj.module.name
            return mod
        else:
            return None

    class Meta:
        model = Tasks
        fields = \
            [
                'id',
                'customer',
                'customer_name',
                'module',
                'module_name',
                'modified_by',

                'task_status',
                'task_status_label',
                'created_datetime',
                'start_datetime',
                'end_datetime',
                'actual_start_datetime',
                'actual_end_datetime',
                'notification_sent',

                'assignee',
                'assignee_name',

                'responsible',
                'responsible_name',

                'site',
                'site_name',

                'zone',
                'zone_name',

                'violations',
                'notes',
                'title',
                'approved',

            ]


class ViolationSerializer(ModelSerializer):
    zone_name = SerializerMethodField('zone_name_method', allow_null=True, required=False, read_only=True)
    site_name = SerializerMethodField('site_name_method', allow_null=True, required=False, read_only=True)
    violation_type_label = SerializerMethodField('violation_type_label_method', allow_null=True, required=False, read_only=True)
    employee_name = SerializerMethodField('employee_name_method', allow_null=True, required=False, read_only=True)

    def zone_name_method(self, obj):
        if obj.zone:
            return obj.zone.name
        else:
            return None

    def site_name_method(self, obj):
        if obj.site:
            return obj.site.name
        else:
            return None

    def violation_type_label_method(self,obj):
        if obj.violations_type:
            return obj.violations_type.label
        else:
            return None

    def employee_name_method(self, obj):
        if obj.employee:
            return obj.employee.name
        else:
            return None

    class Meta:
        model = EmployeeViolations

        fields = [
        'customer',
        'module',
        'created_datetime',

        'employee',
        'violations_type',
        'violations_dtm',
        'zone',
        'site',
        'zone_name',
        'site_name',
        'violation_type_label',
        'employee_name'

        ]


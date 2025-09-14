from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LeaveApplication, LeaveType, LeaveComment

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role', 'department']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'description', 'max_days_per_request', 'is_active']

class LeaveCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LeaveComment
        fields = ['id', 'comment', 'user', 'created_at']

class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    leave_type = LeaveTypeSerializer(read_only=True)
    leave_type_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    comments = LeaveCommentSerializer(many=True, read_only=True)
    can_be_cancelled = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'employee', 'leave_type', 'leave_type_id', 'start_date', 'end_date', 
            'days_requested', 'reason', 'status', 'status_display', 'priority', 
            'priority_display', 'attachment', 'created_at', 'updated_at', 
            'comments', 'can_be_cancelled'
        ]
        read_only_fields = ['employee', 'days_requested', 'created_at', 'updated_at']
    
    def get_can_be_cancelled(self, obj):
        return obj.can_be_cancelled()
    
    def create(self, validated_data):
        validated_data['employee'] = self.context['request'].user
        return super().create(validated_data)
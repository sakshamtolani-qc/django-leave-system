from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import LeaveApplication, LeaveType, LeaveComment
from .serializers import LeaveApplicationSerializer, LeaveTypeSerializer, LeaveCommentSerializer
from accounts.utils import send_leave_status_notification, send_approval_request_notification

User = get_user_model()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class LeaveApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = LeaveApplication.objects.select_related('employee', 'leave_type').prefetch_related('comments__user')
        
        # Filter based on user role
        if user.role == 'employee':
            return queryset.filter(employee=user)
        elif user.role in ['hr', 'admin']:
            # HR and Admin can see all applications
            return queryset.all()
        
        return queryset.filter(employee=user)
    
    @action(detail=False, methods=['get'])
    def my_leaves(self, request):
        """Get current user's leave applications"""
        leaves = LeaveApplication.objects.filter(employee=request.user).order_by('-created_at')
        page = self.paginate_queryset(leaves)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(leaves, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get leaves pending approval for the current user's role"""
        user = request.user
        queryset = LeaveApplication.objects.none()
        
        if user.role == 'hr':
            queryset = LeaveApplication.objects.filter(status='pending')
        elif user.role == 'admin':
            queryset = LeaveApplication.objects.filter(status='hr_approved')
        
        page = self.paginate_queryset(queryset.order_by('-created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a leave application"""
        leave = self.get_object()
        user = request.user
        action_type = request.data.get('action')  # 'approve' or 'reject'
        comments = request.data.get('comments', '')
        
        # Check permissions - only Admin can approve in our simplified workflow
        can_approve = user.role == 'hr' and leave.status == 'pending'
        can_final_approve = (user.role == 'admin' or user.is_superuser) and leave.status == 'hr_approved'
        
        if not (can_approve or can_final_approve):
            return Response(
                {'error': 'You do not have permission to approve this leave.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if action_type == 'approve':
            if can_approve:
                # HR Approval
                leave.status = 'hr_approved'
                leave.hr_approved = True
                leave.hr_approved_by = user
                leave.hr_approved_at = timezone.now()
                leave.hr_comments = comments
            elif can_final_approve:
                # Admin Final Approval
                leave.status = 'approved'
                leave.admin_approved = True
                leave.admin_approved_by = user
                leave.admin_approved_at = timezone.now()
                leave.admin_comments = comments
        else:
            leave.status = 'rejected'
            if user.role == 'hr':
                leave.hr_comments = comments
            else:
                leave.admin_comments = comments
        
        leave.save()
        
        # Send notification
        try:
            send_leave_status_notification(leave, user)
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
        
        # Add comment if provided
        if comments:
            LeaveComment.objects.create(
                leave_application=leave,
                user=user,
                comment=f"Status updated to {leave.get_status_display()}: {comments}"
            )
        
        serializer = self.get_serializer(leave)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a leave application"""
        leave = self.get_object()
        
        if leave.employee != request.user:
            return Response(
                {'error': 'You can only cancel your own leave applications.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not leave.can_be_cancelled():
            return Response(
                {'error': 'This leave application cannot be cancelled.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave.status = 'cancelled'
        leave.save()
        
        serializer = self.get_serializer(leave)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to a leave application"""
        leave = self.get_object()
        comment_text = request.data.get('comment')
        
        if not comment_text:
            return Response(
                {'error': 'Comment text is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = LeaveComment.objects.create(
            leave_application=leave,
            user=request.user,
            comment=comment_text
        )
        
        serializer = LeaveCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
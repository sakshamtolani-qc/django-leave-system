# leaves/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.db.models import Q
from django.utils import timezone
from .models import LeaveApplication, LeaveComment
from django.contrib.auth import get_user_model
from .forms import LeaveApplicationForm, LeaveApprovalForm, LeaveCommentForm
from .utils import (
    send_leave_submitted_email,
    send_leave_approved_email,
    send_leave_rejected_email,
    send_approval_notification_to_approvers,
)
from accounts.utils import (
    send_leave_status_notification,
    send_approval_request_notification,
    send_leave_submitted_email,
)

User = get_user_model()

class LeaveApplicationListView(LoginRequiredMixin, ListView):
    model = LeaveApplication
    template_name = "leaves/leave_list.html"
    context_object_name = "leaves"
    paginate_by = 10

    def get_queryset(self):
        return LeaveApplication.objects.filter(employee=self.request.user)


class LeaveApplicationCreateView(LoginRequiredMixin, CreateView):
    model = LeaveApplication
    form_class = LeaveApplicationForm
    template_name = "leaves/apply_leave.html"
    success_url = reverse_lazy("leaves:my_leaves")

    def form_valid(self, form):
        form.instance.employee = self.request.user
        response = super().form_valid(form)

        messages.success(self.request, "Leave application submitted successfully!")

        # Send confirmation email to employee
        try:
            send_leave_submitted_email(self.object)
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")

        # Notify HR users about new application
        hr_users = User.objects.filter(role="hr", is_active=True)
        email_sent_count = 0
        for hr_user in hr_users:
            try:
                send_approval_request_notification(self.object, hr_user)
                email_sent_count += 1
            except Exception as e:
                print(f"Failed to notify HR user {hr_user.email}: {str(e)}")

        # Add success message about notifications
        if email_sent_count > 0:
            messages.info(
                self.request,
                f"HR team ({email_sent_count} users) has been notified of your application.",
            )

        return response


class LeaveApplicationDetailView(LoginRequiredMixin, DetailView):
    model = LeaveApplication
    template_name = "leaves/leave_detail.html"
    context_object_name = "leave"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = LeaveCommentForm()
        context["comments"] = self.object.comments.all()

        # Check if user can approve this leave based on HR → Admin flow
        user = self.request.user
        leave = self.object

        can_approve = leave.can_be_approved_by(user)
        context["can_approve"] = can_approve
        context["approval_form"] = LeaveApprovalForm() if can_approve else None

        return context


@login_required
def approve_leave(request, pk):
    leave = get_object_or_404(LeaveApplication, pk=pk)
    user = request.user

    # Check permissions for HR → Admin flow
    if not leave.can_be_approved_by(user):
        messages.error(request, "You do not have permission to approve this leave.")
        return redirect("leaves:leave_detail", pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        comments = request.POST.get("comments", "")

        if action == "approve":
            if user.role == "hr" and leave.status == "pending":
                # HR Approval
                leave.status = "hr_approved"
                leave.hr_approved = True
                leave.hr_approved_by = user
                leave.hr_approved_at = timezone.now()
                leave.hr_comments = comments
                send_leave_approved_email(leave, "HR", comments)

                # Notify admin for final approval
                send_approval_notification_to_approvers(leave)
                messages.success(
                    request,
                    "Leave application approved by HR. Awaiting Admin approval.",
                )

            elif (
                user.role == "admin" or user.is_superuser
            ) and leave.status == "hr_approved":
                # Admin Final Approval
                leave.status = "approved"
                leave.admin_approved = True
                leave.admin_approved_by = user
                leave.admin_approved_at = timezone.now()
                leave.admin_comments = comments
                # Send final approval email
                send_leave_approved_email(leave, "Admin", comments)
                messages.success(request, "Leave application fully approved!")

        elif action == "reject":
            leave.status = "rejected"
            reviewer_name = user.get_full_name() or user.username
            if user.role == "hr":
                leave.hr_comments = comments
            else:
                leave.admin_comments = comments

            send_leave_rejected_email(leave, reviewer_name, comments)
            messages.success(request, "Leave application rejected.")

        leave.save()

        # Add comment if provided
        if comments:
            LeaveComment.objects.create(
                leave_application=leave,
                user=user,
                comment=f"Status updated to {leave.get_status_display()}: {comments}",
            )

    return redirect("leaves:leave_detail", pk=pk)


class HRPendingLeavesView(LoginRequiredMixin, ListView):
    """View for HR to see leaves pending their approval"""

    model = LeaveApplication
    template_name = "leaves/hr_pending.html"
    context_object_name = "leaves"
    paginate_by = 10

    def get_queryset(self):
        # Only HR can access this view
        if self.request.user.role != "hr":
            return LeaveApplication.objects.none()

        return LeaveApplication.objects.filter(status="pending").order_by("-created_at")


class AdminPendingLeavesView(LoginRequiredMixin, ListView):
    """View for Admin to see leaves pending their approval"""

    model = LeaveApplication
    template_name = "leaves/admin_pending.html"
    context_object_name = "leaves"
    paginate_by = 10

    def get_queryset(self):
        # Only Admin/Superuser can access this view
        if not (self.request.user.role == "admin" or self.request.user.is_superuser):
            return LeaveApplication.objects.none()

        return LeaveApplication.objects.filter(status="hr_approved").order_by(
            "-created_at"
        )


# Updated dashboard context
@login_required
def get_dashboard_context(request):
    """Helper function to get dashboard context based on user role"""
    user = request.user
    context = {}

    if user.role == "hr":
        context["hr_pending_count"] = LeaveApplication.objects.filter(
            status="pending"
        ).count()
    elif user.role == "admin" or user.is_superuser:
        context["admin_pending_count"] = LeaveApplication.objects.filter(
            status="hr_approved"
        ).count()

    return context


@login_required
def add_comment(request, pk):
    leave = get_object_or_404(LeaveApplication, pk=pk)

    if request.method == "POST":
        form = LeaveCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.leave_application = leave
            comment.user = request.user
            comment.save()
            messages.success(request, "Comment added successfully!")

    return redirect("leaves:leave_detail", pk=pk)


@login_required
def cancel_leave(request, pk):
    leave = get_object_or_404(LeaveApplication, pk=pk, employee=request.user)

    if leave.can_be_cancelled():
        leave.status = "cancelled"
        leave.save()
        messages.success(request, "Leave application cancelled successfully!")
    else:
        messages.error(request, "This leave application cannot be cancelled.")

    return redirect("leaves:leave_detail", pk=pk)


class PendingLeavesView(LoginRequiredMixin, ListView):
    model = LeaveApplication
    template_name = "leaves/pending_leaves.html"
    context_object_name = "leaves"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = LeaveApplication.objects.none()

        if user.role == "manager":
            queryset = LeaveApplication.objects.filter(status="pending")
        elif user.role == "hr":
            queryset = LeaveApplication.objects.filter(status="manager_approved")
        elif user.role == "admin":
            queryset = LeaveApplication.objects.filter(status="hr_approved")

        return queryset

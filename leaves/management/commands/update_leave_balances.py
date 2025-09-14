# leaves/management/commands/update_leave_balances.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import LeaveBalance
from leaves.models import LeaveApplication
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Update leave balances based on approved leaves'
    
    def handle(self, *args, **options):
        self.stdout.write('Updating leave balances...')
        
        # Get all approved leaves from this year
        current_year = date.today().year
        approved_leaves = LeaveApplication.objects.filter(
            status='approved',
            start_date__year=current_year
        ).select_related('employee', 'leave_type')
        
        # Group by employee and leave type
        employee_leave_usage = {}
        for leave in approved_leaves:
            employee = leave.employee
            leave_type = leave.leave_type.name.lower()
            
            if employee not in employee_leave_usage:
                employee_leave_usage[employee] = {}
            
            if leave_type not in employee_leave_usage[employee]:
                employee_leave_usage[employee][leave_type] = 0
            
            employee_leave_usage[employee][leave_type] += leave.days_requested
        
        # Update balances
        for employee, usage in employee_leave_usage.items():
            balance, created = LeaveBalance.objects.get_or_create(user=employee)
            
            # Reset to default values first (you might want to adjust this logic)
            if created:
                self.stdout.write(f'Created new leave balance for {employee.username}')
            
            # Deduct used days (this is a simplified approach)
            if 'annual leave' in usage:
                balance.annual_leave = max(0, 21 - usage['annual leave'])
            if 'sick leave' in usage:
                balance.sick_leave = max(0, 10 - usage['sick leave'])
            if 'casual leave' in usage:
                balance.casual_leave = max(0, 7 - usage['casual leave'])
            
            balance.save()
            self.stdout.write(f'Updated leave balance for {employee.username}')
        
        self.stdout.write(self.style.SUCCESS('Leave balances updated successfully'))

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from leaves.models import LeaveType, LeaveApplication
from accounts.models import LeaveBalance
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Number of users to create')
        parser.add_argument('--leaves', type=int, default=20, help='Number of leave applications to create')
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create leave types
        leave_types = [
            {'name': 'Annual Leave', 'description': 'Yearly vacation days', 'max_days_per_request': 30},
            {'name': 'Sick Leave', 'description': 'Medical leave', 'max_days_per_request': 10},
            {'name': 'Casual Leave', 'description': 'Personal days', 'max_days_per_request': 7},
            {'name': 'Maternity Leave', 'description': 'Maternity leave', 'max_days_per_request': 90},
            {'name': 'Paternity Leave', 'description': 'Paternity leave', 'max_days_per_request': 15},
            {'name': 'Emergency Leave', 'description': 'Emergency situations', 'max_days_per_request': 5},
        ]
        
        for lt_data in leave_types:
            leave_type, created = LeaveType.objects.get_or_create(
                name=lt_data['name'], 
                defaults=lt_data
            )
            if created:
                self.stdout.write(f'Created leave type: {leave_type.name}')
        
        # Create sample users
        departments = ['Engineering', 'Human Resources', 'Marketing', 'Sales', 'Finance', 'Operations']
        roles = ['employee', 'manager', 'hr', 'admin']
        
        # Create manager and HR users first
        manager, created = User.objects.get_or_create(
            username='manager_john',
            defaults={
                'email': 'manager@company.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'role': 'manager',
                'department': 'Engineering',
                'employee_id': 'EMP001'
            }
        )
        if created:
            manager.set_password('password123')
            manager.save()
            LeaveBalance.objects.create(user=manager)
            self.stdout.write(f'Created manager: {manager.username}')
        
        hr_user, created = User.objects.get_or_create(
            username='hr_alice',
            defaults={
                'email': 'hr@company.com',
                'first_name': 'Alice',
                'last_name': 'HR',
                'role': 'hr',
                'department': 'Human Resources',
                'employee_id': 'EMP002'
            }
        )
        if created:
            hr_user.set_password('password123')
            hr_user.save()
            LeaveBalance.objects.create(user=hr_user)
            self.stdout.write(f'Created HR user: {hr_user.username}')
        
        # Create regular employees
        first_names = ['Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Ethan', 'Sophia', 'Mason', 'Isabella', 'William']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        created_users = []
        for i in range(options['users']):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}_{last_name.lower()}_{i}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@company.com",
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': random.choice(['employee', 'employee', 'employee', 'manager']),  # More employees than managers
                    'department': random.choice(departments),
                    'employee_id': f'EMP{1000 + i}',
                    'manager': manager if random.choice([True, False]) else None
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                LeaveBalance.objects.create(user=user)
                created_users.append(user)
                self.stdout.write(f'Created user: {user.username}')
        
        # Create leave applications
        all_users = list(User.objects.filter(role='employee')) + created_users
        leave_types_list = list(LeaveType.objects.all())
        statuses = ['pending', 'manager_approved', 'hr_approved', 'approved', 'rejected']
        priorities = ['low', 'medium', 'high', 'urgent']
        
        reasons = [
            'Family vacation planned for summer holidays',
            'Medical appointment and recovery time needed',
            'Personal matters that require immediate attention',
            'Wedding ceremony of close family member',
            'Moving to new apartment and settling in',
            'Attending important conference for professional development',
            'Child care responsibilities during school holidays',
            'Emergency dental treatment required',
            'Mental health break and relaxation time needed',
            'Visiting elderly parents in hometown'
        ]
        
        for i in range(options['leaves']):
            user = random.choice(all_users)
            leave_type = random.choice(leave_types_list)
            start_date = date.today() + timedelta(days=random.randint(-30, 60))
            duration = random.randint(1, min(leave_type.max_days_per_request, 15))
            end_date = start_date + timedelta(days=duration - 1)
            
            leave_app, created = LeaveApplication.objects.get_or_create(
                employee=user,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    'reason': random.choice(reasons),
                    'status': random.choice(statuses),
                    'priority': random.choice(priorities),
                    'days_requested': duration
                }
            )
            
            if created:
                # Set approval fields based on status
                if leave_app.status in ['manager_approved', 'hr_approved', 'approved']:
                    leave_app.manager_approved_by = manager
                    leave_app.manager_approved_at = leave_app.created_at + timedelta(hours=2)
                    leave_app.manager_comments = "Approved by manager"
                
                if leave_app.status in ['hr_approved', 'approved']:
                    leave_app.hr_approved_by = hr_user
                    leave_app.hr_approved_at = leave_app.created_at + timedelta(hours=4)
                    leave_app.hr_comments = "Approved by HR"
                
                if leave_app.status == 'approved':
                    leave_app.final_approved_by = hr_user
                    leave_app.final_approved_at = leave_app.created_at + timedelta(hours=6)
                
                leave_app.save()
                self.stdout.write(f'Created leave application: {leave_app}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {options["users"]} users and {options["leaves"]} leave applications'
            )
        )
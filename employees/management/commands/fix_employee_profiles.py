# Create this file: employees/management/__init__.py (empty file)

# Create this file: employees/management/commands/__init__.py (empty file)

# Create this file: employees/management/commands/fix_employee_profiles.py

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix employee profile database issues - remove duplicates and create missing profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Starting Employee Profile Database Fix...\n')
        )
        
        # Check if EmployeeProfile model exists
        try:
            from employees.models import EmployeeProfile
            model_exists = True
            self.stdout.write('✅ EmployeeProfile model found')
        except ImportError:
            model_exists = False
            self.stdout.write(
                self.style.WARNING('⚠️  EmployeeProfile model not found - skipping profile operations')
            )
        
        # Show current user stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n📊 Database Statistics:')
        self.stdout.write(f'   Total users: {total_users}')
        self.stdout.write(f'   Active users: {active_users}')
        
        if model_exists:
            total_profiles = EmployeeProfile.objects.count()
            self.stdout.write(f'   Total profiles: {total_profiles}')
        
        # List all users
        self.stdout.write(f'\n👥 All Users:')
        for user in User.objects.all():
            status = "🟢 Active" if user.is_active else "🔴 Inactive"
            profile_status = ""
            
            if model_exists:
                profile_count = EmployeeProfile.objects.filter(user=user).count()
                if profile_count == 0:
                    profile_status = "❌ No Profile"
                elif profile_count == 1:
                    profile_status = "✅ Has Profile"
                else:
                    profile_status = f"⚠️  {profile_count} Profiles"
            
            self.stdout.write(
                f'   ID: {user.id:2d} | {user.username:15s} | '
                f'{user.get_full_name():20s} | {status} {profile_status}'
            )
        
        if not model_exists:
            self.stdout.write(
                self.style.SUCCESS('\n✅ No profile issues to fix - EmployeeProfile model not created yet')
            )
            return
        
        # Find duplicate profiles
        duplicates = []
        users_without_profiles = []
        
        for user in User.objects.all():
            profiles = EmployeeProfile.objects.filter(user=user)
            profile_count = profiles.count()
            
            if profile_count > 1:
                duplicates.append((user, profiles))
            elif profile_count == 0:
                users_without_profiles.append(user)
        
        # Report issues found
        issues_found = len(duplicates) + len(users_without_profiles)
        
        if issues_found == 0:
            self.stdout.write(
                self.style.SUCCESS('\n✅ No profile issues found! Database is clean.')
            )
            return
        
        self.stdout.write(f'\n🔍 Issues Found:')
        
        if duplicates:
            self.stdout.write(f'   📋 Users with duplicate profiles: {len(duplicates)}')
            for user, profiles in duplicates:
                self.stdout.write(f'      - {user.username}: {profiles.count()} profiles')
        
        if users_without_profiles:
            self.stdout.write(f'   👤 Users without profiles: {len(users_without_profiles)}')
            for user in users_without_profiles:
                self.stdout.write(f'      - {user.username}')
        
        # Dry run mode
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n🔍 DRY RUN MODE - No changes will be made')
            )
            
            if duplicates:
                self.stdout.write('   Would remove duplicate profiles:')
                for user, profiles in duplicates:
                    profiles_to_delete = profiles[1:]
                    self.stdout.write(f'      - Delete {len(profiles_to_delete)} duplicate(s) for {user.username}')
            
            if users_without_profiles:
                self.stdout.write('   Would create missing profiles:')
                for user in users_without_profiles:
                    self.stdout.write(f'      - Create profile for {user.username}')
            
            return
        
        # Confirmation
        if not options['force']:
            self.stdout.write(f'\n⚠️  About to fix {issues_found} profile issues.')
            confirm = input('Continue? (y/N): ')
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write('❌ Cancelled by user')
                return
        
        # Fix duplicates
        if duplicates:
            self.stdout.write('\n🔧 Removing duplicate profiles...')
            
            with transaction.atomic():
                for user, profiles in duplicates:
                    profiles_to_delete = profiles[1:]  # Keep first, delete rest
                    deleted_count = 0
                    
                    for profile in profiles_to_delete:
                        try:
                            profile.delete()
                            deleted_count += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'      ❌ Error deleting profile for {user.username}: {e}')
                            )
                    
                    if deleted_count > 0:
                        self.stdout.write(
                            f'      ✅ Deleted {deleted_count} duplicate profile(s) for {user.username}'
                        )
        
        # Create missing profiles
        if users_without_profiles:
            self.stdout.write('\n🔧 Creating missing profiles...')
            
            created_count = 0
            error_count = 0
            
            for user in users_without_profiles:
                try:
                    profile = EmployeeProfile.objects.create(user=user)
                    self.stdout.write(f'      ✅ Created profile for {user.username}')
                    created_count += 1
                except IntegrityError as e:
                    self.stdout.write(
                        self.style.ERROR(f'      ❌ Integrity error for {user.username}: {e}')
                    )
                    error_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'      ❌ Unexpected error for {user.username}: {e}')
                    )
                    error_count += 1
            
            self.stdout.write(f'\n   Created: {created_count}, Errors: {error_count}')
        
        # Final verification
        self.stdout.write('\n🔍 Final verification...')
        remaining_issues = 0
        
        for user in User.objects.all():
            profile_count = EmployeeProfile.objects.filter(user=user).count()
            if profile_count != 1:
                remaining_issues += 1
                status = "No profile" if profile_count == 0 else f"{profile_count} profiles"
                self.stdout.write(
                    self.style.WARNING(f'      ⚠️  {user.username}: {status}')
                )
        
        if remaining_issues == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All profile issues have been resolved!')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {remaining_issues} issues remain - manual intervention may be required')
            )
        
        # Show updated stats
        final_profiles = EmployeeProfile.objects.count()
        self.stdout.write(f'\n📊 Final Statistics:')
        self.stdout.write(f'   Total users: {total_users}')
        self.stdout.write(f'   Total profiles: {final_profiles}')
        
        if total_users == final_profiles:
            self.stdout.write(self.style.SUCCESS('   ✅ User count matches profile count!'))
        else:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Mismatch: {total_users} users vs {final_profiles} profiles')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Employee profile database fix completed!')
        )
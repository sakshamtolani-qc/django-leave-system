# documents/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, FileResponse,JsonResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from .models import IDCard, OfferLetter
from .forms import OfferLetterForm
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from PIL import Image as PILImage
import qrcode

User = get_user_model()

@login_required
def document_dashboard(request):
    """Documents dashboard - HR/Admin only"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "Only HR and administrators can access document management.")
        return redirect('dashboard:home')
    
    # Get statistics
    id_cards_count = IDCard.objects.count()
    offer_letters_count = OfferLetter.objects.count()
    sent_letters_count = OfferLetter.objects.filter(is_sent=True).count()
    this_month_count = OfferLetter.objects.filter(
        generated_at__month=timezone.now().month,
        generated_at__year=timezone.now().year
    ).count()
    
    # Get recent documents
    recent_id_cards = IDCard.objects.select_related('employee', 'generated_by').order_by('-generated_at')[:5]
    recent_offer_letters = OfferLetter.objects.select_related('employee', 'generated_by').order_by('-generated_at')[:5]
    
    # Get all active employees for the modal
    all_employees = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'id_cards_count': id_cards_count,
        'offer_letters_count': offer_letters_count,
        'sent_letters_count': sent_letters_count,
        'this_month_count': this_month_count,
        'recent_id_cards': recent_id_cards,
        'recent_offer_letters': recent_offer_letters,
        'all_employees': all_employees,
    }
    
    return render(request, 'documents/dashboard.html', context)
@login_required
def edit_offer_letter(request, pk):
    """Edit offer letter - HR/Admin only"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "Only HR and administrators can edit offer letters.")
        return redirect('documents:offer_letter_detail', pk=pk)
    
    offer_letter = get_object_or_404(OfferLetter, pk=pk)
    
    if request.method == 'POST':
        form = OfferLetterForm(request.POST, instance=offer_letter)
        if form.is_valid():
            offer_letter = form.save(commit=False)
            
            # Regenerate letter content with new details
            offer_letter.letter_content = generate_offer_letter_content(
                employee=offer_letter.employee,
                position=offer_letter.position,
                department=offer_letter.department,
                salary=offer_letter.salary,
                joining_date=offer_letter.joining_date
            )
            
            offer_letter.save()
            messages.success(request, 'Offer letter updated successfully!')
            return redirect('documents:offer_letter_detail', pk=offer_letter.pk)
    else:
        form = OfferLetterForm(instance=offer_letter)
    
    context = {
        'form': form,
        'offer_letter': offer_letter,
        'employee': offer_letter.employee,
    }
    
    return render(request, 'documents/edit_offer_letter.html', context)

@login_required
def send_offer_letter(request, pk):
    """Mark offer letter as sent and send email"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    offer_letter = get_object_or_404(OfferLetter, pk=pk)
    
    if request.method == 'POST':
        try:
            # Mark as sent
            offer_letter.is_sent = True
            offer_letter.sent_at = timezone.now()
            offer_letter.save()
            
            # Here you would send the actual email with PDF attachment
            # For now, we'll just return success
            
            return JsonResponse({'success': True, 'message': 'Offer letter sent successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def generate_id_card(request, employee_id):
    """Generate ID card for employee - Admin only"""
    if not (request.user.role in ['admin'] or request.user.is_superuser):
        messages.error(request, "Only administrators can generate ID cards.")
        return redirect('dashboard:user_list')
    
    employee = get_object_or_404(User, id=employee_id)
    
    # Create or update ID card
    id_card, created = IDCard.objects.get_or_create(
        employee=employee,
        defaults={'generated_by': request.user}
    )
    
    if not created:
        id_card.generated_by = request.user
        id_card.save()
    
    messages.success(request, f'ID Card generated for {employee.get_full_name()}')
    return redirect('documents:id_card_view', employee_id=employee.id)

@login_required
def id_card_view(request, employee_id):
    """View ID card"""
    employee = get_object_or_404(User, id=employee_id)
    
    # Check permissions - employees can view their own, admin can view all
    if not (request.user == employee or request.user.role in ['admin'] or request.user.is_superuser):
        messages.error(request, "You can only view your own ID card.")
        return redirect('dashboard:home')
    
    try:
        id_card = employee.id_card
    except IDCard.DoesNotExist:
        messages.error(request, "ID card not generated yet. Contact administrator.")
        return redirect('dashboard:home')
    
    # Generate QR code for the ID
    qr_data = f"Employee: {employee.get_full_name()}\nID: {employee.employee_id}\nCard: {id_card.card_number}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    context = {
        'employee': employee,
        'id_card': id_card,
        'company_name': getattr(settings, 'COMPANY_NAME', 'Quorium Consulting'),
    }
    
    return render(request, 'documents/id_card.html', context)

@login_required
def create_offer_letter(request, employee_id):
    """Create offer letter - HR/Admin only"""
    if not (request.user.role in ['hr', 'admin'] or request.user.is_superuser):
        messages.error(request, "Only HR and administrators can generate offer letters.")
        return redirect('dashboard:user_list')
    
    employee = get_object_or_404(User, id=employee_id)
    
    if request.method == 'POST':
        form = OfferLetterForm(request.POST)
        if form.is_valid():
            offer_letter = form.save(commit=False)
            offer_letter.employee = employee
            offer_letter.generated_by = request.user
            
            # Generate letter content
            offer_letter.letter_content = generate_offer_letter_content(
                employee=employee,
                position=offer_letter.position,
                department=offer_letter.department,
                salary=offer_letter.salary,
                joining_date=offer_letter.joining_date
            )
            
            offer_letter.save()
            messages.success(request, f'Offer letter generated for {employee.get_full_name()}')
            return redirect('documents:offer_letter_detail', pk=offer_letter.pk)
    else:
        form = OfferLetterForm(initial={
            'position': getattr(employee, 'position', ''),
            'department': employee.department or '',
            'joining_date': timezone.now().date(),
        })
    
    context = {
        'form': form,
        'employee': employee,
    }
    
    return render(request, 'documents/create_offer_letter.html', context)

@login_required
def offer_letter_detail(request, pk):
    """View offer letter details"""
    offer_letter = get_object_or_404(OfferLetter, pk=pk)
    
    # Check permissions
    can_view = (
        request.user == offer_letter.employee or
        request.user.role in ['hr', 'admin'] or
        request.user.is_superuser
    )
    
    if not can_view:
        messages.error(request, "You don't have permission to view this offer letter.")
        return redirect('dashboard:home')
    
    context = {
        'offer_letter': offer_letter,
        'company_name': getattr(settings, 'COMPANY_NAME', 'Quorium Consulting'),
    }
    
    return render(request, 'documents/offer_letter_detail.html', context)

@login_required
def download_offer_letter(request, pk):
    """Download offer letter as PDF"""
    offer_letter = get_object_or_404(OfferLetter, pk=pk)
    
    # Check permissions
    can_download = (
        request.user == offer_letter.employee or
        request.user.role in ['hr', 'admin'] or
        request.user.is_superuser
    )
    
    if not can_download:
        messages.error(request, "You don't have permission to download this offer letter.")
        return redirect('dashboard:home')
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    story = []
    
    # Company letterhead
    story.append(Paragraph(f"<b>{getattr(settings, 'COMPANY_NAME', 'Quorium Consulting')}</b>", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("OFFER LETTER", title_style))
    story.append(Spacer(1, 20))
    
    # Letter content
    content_paragraphs = offer_letter.letter_content.split('\n\n')
    for paragraph in content_paragraphs:
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles['Normal']))
            story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="offer_letter_{offer_letter.employee.username}.pdf"'
    
    return response

def generate_offer_letter_content(employee, position, department, salary, joining_date):
    """Generate offer letter content"""
    company_name = getattr(settings, 'COMPANY_NAME', 'Quorium Consulting')
    
    content = f"""Dear {employee.get_full_name()},

We are pleased to offer you the position of {position} in our {department} department at {company_name}.

We were impressed with your background and experience, and believe you will be a valuable addition to our team.

POSITION DETAILS:
• Position: {position}
• Department: {department}
• Reporting Date: {joining_date.strftime('%B %d, %Y')}
• Annual Salary: ₹{salary:,.2f}

TERMS AND CONDITIONS:
• This is a full-time position
• You will be entitled to benefits as per company policy
• This offer is contingent upon successful completion of background checks
• You will be required to sign a confidentiality agreement

Please confirm your acceptance of this offer by signing and returning this letter by {(joining_date - timezone.timedelta(days=7)).strftime('%B %d, %Y')}.

We look forward to welcoming you to the {company_name} team!

Sincerely,

Human Resources Department
{company_name}

---

ACCEPTANCE:

I, {employee.get_full_name()}, accept the above offer of employment.

Signature: _____________________ Date: _____________________"""

    return content
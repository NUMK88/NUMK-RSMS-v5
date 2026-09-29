import csv
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import Student, Book, BookCopy, Transaction, Reservation, DigitalMaterial, Notification, AuditLog, Course

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or request.user.groups.filter(name__in=roles).exists():
                return view_func(request, *args, **kwargs)
            if 'Student' in roles and hasattr(request.user, 'student'):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('You do not have permission to access this page.')
        return wrapped
    return decorator

def log(request, action, obj, details=''):
    AuditLog.objects.create(user=request.user, action=action, object_type=obj.__class__.__name__, object_id=str(obj.pk), details=details)

def refresh_overdue():
    for t in Transaction.objects.filter(status='On Loan', returned_time__isnull=True):
        if t.overdue: t.status='Overdue'; t.save(update_fields=['status'])

def notify(student, title, message, kind='General'):
    Notification.objects.create(student=student,title=title,message=message,notification_type=kind)

@login_required
def dashboard(request):
    refresh_overdue()
    return render(request,'core/dashboard.html',{
        'books':Book.objects.count(),'copies':BookCopy.objects.count(),'students':Student.objects.count(),
        'loans':Transaction.objects.filter(status__in=['On Loan','Overdue']).count(),
        'overdue':Transaction.objects.filter(status='Overdue').count(),
        'reservations':Reservation.objects.filter(status__in=['Pending','Ready']).count(),
        'digital':DigitalMaterial.objects.filter(active=True).count(),
        'unread':Notification.objects.filter(read_at__isnull=True).count(),
    })

@login_required
def books(request):
    qs=Book.objects.prefetch_related('copies').order_by('call_number')
    q=request.GET.get('q','').strip()
    if q: qs=qs.filter(title__icontains=q) | qs.filter(author__icontains=q) | qs.filter(call_number__icontains=q)
    return render(request,'core/books.html',{'books':qs,'q':q})

@login_required
def students(request): return render(request,'core/students.html',{'students':Student.objects.all().order_by('matric_no')})

@login_required
@role_required('Librarian','Administrator')
def issue_book(request):
    refresh_overdue()
    if request.method=='POST':
        matric=request.POST.get('matric_no','').strip(); barcode=request.POST.get('barcode','').strip()
        student=get_object_or_404(Student,matric_no=matric,status='Active'); copy=get_object_or_404(BookCopy,barcode=barcode)
        if Transaction.objects.filter(student=student,returned_time__isnull=True).exists(): return HttpResponse('Issue blocked: student already has a Reserve book.',status=400)
        if Transaction.objects.filter(student=student,status='Overdue',returned_time__isnull=True).exists(): return HttpResponse('Issue blocked: student has an overdue item.',status=400)
        if copy.status!='Available': return HttpResponse('Issue blocked: copy is not available.',status=400)
        ready=Reservation.objects.filter(book=copy.book,status='Ready').exclude(student=student).first()
        if ready: return HttpResponse('Issue blocked: this title is reserved for the next student in the queue.',status=400)
        with transaction.atomic():
            now=timezone.now(); t=Transaction.objects.create(student=student,copy=copy,issued_by=request.user,issue_time=now,due_time=now+timezone.timedelta(hours=4),status='On Loan')
            copy.status='On Loan'; copy.save(update_fields=['status'])
            Reservation.objects.filter(student=student,book=copy.book,status__in=['Pending','Ready']).update(status='Fulfilled',fulfilled_at=now)
            notify(student,'Reserve book issued',f'{copy.book.title} is due at {t.due_time.astimezone().strftime("%d %b %Y, %I:%M %p")}.','Loan')
            log(request,'Issue',t,f'Barcode {copy.barcode}; due {t.due_time}')
        return redirect('dashboard')
    return render(request,'core/issue.html')

@login_required
@role_required('Librarian','Administrator')
def return_book(request):
    if request.method=='POST':
        barcode=request.POST.get('barcode','').strip(); copy=get_object_or_404(BookCopy,barcode=barcode)
        t=Transaction.objects.filter(copy=copy,returned_time__isnull=True).order_by('-issue_time').first()
        if not t: return HttpResponse('No active loan found for this copy.',status=404)
        now=timezone.now(); t.returned_time=now; t.returned_by=request.user; t.status='Overdue' if now>t.due_time else 'Returned'; t.save()
        copy.status='Available'; copy.save(update_fields=['status'])
        notify(t.student,'Reserve book returned',f'{copy.book.title} has been recorded as returned.','Return')
        next_res=Reservation.objects.filter(book=copy.book,status='Pending').order_by('requested_at').first()
        if next_res:
            next_res.status='Ready'; next_res.save(update_fields=['status'])
            notify(next_res.student,'Reserved book ready',f'{copy.book.title} is now ready for collection at the Reserve Section.','Reservation')
        log(request,'Return',t,f'Barcode {copy.barcode}; overdue={now>t.due_time}')
        return redirect('dashboard')
    return render(request,'core/return.html')

@login_required
def reservations(request):
    return render(request,'core/reservations.html',{'reservations':Reservation.objects.select_related('student','book').all()})

@login_required
@role_required('Student','Librarian','Administrator')
def reserve_book(request):
    if request.method!='POST': return redirect('books')
    student=get_object_or_404(Student,matric_no=request.POST.get('matric_no','').strip(),status='Active'); book=get_object_or_404(Book,pk=request.POST.get('book_id'))
    if Transaction.objects.filter(student=student,returned_time__isnull=True).exists(): return HttpResponse('Reservation blocked: student already has a Reserve book.',status=400)
    if BookCopy.objects.filter(book=book,status='Available').exists(): return HttpResponse('Reservation is intended for unavailable Reserve materials. A copy is currently available.',status=400)
    if Reservation.objects.filter(student=student,book=book,status__in=['Pending','Ready']).exists(): return HttpResponse('Reservation already exists for this book.',status=400)
    r=Reservation.objects.create(student=student,book=book); notify(student,'Reservation received',f'Your request for {book.title} is in the Reserve queue.','Reservation'); log(request,'Reserve',r); return redirect('reservations')

@login_required
@role_required('Student','Librarian','Administrator')
def cancel_reservation(request,reservation_id):
    r=get_object_or_404(Reservation,pk=reservation_id); r.status='Cancelled'; r.save(update_fields=['status']); log(request,'Cancel reservation',r); return redirect('reservations')

@login_required
@role_required('Librarian','Administrator')
def scanner(request): return render(request,'core/scanner.html')

@login_required
def digital_reserve(request):
    qs=DigitalMaterial.objects.filter(active=True).select_related('course').order_by('-added_at')
    return render(request,'core/digital_reserve.html',{'materials':qs})

@login_required
def notifications(request):
    student=getattr(request.user,'student',None)
    qs=Notification.objects.filter(student=student).order_by('-created_at') if student else Notification.objects.none()
    return render(request,'core/notifications.html',{'notifications':qs})

@login_required
def mark_notification_read(request,notification_id):
    student=getattr(request.user,'student',None); n=get_object_or_404(Notification,pk=notification_id,student=student); n.read_at=timezone.now(); n.save(update_fields=['read_at']); return redirect('notifications')

@login_required
@role_required('Librarian','Administrator')
def reports(request):
    refresh_overdue()
    context={'transactions':Transaction.objects.count(),'issued':Transaction.objects.filter(returned_time__isnull=True).count(),'returned':Transaction.objects.filter(returned_time__isnull=False).count(),'overdue':Transaction.objects.filter(status='Overdue').count(),'reservations':Reservation.objects.count(),'digital':DigitalMaterial.objects.filter(active=True).count()}
    return render(request,'core/reports.html',context)

@login_required
@role_required('Librarian','Administrator')
def transactions_csv(request):
    refresh_overdue(); response=HttpResponse(content_type='text/csv'); response['Content-Disposition']='attachment; filename="numk-rsms-transactions.csv"'; w=csv.writer(response); w.writerow(['Student','Matric No.','Book','Call Number','Barcode','Issue Time','Due Time','Return Time','Status'])
    for t in Transaction.objects.select_related('student','copy__book').order_by('-issue_time'):
        w.writerow([t.student.full_name,t.student.matric_no,t.copy.book.title,t.copy.book.call_number,t.copy.barcode,t.issue_time,t.due_time,t.returned_time,t.status])
    return response


@login_required
def student_portal(request):
    student=getattr(request.user,'student',None)
    if not student: raise PermissionDenied('Student account required.')
    refresh_overdue()
    loans=Transaction.objects.filter(student=student,returned_time__isnull=True).select_related('copy__book')
    reservations_qs=Reservation.objects.filter(student=student).select_related('book').order_by('-requested_at')
    notifications_qs=Notification.objects.filter(student=student).order_by('-created_at')[:10]
    return render(request,'core/student_portal.html',{'student':student,'loans':loans,'reservations':reservations_qs,'notifications':notifications_qs})

@login_required
@role_required('Librarian','Administrator')
def staff_portal(request):
    refresh_overdue()
    return render(request,'core/staff_portal.html',{'today_issues':Transaction.objects.filter(issue_time__date=timezone.localdate()).count(),'today_returns':Transaction.objects.filter(returned_time__date=timezone.localdate()).count(),'available':BookCopy.objects.filter(status='Available').count(),'overdue':Transaction.objects.filter(status='Overdue').count()})

@login_required
@role_required('Administrator')
def management_portal(request):
    return render(request,'core/management_portal.html',{'users':__import__('django.contrib.auth.models',fromlist=['User']).User.objects.count(),'books':Book.objects.count(),'copies':BookCopy.objects.count(),'students':Student.objects.count(),'courses':Course.objects.count(),'transactions':Transaction.objects.count()})

@login_required
@role_required('Librarian','Administrator')
def transactions_xlsx(request):
    from openpyxl import Workbook
    wb=Workbook(); ws=wb.active; ws.title='Transactions'
    ws.append(['Student','Matric No.','Book','Call Number','Barcode','Issue Time','Due Time','Return Time','Status'])
    for t in Transaction.objects.select_related('student','copy__book').order_by('-issue_time'):
        ws.append([t.student.full_name,t.student.matric_no,t.copy.book.title,t.copy.book.call_number,t.copy.barcode,t.issue_time.replace(tzinfo=None),t.due_time.replace(tzinfo=None),t.returned_time.replace(tzinfo=None) if t.returned_time else None,t.status])
    response=HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); response['Content-Disposition']='attachment; filename="numk-rsms-transactions.xlsx"'; wb.save(response); return response

@login_required
@role_required('Librarian','Administrator')
def transactions_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    response=HttpResponse(content_type='application/pdf'); response['Content-Disposition']='attachment; filename="numk-rsms-transactions.pdf"'
    doc=SimpleDocTemplate(response,pagesize=landscape(A4),rightMargin=20,leftMargin=20,topMargin=25,bottomMargin=25)
    styles=getSampleStyleSheet(); data=[['Student','Matric','Book','LCC Call No.','Barcode','Issue','Due','Return','Status']]
    for t in Transaction.objects.select_related('student','copy__book').order_by('-issue_time'):
        data.append([t.student.full_name,t.student.matric_no,t.copy.book.title,t.copy.book.call_number,t.copy.barcode,t.issue_time.strftime('%d/%m/%Y %H:%M'),t.due_time.strftime('%d/%m/%Y %H:%M'),t.returned_time.strftime('%d/%m/%Y %H:%M') if t.returned_time else '-',t.status])
    table=Table(data,repeatRows=1); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP')]))
    doc.build([Paragraph('NUMK-RSMS Reserve Section — Transaction Report',styles['Title']),table]); return response

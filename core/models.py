from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Student(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,null=True,blank=True)
    matric_no=models.CharField(max_length=50,unique=True)
    full_name=models.CharField(max_length=200)
    department=models.CharField(max_length=150,blank=True)
    programme=models.CharField(max_length=150,blank=True)
    level=models.CharField(max_length=30,blank=True)
    status=models.CharField(max_length=30,default='Active')
    def __str__(self): return f'{self.matric_no} - {self.full_name}'

class Lecturer(models.Model):
    staff_id=models.CharField(max_length=50,unique=True)
    full_name=models.CharField(max_length=200)
    department=models.CharField(max_length=150,blank=True)
    email=models.EmailField(blank=True)
    def __str__(self): return self.full_name

class Course(models.Model):
    code=models.CharField(max_length=30,unique=True)
    title=models.CharField(max_length=200)
    department=models.CharField(max_length=150,blank=True)
    level=models.CharField(max_length=30,blank=True)
    semester=models.CharField(max_length=30,blank=True)
    session=models.CharField(max_length=30,blank=True)
    lecturer=models.ForeignKey(Lecturer,null=True,blank=True,on_delete=models.SET_NULL)
    def __str__(self): return f'{self.code} - {self.title}'

class Book(models.Model):
    title=models.CharField(max_length=300)
    author=models.CharField(max_length=250)
    isbn=models.CharField(max_length=50,blank=True)
    edition=models.CharField(max_length=80,blank=True)
    publisher=models.CharField(max_length=200,blank=True)
    year=models.PositiveIntegerField(null=True,blank=True)
    lcc_class=models.CharField(max_length=10,help_text='Example: Z')
    lcc_number=models.CharField(max_length=30,help_text='Example: 665')
    cutter_number=models.CharField(max_length=30,blank=True,help_text='Example: .L53')
    call_number=models.CharField(max_length=100,db_index=True)
    collection=models.CharField(max_length=100,default='Reserve')
    def __str__(self): return f'{self.call_number} - {self.title}'

class BookCopy(models.Model):
    book=models.ForeignKey(Book,on_delete=models.CASCADE,related_name='copies')
    accession_no=models.CharField(max_length=80,unique=True)
    barcode=models.CharField(max_length=100,unique=True)
    copy_no=models.PositiveIntegerField(default=1)
    condition=models.CharField(max_length=50,default='Good')
    status=models.CharField(max_length=30,default='Available')
    def __str__(self): return self.accession_no

class ReserveItem(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    book=models.ForeignKey(Book,on_delete=models.CASCADE)
    required_copies=models.PositiveIntegerField(default=1)
    reserve_type=models.CharField(max_length=30,default='Core')
    active=models.BooleanField(default=True)

class Transaction(models.Model):
    student=models.ForeignKey(Student,on_delete=models.PROTECT)
    copy=models.ForeignKey(BookCopy,on_delete=models.PROTECT)
    issued_by=models.ForeignKey(User,on_delete=models.PROTECT,related_name='issued_transactions')
    issue_time=models.DateTimeField(default=timezone.now)
    due_time=models.DateTimeField()
    returned_time=models.DateTimeField(null=True,blank=True)
    returned_by=models.ForeignKey(User,null=True,blank=True,on_delete=models.PROTECT,related_name='returned_transactions')
    status=models.CharField(max_length=30,default='On Loan')
    remarks=models.TextField(blank=True)
    def save(self,*args,**kwargs):
        if not self.due_time:
            self.due_time=self.issue_time+timedelta(hours=4)
        super().save(*args,**kwargs)
    @property
    def overdue(self): return self.returned_time is None and timezone.now()>self.due_time

class Reservation(models.Model):
    STATUS_CHOICES=[('Pending','Pending'),('Ready','Ready'),('Fulfilled','Fulfilled'),('Cancelled','Cancelled')]
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='reservations')
    book=models.ForeignKey(Book,on_delete=models.CASCADE,related_name='reservations')
    requested_at=models.DateTimeField(default=timezone.now)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
    fulfilled_at=models.DateTimeField(null=True,blank=True)
    notes=models.TextField(blank=True)
    class Meta:
        ordering=['requested_at']
        constraints=[models.UniqueConstraint(fields=['student','book'],condition=models.Q(status__in=['Pending','Ready']),name='unique_active_student_book_reservation')]
    def __str__(self): return f'{self.student.matric_no} - {self.book.title} - {self.status}'

class DigitalMaterial(models.Model):
    ACCESS_CHOICES=[('Course','Course students'),('All Students','All students'),('Staff','Staff only')]
    title=models.CharField(max_length=300)
    course=models.ForeignKey(Course,on_delete=models.SET_NULL,null=True,blank=True,related_name='digital_materials')
    material_type=models.CharField(max_length=50,default='PDF')
    file=models.FileField(upload_to='digital_reserve/',blank=True,null=True)
    external_url=models.URLField(blank=True)
    access_level=models.CharField(max_length=30,choices=ACCESS_CHOICES,default='Course')
    active=models.BooleanField(default=True)
    added_at=models.DateTimeField(default=timezone.now)
    def __str__(self): return self.title

class Notification(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='notifications')
    title=models.CharField(max_length=200)
    message=models.TextField()
    notification_type=models.CharField(max_length=40,default='General')
    created_at=models.DateTimeField(default=timezone.now)
    read_at=models.DateTimeField(null=True,blank=True)
    def __str__(self): return f'{self.student.matric_no}: {self.title}'

class AuditLog(models.Model):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    action=models.CharField(max_length=100)
    object_type=models.CharField(max_length=100)
    object_id=models.CharField(max_length=50,blank=True)
    details=models.TextField(blank=True)
    created_at=models.DateTimeField(default=timezone.now)
    class Meta: ordering=['-created_at']

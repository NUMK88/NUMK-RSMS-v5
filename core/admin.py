from django.contrib import admin
from .models import *
for model in [Student,Lecturer,Course,Book,BookCopy,ReserveItem,Transaction,Reservation,DigitalMaterial,Notification,AuditLog]:
    admin.site.register(model)

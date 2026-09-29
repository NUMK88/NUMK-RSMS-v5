from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from core import views
urlpatterns=[
 path('admin/',admin.site.urls), path('login/',auth_views.LoginView.as_view(template_name='core/login.html'),name='login'), path('logout/',auth_views.LogoutView.as_view(),name='logout'),
 path('',views.dashboard,name='dashboard'),
 path('student-portal/',views.student_portal,name='student_portal'), path('staff-portal/',views.staff_portal,name='staff_portal'), path('management/',views.management_portal,name='management_portal'), path('books/',views.books,name='books'), path('students/',views.students,name='students'),
 path('issue/',views.issue_book,name='issue'), path('return/',views.return_book,name='return'), path('scanner/',views.scanner,name='scanner'),
 path('reservations/',views.reservations,name='reservations'), path('reserve/',views.reserve_book,name='reserve'), path('reservations/<int:reservation_id>/cancel/',views.cancel_reservation,name='cancel_reservation'),
 path('digital-reserve/',views.digital_reserve,name='digital_reserve'), path('notifications/',views.notifications,name='notifications'), path('notifications/<int:notification_id>/read/',views.mark_notification_read,name='mark_notification_read'),
 path('reports/',views.reports,name='reports'), path('reports/transactions.csv',views.transactions_csv,name='transactions_csv'), path('reports/transactions.xlsx',views.transactions_xlsx,name='transactions_xlsx'), path('reports/transactions.pdf',views.transactions_pdf,name='transactions_pdf'),
]

from django.contrib import admin
#super user - okstore
#pass 1234
# Register your models here.
from .models import *

admin.site.register(Customer)
admin.site.register(Seller)

from django.contrib import admin

from .models import Label, Membership, Project

admin.site.register(Project)
admin.site.register(Label)
admin.site.register(Membership)

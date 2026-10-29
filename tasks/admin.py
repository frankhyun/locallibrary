from django.contrib import admin

from .models import Attachment, Comment, Task

admin.site.register(Task)
admin.site.register(Comment)
admin.site.register(Attachment)

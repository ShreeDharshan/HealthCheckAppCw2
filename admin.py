from django.contrib import admin
from .models import Department, Team, Profile, Session, Card, Vote

admin.site.register(Department)
admin.site.register(Team)
admin.site.register(Profile)
admin.site.register(Session)
admin.site.register(Card)
admin.site.register(Vote)

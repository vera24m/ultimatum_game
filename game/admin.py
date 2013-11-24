from django.contrib import admin
from game.models import Opponent, Player, Round, Question, Option, Answer

class OptionInline(admin.StackedInline):
    model = Option
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['text']}),
    ]
    inlines = [OptionInline]

admin.site.register(Opponent)
admin.site.register(Player)
admin.site.register(Round)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)

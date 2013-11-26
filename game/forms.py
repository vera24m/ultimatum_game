from django.forms import Form, ModelForm, BooleanField, RadioSelect, HiddenInput

from game.models import Kind, Opponent, Player, Round, Question, Option, Answer

class OfferAcceptanceForm(ModelForm):
    class Meta:
        model = Round
        fields = ['accepted', 'time_elapsed']
        widgets = { 'accepted': RadioSelect, 'time_elapsed' : HiddenInput }

class QuestionnaireForm(ModelForm):
    class Meta:
        model = Answer
        fields = ['option']
        widgets = { 'option': RadioSelect }
    
    #def clean_option(self):
    #    option = self.cleaned_data['option']
    #    return Option.objects.get(id=option)

class ReadForm(Form):
    checked = BooleanField(label='Check this box if you have read this carefully')

class DemographicForm(ModelForm):
    class Meta:
        model = Player
        fields = ['hours_a_day_you_spend_behind_a_computer', 'age', 'nationality',
                  #'gender', 'robot_experience', 'ultimatum_experience',
                 ]
        widgets = {'gender': RadioSelect, 'robot_experience': RadioSelect, 'ultimatum_experience': RadioSelect}

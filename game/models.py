import logging
from django.core.exceptions import ValidationError
from django.db import models
from uuid import uuid1

logger = logging.getLogger(__name__)

class Kind(models.Model):
    ID_HUMAN = 'h'
    ID_COMPUTER = 'c'
    ID_ROBOT = 'r'
    ID_NONDETERMINISTIC = 'n'
    IDS = (
        (ID_HUMAN, 'Human'),
        (ID_COMPUTER, 'Computer'),
        (ID_ROBOT, 'Robot'),
        (ID_NONDETERMINISTIC, 'Randomness'),
    )

    id = models.CharField(max_length=1, choices=IDS, primary_key=True)

    def __unicode__(self):
        return self.get_id_display()

class Opponent(models.Model):
    # XXX: Beter way of storing this?
    kind = models.ForeignKey(Kind)
    picture = models.CharField(max_length=20)

    def __unicode__(self):
        return '<O(%s) %s>' % (self.kind, self.pk)

class Player(models.Model):
    MALE = False
    FEMALE = True
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female')
    )
    
    YES_NO = ((True, 'Yes'), (False, 'No'))

    registration_datetime = models.DateTimeField(auto_now_add=True)
    opponent_kind = models.ForeignKey(Kind)
    #opponents = models.ManyToManyField(Opponent)
    mturk_key = models.CharField(max_length=32, default=uuid1().hex, editable=False)
    start_time = models.IntegerField(default=-1)
    instructions_time = models.IntegerField(default=-1)
    questionnaire_time = models.IntegerField(default=-1)
    
    #gender = models.BooleanField(max_length=1, choices=GENDER)
    hours_a_day_you_spend_behind_a_computer = models.CharField(max_length=3)
    #robot_experience = models.BooleanField(choices=YES_NO)
    #ultimatum_experience = models.BooleanField(choices=YES_NO)
    age = models.CharField(max_length=3)
    nationality = models.CharField(max_length=50)

    # XXX: Express that all opponents should be of the same kind.

    def __unicode__(self):
        return '<P(%s) %s>' % (self.opponent_kind, self.pk)

class Round(models.Model):
    ACCEPT_CHOICES = ((True, 'Accept'), (False, 'Reject'))

    datetime = models.DateTimeField(auto_now=True)
    player = models.ForeignKey(Player)
    opponent = models.ForeignKey(Opponent)
    amount_offered = models.IntegerField()
    is_intentional = models.BooleanField()
    accepted = models.BooleanField(choices=ACCEPT_CHOICES, default=None)
    time_elapsed = models.IntegerField(default=-1)

    # XXX: Express that oppenent's kind matches player's selected opponent_kind.
    
    def clean(self):
        if self.accepted not in (True, False):
            raise ValidationError('The offer must be accepted or rejected explicitly.')

    def __unicode__(self):
        return '<R(%s) %s / %s / %s>' % (self.accepted, self.opponent, self.amount_offered, self.player)

class Question(models.Model):
    """Model for a question of the questionnaire."""
    text = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.text

class Option(models.Model):
    """Model for a possible answer to a question."""
    question = models.ForeignKey(Question)
    text = models.CharField(max_length=200)
    
    def __unicode__(self):
        return self.text

class Answer(models.Model):
    """Model for an answer a user has given to a question."""
    player = models.ForeignKey(Player)
    question = models.ForeignKey(Question)
    #options = [o for o in Option.objects.all() if o.question==Question.objects.all()[2]]
    #choices = ((option.id, option.text) for option in options) 
    option = models.ForeignKey(Option)      
    
    def __unicode__(self):
        return '<A %s / %s / %s>' % (self.player, self.question, self.option)
    
    def generate_choices(self):
        question = self.question
        options = [o for o in Option.objects.all() if o.question==question]
        choices = ((option.id, option.text) for option in options)
        return choices

from django.core.exceptions import ValidationError
from django.db import models

class Kind(models.Model):
    ID_HUMAN = 'h'
    ID_COMPUTER = 'c'
    ID_ROBOT = 'r'
    IDS = (
        (ID_HUMAN, 'Human'),
        (ID_COMPUTER, 'Computer'),
        (ID_ROBOT, 'Robot'),
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
    MALE = 'm'
    FEMALE = 'f'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female')
    )

    registration_datetime = models.DateTimeField(auto_now_add=True)
    gender = models.CharField(max_length=1, choices=GENDER)
    opponent_kind = models.ForeignKey(Kind)
    #opponents = models.ManyToManyField(Opponent)

    # XXX: Express that all opponents should be of the same kind.

    def __unicode__(self):
        return '<P(%s) %s>' % (self.opponent_kind, self.pk)

class Round(models.Model):
    ACCEPT_CHOICES = ((True, 'Accept'), (False, 'Reject'))

    datetime = models.DateTimeField(auto_now=True)
    player = models.ForeignKey(Player)
    opponent = models.ForeignKey(Opponent)
    amount_offered = models.IntegerField()
    accepted = models.BooleanField(choices=ACCEPT_CHOICES, default=None)

    # XXX: Express that oppenent's kind matches player's selected opponent_kind.
    
    def clean(self):
        if self.accepted not in (True, False):
            raise ValidationError('The offer must be accepted or rejected explicitly.')

    def __unicode__(self):
        return '<R(%s) %s / %s / %s>' % (self.accepted, self.opponent, this.amount_offered, this.player)

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
    options = Option.objects.all()
    choices = ((option.id, option.text) for option in options)
    player = models.ForeignKey(Player)
    question = models.ForeignKey(Question)
    option = models.ForeignKey(Option, choices=choices, default=None)   
    #ACCEPT_CHOICES = ((True, 'Accept'), (False, 'Reject'))
    #accepted = models.BooleanField(choices=ACCEPT_CHOICES, default=None)
    
    def __unicode__(self):
        return '<A %s / %s / %s>' % (self.player, self.question, self.option)

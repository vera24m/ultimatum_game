from django.db import models

class Opponent(models.Model):
    HUMAN = 'h'
    COMPUTER = 'c'
    ROBOT = 'r'
    KIND = (
        (HUMAN, 'Human'),
        (COMPUTER, 'Computer'),
        (ROBOT, 'Robot'),
    )

    # XXX: Manually set ID/PK.

    kind = models.CharField(max_length=1, choices=KIND)
    # XXX: Beter way of storing this?
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

    gender = models.CharField(max_length=1, choices=GENDER)

    def __unicode__(self):
        return '<P(%s) %s>' % (self.kind, self.pk)

class Round(models.Model):
    player = models.ForeignKey(Player)
    opponent = models.ForeignKey(Opponent)
    amount_offered = models.IntegerField()
    accepted = models.BooleanField()

    def __unicode__(self):
        return '<R(%s) %s / %s / %s>' % (self.accepted, self.opponent, this.amount_offered, this.player)


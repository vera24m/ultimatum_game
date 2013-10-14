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

# XXX: Is there a better way to ensure existence of all Kinds?
for k in Kind.IDS:
    Kind.objects.get_or_create(id=k[0])

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

    gender = models.CharField(max_length=1, choices=GENDER)
    opponent_kind = models.ForeignKey(Kind)
    #opponents = models.ManyToManyField(Opponent)

    # XXX: Express that all opponents should be of the same kind.

    def __unicode__(self):
        return '<P(%s) %s>' % (self.opponent_kind, self.pk)

class Round(models.Model):
    player = models.ForeignKey(Player)
    opponent = models.ForeignKey(Opponent)
    amount_offered = models.IntegerField()
    accepted = models.BooleanField()

    # XXX: Express that oppenent's kind matches player's selected opponent_kind.

    def __unicode__(self):
        return '<R(%s) %s / %s / %s>' % (self.accepted, self.opponent, this.amount_offered, this.player)


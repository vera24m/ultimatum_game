import logging
import random

from django.core.urlresolvers import reverse
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.paginator import Paginator, PageNotAnInteger

from game.models import Kind, Opponent, Player, Round, Question, Option, Answer
from game.forms import OfferAcceptanceForm, QuestionnaireForm, ReadForm, MturkForm

# The amount of "money units" available in each round.
AMOUNT_AVAILABLE = 100
# The number of rounds.
NUM_ROUNDS = 8
# The number of questions per page in the questionnaire.
QUESTIONS_PER_PAGE = 2
# The minimum number of questions per page in the questionnaire.
QUESTION_ORPHANS = 0

logger = logging.getLogger(__name__)

# XXX: Must somehow ensure cookies are enabled?
# XXX: Must showhow ensure javascript is enabled.
# XXX: Must keep track of response times. Augment Round model.
# XXX: We should enforce that the offer is uncovered.
# XXX: Should keep offer displayed once it's been uncovered. Timer must not be
#      reset.

# generate game/fixtures/initial_data.json
# python manage.py dumpdata game | json_pp
# XXX: Also delete players.
###############################################################################
# XXX: Is there a better way to ensure existence of all Kinds?
for k in Kind.IDS:
    Kind.objects.get_or_create(id=k[0])
#
## XXX: Is there a better way to generate all opponents?
for k in Kind.objects.all():
    for i in range(1, NUM_ROUNDS+1):
        picture = '%s_%s' % (k.id, i)
        Opponent.objects.get_or_create(kind=k, picture=picture)
###############################################################################

# XXX: Must enforce, per player, that intro and instructions have been viewed!

class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303

def get_or_create_player(session):
    # XXX: Something to consider: though randomness is probably "good enough",
    # one could also check, for each kind of opponent, how  many players
    # completed the game and questionnaire, then select the opponent kind for
    # which the least amount of data has been collected so far.
    player, created = Player.objects.get_or_create(id=session.get('player_id', None),
        defaults={'opponent_kind': random.choice(Kind.objects.all())})

    if created:
        session['player_id'] = player.id

    return player

def get_opponent(session):
    # XXX: Use hasattr or something like that instead? If so, fix elsewhere as
    # well.
    opponent_id = session.get('opponent_id', None)
    return Opponent.objects.get(id=opponent_id) if opponent_id else None

def create_opponent(session, player):
    # Must not have more than one opponent concurrently.
    assert not get_opponent(session)

    # Determine eligible opponents.
    available_opponents = list(Opponent.objects.filter(kind=player.opponent_kind))
    for r in Round.objects.filter(player=player):
        # Can't play the same opponent twice.
        available_opponents.remove(r.opponent)

    if not available_opponents:
        # No opponents left.
        return None

    # XXX: Might have to select a RANDOM opponent; see
    # /opt/lampp/htdocs/ultimatum/index.php
    opponent = available_opponents[0]
    session['opponent_id'] = opponent.id

    return opponent

def get_or_create_offer(session, player):
    offer = session.get('amount_offered', None)
    if offer:
        # Already made an offer, but it was not yet accepted.
        return offer

    # XXX: This amount precisely matches the number of opponents of any given
    # kind. That correspondence must be made clearer!
    # XXX: Also, for some reason an offer of 40 was never made. We could easily
    # add two times 40. As long as the number of available options is equal to
    # or greater than the number of available opponents, there's no problem.
    # (Of course, during statistical analysis one must keep in mind that
    # players did not receive exactly the same offers.)
    available_offers = [10, 10, 20, 20, 30, 30, 50, 50,]
    assert len(available_offers) == NUM_ROUNDS

    for r in Round.objects.filter(player=player):
        available_offers.remove(r.amount_offered)

    # XXX make nicer.
    assert available_offers

    # XXX: The original experiment hard-coded eight distinct offer sequences
    # that were "symmetric". The fourth and fifth offer would always be
    # identical. Our randomized appraoch doesn't guarantee any of these
    # properties. Is that a good or a bad thing?
    offer = random.choice(available_offers)
    session['amount_offered'] = offer

    return offer

def get_round_number(session, player):
    # Must have an opponent for this question to make sense.
    assert get_opponent(session)

    return len(Round.objects.filter(player=player)) + 1

def get_round_details(session, find_opponent=False):
    player = get_or_create_player(session)

    opponent = get_opponent(session)
    if not opponent and find_opponent:
        opponent = create_opponent(session, player)

    if opponent:
        round_number = get_round_number(session, player)
        logger.debug('Player %s plays round %d against %s' %
                     (player, round_number, opponent))
    else:
        round_number = None
        logger.debug('Player %s played all rounds' % player)

    return player, opponent, round_number

#def can_play_round():
#    return True
#
#def is_playing_round():
#    return True

@require_GET
def start_game(request):
    return render(request, 'game/start_game.html')

@require_GET
def view_instructions(request):
    player = get_or_create_player(request.session)
    return render(request, 'game/view_instructions.html',
                  {'opponent_kind': str(player.opponent_kind)})

@require_GET
def start_round(request):
    player, opponent, round_number = get_round_details(request.session, True)
    if round_number in {1, (NUM_ROUNDS/2)+1} and not request.session.get('viewed', False):
        request.session['viewed'] = True
        return HttpResponseSeeOther(reverse('game:intentionality'))
    else:
        request.session['viewed'] = False
    if not opponent:
        return HttpResponseSeeOther(reverse('game:questionnaire'))

    return render(request, 'game/start_round.html',
                  {'round_number': round_number, 'opponent': opponent, 'picture': opponent.picture + '.jpg'})

@require_GET
def intentionality(request):
    player, opponent, round_number = get_round_details(request.session)
    form = ReadForm()    
    if request.GET.get('checked'):
        return HttpResponseSeeOther(reverse('game:start_round'))
    
    #XXX: randomize intentionality?
    return render(request, 'game/intentionality.html', {'intentionality': (round_number==1), 'form': form})

@require_http_methods(["GET", "POST"])
def play_round(request):
    player, opponent, round_number = get_round_details(request.session)
    if not opponent:
        # The player has not yet been introduced to an opponent. That must
        # happen first.
        return HttpResponseSeeOther(reverse('game:start_round'))

    amount_offered = get_or_create_offer(request.session, player)
    round = Round(player=player, opponent=opponent, amount_offered=amount_offered)
    if request.method == 'GET':
        form = OfferAcceptanceForm(instance=round)
    else:
        form = OfferAcceptanceForm(request.POST, instance=round)
        if form.is_valid():
            form.save()
            # Abstract away from this.
            del request.session['amount_offered']
            #del request.session['opponent_id']

            return HttpResponseSeeOther(reverse('game:end_round'))

    context = {
      'opponent_name': 'Opponent %d' % round_number,
      'amount_offered': amount_offered,
      'amount_kept': AMOUNT_AVAILABLE - amount_offered,
      'form': form,
      'picture': opponent.picture + '.jpg',
    }

    return render(request, 'game/play_round.html', context)

@require_GET
def end_round(request):
    player, opponent, round_number = get_round_details(request.session)
    round = Round.objects.get(player=player, opponent=opponent)
    logger.debug('offered: %s, accepted: %s' % (str(round.amount_offered), str(round.accepted)))
    del request.session['opponent_id']
    return render(request, 'game/end_round.html', {'amount_offered': round.amount_offered, 'accepted': round.accepted})

@require_http_methods(["GET", "POST"])
def questionnaire(request):
    player = get_round_details(request.session)[0]
    questions = Question.objects.all()
    
    paginator = Paginator(questions, per_page=QUESTIONS_PER_PAGE, orphans=QUESTION_ORPHANS) # Show x questions per page
    page = request.session.get('page', 1)
    
    if page > paginator.num_pages:
        return render(request, 'game/thankyou.html', {})
    
    questions = paginator.page(page)
    answers = [Answer(player=player, question=q) for q in questions]
    if request.method == 'GET':
        forms = [QuestionnaireForm(prefix=str(a.question.id), instance=a) for a in answers]
        questions_forms = [(a.question, QuestionnaireForm(prefix=str(a.question.id), instance=a)) for a in answers]
    else:
        forms = [QuestionnaireForm(request.POST, prefix=str(a.question.id), instance=a) for a in answers]
        questions_forms = [(a.question, QuestionnaireForm(request.POST, prefix=str(a.question.id), instance=a)) for a in answers]
        if all([form.is_valid() for form in forms]):
            for form in forms:
                form.save()
            page += 1
            request.session['page'] = page
            if not questions.has_next():
                # Last page. Go to thank you page.
                request.session['finished'] = True
                return render(request, 'game/thankyou.html', {})
            else:
                return HttpResponseSeeOther(reverse('game:questionnaire'))
    
    questions = paginator.page(page)
    
    for (question, form) in questions_forms:
        form.fields['option'].queryset = Option.objects.filter(question=question)
        form.fields['option'].empty_label = None
    
    request.session['page'] = page
    return render(request, 'game/questionnaire.html', {'forms': forms, 'questions_forms': questions_forms})

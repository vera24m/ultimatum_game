import logging
import random
import time

from django.core.urlresolvers import reverse
from django.db.models import Count, Min
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.paginator import Paginator, PageNotAnInteger

from game.models import Kind, Opponent, Player, Round, Question, Option, Answer
from game.forms import OfferAcceptanceForm, QuestionnaireForm, ReadForm, DemographicForm

from uuid import uuid1

# The amount of "money units" available in each round.
AMOUNT_AVAILABLE = 100
# The number of rounds.
NUM_ROUNDS = 8
# The number of questions per page in the questionnaire.
QUESTIONS_PER_PAGE = 5
# The minimum number of questions per page in the questionnaire.
QUESTION_ORPHANS = 2

logger = logging.getLogger(__name__)

# XXX: Must somehow ensure cookies are enabled?
# XXX: Must showhow ensure javascript is enabled.
# XXX: Should keep offer displayed once it's been uncovered. Timer must not be
#      reset.

# generate game/fixtures/initial_data.json
# python manage.py dumpdata game | json_pp
# XXX: Also delete players.
###############################################################################
# XXX: Is there a better way to ensure existence of all Kinds?
#for k in Kind.IDS:
#    Kind.objects.get_or_create(id=k[0])
##
### XXX: Is there a better way to generate all opponents?
#for k in Kind.objects.all():
#    for i in range(1, NUM_ROUNDS+1):
#        picture = '%s_%s' % (k.id, i)
#        Opponent.objects.get_or_create(kind=k, picture=picture)
###############################################################################

# XXX: Must enforce, per player, that intro and instructions have been viewed!

class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303

def get_or_create_player(session):
    player, created = Player.objects.get_or_create(id=session.get('player_id', None),
        defaults={'opponent_kind': select_opponent_kind_for_new_player()})

    if created:
        session['player_id'] = player.id

    return player

def select_opponent_kind_for_new_player():
    # XXX: We select the opponent kind that has been assigned to the least
    # number of players. Note that *all* players are taken into consideration,
    # including those that did not yet finish or "abandoned" the experiment.
    # This is not optimal, but should converge to optimality in the limit. One
    # advantage of this approach over an approach that takes historical game
    # round data into account is that it has nicer characteristics if, after
    # _some_ rounds have already been played, a large number of people all of a
    # sudden start the experiment.
    kinds = Kind.objects.annotate(num_players=Count('player'))
    min_players = kinds.aggregate(min_players=Min('num_players'))['min_players']
    return random.choice(kinds.filter(num_players=min_players))

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
    opponent = random.choice(available_opponents)
    session['opponent_id'] = opponent.id

    return opponent

def create_intent(session, player):
    choice = session.get('intent', random.choice([True, False]))
    session['intent'] = choice

    return choice

def get_or_create_offer(session, player, opponent):
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
    if str(opponent.kind) != 'Randomness':
        available_offers = [10, 20, 30, 50]
        assert len(available_offers) * 2 == NUM_ROUNDS
    else:
        available_offers = [10, 10, 20, 20, 30, 30, 50, 50]
        assert len(available_offers)  == NUM_ROUNDS
        session['intent'] = False
        
    for r in Round.objects.filter(player=player, is_intentional=session['intent']):
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

def is_first_subround(round_number):
    return round_number in {1, (NUM_ROUNDS / 2) + 1}

@require_GET
def start_game(request):
    request.session['start_time'] = time.time()
    return render(request, 'game/start_game.html', {})

@require_GET
def view_instructions(request):
    player = get_or_create_player(request.session)
    
    if player.instructions_time == -1:
        elapsed = (time.time() - request.session.get('start_time')) * 1000
        player.start_time = int(round(elapsed))
        player.save()

    request.session['instructions_time'] = time.time()

    if str(player.opponent_kind) == 'Randomness':
        page = 'game:no_player'
    else:
        page = 'game:intentionality'

    return render(request, 'game/view_instructions.html',
                  {'opponent_kind': str(player.opponent_kind),
                    'page' : page})
@require_GET
def no_player(request):
    return render(request, 'game/no_player.html', {})

@require_http_methods(["GET", "POST"])
def intentionality(request):
    player, opponent, round_number = get_round_details(request.session)
    
    form = ReadForm()
    logger.debug(request.POST.get('checked', False))
    if not is_first_subround(round_number):
        return HttpResponseSeeOther(reverse('game:start_round'))

    if 'viewed_intentionality' not in request.session:
        request.session['viewed_intentionality'] = []

    if request.method == 'POST' and request.POST.get('checked', False):
        request.session['viewed_intentionality'] += [round_number]
        return HttpResponseSeeOther(reverse('game:start_round'))
    
    choice = create_intent(request.session, player)
    
    if (round_number != 1):
        visited_intent = request.session.get('visited_intent', False)
        if not visited_intent:
            choice = not choice
            request.session['intent'] = choice
            request.session['visited_intent'] = True
    
    return render(request, 'game/intentionality.html',
                  {'intentionality': choice, 'form': form})

@require_GET
def start_round(request):
    player, opponent, round_number = get_round_details(request.session, True)

    if player.instructions_time == -1:
        elapsed = (time.time() - request.session.get('instructions_time')) * 1000
        player.instructions_time = int(round(elapsed))
        player.save()
    #if round_number in {1, (NUM_ROUNDS/2)+1} and not request.session.get('viewed', False):
    #    request.session['viewed'] = True
    #    return HttpResponseSeeOther(reverse('game:intentionality'))
    #else:
    #    request.session['viewed'] = False

    if not opponent:
        return HttpResponseSeeOther(reverse('game:questionnaire'))
         
    if is_first_subround(round_number) and not round_number in request.session.get('viewed_intentionality', []) and not str(opponent.kind) == 'Randomness':
        return HttpResponseSeeOther(reverse('game:intentionality'))

    return render(request, 'game/start_round.html',
                  {'round_number': round_number, 'opponent': opponent, 'picture': opponent.picture + '.jpg'})

@require_http_methods(["GET", "POST"])
def play_round(request):
    player, opponent, round_number = get_round_details(request.session)
    if not opponent:
        # The player has not yet been introduced to an opponent. That must
        # happen first.
        return HttpResponseSeeOther(reverse('game:start_round'))

    amount_offered = get_or_create_offer(request.session, player, opponent)
    round = Round(player=player, opponent=opponent, amount_offered=amount_offered,
                  is_intentional=(request.session['intent']))
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
        return HttpResponseSeeOther(reverse('game:demographic'))
    
    if page == 1:
        request.session['questionnaire_time'] = time.time()
    
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
                # Last page. Go to next page.
                request.session['finished'] = True
                if player.questionnaire_time == -1:
                    elapsed = (time.time() - request.session.get('questionnaire_time')) * 1000
                    player.questionnaire_time = int(round(elapsed))
                    player.save()
                return HttpResponseSeeOther(reverse('game:demographic'))
            else:
                return HttpResponseSeeOther(reverse('game:questionnaire'))
    
    questions = paginator.page(page)
    
    for (question, form) in questions_forms:
        form.fields['option'].queryset = Option.objects.filter(question=question)
        form.fields['option'].empty_label = None
    
    request.session['page'] = page
    return render(request, 'game/questionnaire.html', {'forms': forms, 'questions_forms': questions_forms})

@require_http_methods(["GET", "POST"])
def demographic(request):
    player, opponent, round_number = get_round_details(request.session)
    if request.method == 'GET':
        form = DemographicForm(instance=player)
    else:
        form = DemographicForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            return HttpResponseSeeOther(reverse('game:thankyou'))
    return render(request, 'game/demographic.html', {'form': form})

@require_GET
def thankyou(request):
    player, opponent, round_number = get_round_details(request.session)
    if player.mturk_key == str(0):
        player.mturk_key = uuid1().hex
        player.save()
    key = player.mturk_key
    return render(request, 'game/thankyou.html', {'key': key})

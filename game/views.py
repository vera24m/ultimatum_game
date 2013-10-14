import random

from django.http import HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from game.models import Kind, Opponent, Player, Round

def get_or_create_player(session):
    player, created = Player.objects.get_or_create(id=session.get('player_id', None),
        defaults={'opponent_kind': random.choice(Kind.objects.all())})

    if created:
        session['player_id'] = player.id

    return player

@require_GET
def start_game(request):
    return render(request, 'game/start_game.html', {})

@require_POST
def view_instructions(request):
    player = get_or_create_player(request.session)
    context = {
      'opponent_kind': player.opponent_kind
    }

    return render(request, 'game/view_instructions.html', context)

@require_POST
def start_round(request):
    return render(request, 'game/start_round.html', {})

@require_POST
def play_round(request):
    return render(request, 'game/play_round.html', {})

@require_POST
def end_round(request):
    return render(request, 'game/end_round.html', {})


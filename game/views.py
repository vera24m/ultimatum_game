import random

from django.http import HttpResponseNotAllowed
from django.shortcuts import render

from game.models import Opponent, Player, Round

def start_game(request):
    return render(request, 'game/start_game.html', {})

def view_instructions(request):
    # XXX: Add template explaining this is not the start of the game.
    # XXX: We're going to repeat this often. Add nice decorator.
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    context = {
      'opponent_kind': random.choice(Opponent.KIND)[0]
    }

    return render(request, 'game/view_instructions.html', context)


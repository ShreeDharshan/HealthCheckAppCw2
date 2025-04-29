from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Card, Vote, Session, Profile, Team, Department

# Home page - Health Check Voting
@login_required
def home(request):
    cards = Card.objects.all()
    sessions = Session.objects.order_by('-date')  

    selected_session_id = request.GET.get('session') or request.POST.get('session')
    if selected_session_id:
        try:
            selected_session = Session.objects.get(id=selected_session_id)
        except Session.DoesNotExist:
            selected_session = sessions.first()
    else:
        selected_session = sessions.first()

    votes = Vote.objects.filter(user=request.user, session=selected_session) if selected_session else []
    existing_votes = {vote.card.id: vote for vote in votes}

    
    cards_to_show = [card for card in cards if card.id not in existing_votes]

    if request.method == 'POST':
        for card in cards_to_show:
            status = request.POST.get(f'status_{card.id}')
            improving = request.POST.get(f'improving_{card.id}') == 'on'

            if status and selected_session:
                Vote.objects.update_or_create(
                    user=request.user,
                    session=selected_session,
                    card=card,
                    defaults={'status': status, 'improving': improving}
                )
        messages.success(request, "Your votes have been saved successfully!")
        return redirect(f"/?session={selected_session.id}")

    context = {
        'cards': cards_to_show,
        'sessions': sessions,
        'selected_session': selected_session,
        'existing_votes': existing_votes,
    }
    return render(request, 'checkapp/home.html', context)

# Register new user
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'checkapp/register.html', {'form': form})

# Team Summary page
@login_required
def team_summary(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'team_leader':
        messages.error(request, "You are not authorized to view the team summary.")
        return redirect('home')

    team = request.user.profile.team
    if not team:
        messages.error(request, "You are not assigned to any team.")
        return redirect('home')

    team_members = Profile.objects.filter(team=team).values_list('user', flat=True)
    latest_session = Session.objects.order_by('-date').first()

    votes = Vote.objects.filter(user__in=team_members, session=latest_session) if latest_session else []

    summary = votes.values('card__title', 'status').annotate(count=Count('id'))

    result = {}
    for entry in summary:
        card = entry['card__title']
        status = entry['status']
        count = entry['count']
        if card not in result:
            result[card] = {'green': 0, 'amber': 0, 'red': 0}
        result[card][status] = count

    context = {
        'team': team,
        'summary': result
    }
    return render(request, 'checkapp/team_summary.html', context)

# Department Summary page
@login_required
def department_summary(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'department_leader':
        messages.error(request, "You are not authorized to view the department summary.")
        return redirect('home')

    department = request.user.profile.team.department if request.user.profile.team else None
    if not department:
        messages.error(request, "You are not assigned to any department.")
        return redirect('home')

    teams = Team.objects.filter(department=department)
    team_members = Profile.objects.filter(team__in=teams).values_list('user', flat=True)
    latest_session = Session.objects.order_by('-date').first()

    votes = Vote.objects.filter(user__in=team_members, session=latest_session) if latest_session else []

    summary = votes.values('card__title', 'status').annotate(count=Count('id'))

    result = {}
    for entry in summary:
        card = entry['card__title']
        status = entry['status']
        count = entry['count']
        if card not in result:
            result[card] = {'green': 0, 'amber': 0, 'red': 0}
        result[card][status] = count

    context = {
        'department': department,
        'summary': result
    }
    return render(request, 'checkapp/department_summary.html', context)

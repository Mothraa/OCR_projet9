from itertools import chain
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Value, CharField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
# from django.urls import reverse_lazy

from .forms import TicketForm, ReviewForm, FollowerForm, DeleteTicketForm  # Ticket, Review, 
from authentication.models import CustomUser
from .models import UserFollows, Ticket, Review

# pour debug
# import logging
# logger = logging.getLogger(__name__)
#####


# def custom_pagination(queryset_name, context_name):
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapper(request, *args, **kwargs):
#             response = view_func(request, *args, **kwargs)

#             if isinstance(response, dict):
#                 queryset = response.get(queryset_name)
#                 if queryset:
#                     paginator = Paginator(queryset, settings.NB_ITEM_PAGINATOR)
#                     page_number = request.GET.get('page')
#                     try:
#                         paginated_queryset = paginator.page(page_number)
#                     except PageNotAnInteger:
#                         paginated_queryset = paginator.page(1)
#                     except EmptyPage:
#                         paginated_queryset = paginator.page(paginator.num_pages)

#                     response[context_name] = paginated_queryset
#             return response
#         return wrapper
#     return decorator


@login_required
def home(request):
    return render(request, 'ticket/home.html')


# @custom_pagination('tickets', 'tickets')
@login_required
def flux(request):
    tickets = Ticket.objects.all()

    paginator = Paginator(tickets, settings.NB_ITEM_PAGINATOR)
    page_number = request.GET.get('page')
    try:
        paginated_tickets = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_tickets = paginator.page(1)
    except EmptyPage:
        paginated_tickets = paginator.page(paginator.num_pages)
    return render(request, 'ticket/flux.html', context={'tickets': paginated_tickets})


# @custom_pagination('posts', 'posts')
@login_required
def posts(request):

    # on récupère les tickets et reviews de l'utilisateur, auquel on ajoute un "tag" pour les distinguer
    tickets = Ticket.objects.filter(user=request.user)
    tickets = tickets.annotate(content_type=Value('TICKET', CharField()))
    reviews = Review.objects.filter(user=request.user)
    reviews = reviews.annotate(content_type=Value('REVIEW', CharField()))
    # on regroupe les deux listes en une, que l'on trie par date antéchronologique
    posts = sorted(chain(reviews, tickets), key=lambda post: post.time_created, reverse=True)

    # on regarde pour chaque post si l'utilisateur y a déjà répondu ou pas
    user_reply = {
        post.id: post.ticket and Review.objects.filter(ticket=post.ticket, user=request.user).exists()
        for post in posts if hasattr(post, 'ticket')
    }

    paginator = Paginator(posts, settings.NB_ITEM_PAGINATOR)
    page_number = request.GET.get('page')
    try:
        paginated_posts = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_posts = paginator.page(1)
    except EmptyPage:
        paginated_posts = paginator.page(paginator.num_pages)

    return render(request, 'ticket/posts.html', context={'posts': paginated_posts, 'user_reply': user_reply})


@login_required
def review_reply(request):
    pass
    return render(request, 'ticket/posts.html')


@login_required
def ticket_edit(request, ticket_id):
    # https://docs.djangoproject.com/fr/5.0/topics/http/shortcuts/
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # logger.debug(f"Editing ticket with ID: {ticket.id}")
    print(f"Editing ticket with ID: {ticket.id}")
    # edit_form = TicketForm(instance=ticket)
    if request.method == 'POST':
        edit_form = TicketForm(request.POST, request.FILES, instance=ticket)
        if edit_form.is_valid():
            edit_form.save()
            return redirect('posts')
    else:
        edit_form = TicketForm(instance=ticket)

    return render(request, 'ticket/edit_ticket.html',  {'edit_form': edit_form})


@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.method == 'POST':
        form = DeleteTicketForm(request.POST)
        if form.is_valid() and form.cleaned_data['delete_ticket']:
            ticket.delete()
            # print("Effacé !! ou presque...")
            messages.success(request, f"Ticket {ticket.title} supprimé.")
            return redirect('posts')
        else:
            messages.error(request, "Erreur de suppression.")
    # return redirect(reverse_lazy('posts'))
    return redirect('posts')


@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():
            print("form is valid")
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, f"Ticket {ticket.title} créé avec succès.")
            return redirect('flux')
        else:
            print("Ticket form errors:", form.errors)
            messages.error(
                request,
                "Erreur lors de la création du ticket.\
                Si l'erreur persiste veuillez prendre contact avec votre administrateur."
            )
    else:
        # print("Ticket form errors:", form.errors)
        form = TicketForm()
    return render(request, 'ticket/create_ticket.html', {'form': form})


@login_required
def create_review(request):
    if request.method == 'POST':
        ticket_form = TicketForm(request.POST, request.FILES)
        review_form = ReviewForm(request.POST)

        if ticket_form.is_valid() and review_form.is_valid():
        # if all([ticket_form.is_valid(), review_form.is_valid()]):
            ticket = ticket_form.save(commit=False)
            ticket.user = request.user
            ticket.save()

            review = review_form.save(commit=False)
            review.user = request.user
            review.ticket = ticket  # on récupère le ticket qui vient d'etre créé pour y assigner la review
            review.save()

            messages.success(request, "Ticket et critique créées avec succès.")
            return redirect('flux')
        else:
            print("Ticket form errors:", ticket_form.errors)
            print("Review form errors:", review_form.errors)
            messages.error(
                request,
                "Erreur lors de la création du ticket.\
                Si l'erreur persiste veuillez prendre contact avec votre administrateur."
            )
    else:
        ticket_form = TicketForm()
        review_form = ReviewForm()
    return render(request, 'ticket/create_review.html', {
        'ticket_form': ticket_form,
        'review_form': review_form,
    })



@login_required
def review_edit(request):
    return render(request, 'ticket/home.html')


@login_required
def review_delete(request):
    return render(request, 'ticket/home.html')





@login_required
def subscription(request):
    if request.method == 'POST':
        add_user_form = FollowerForm(request.POST)
        add_user_form.user = request.user

        if add_user_form.is_valid():
            followed_user_nickname = add_user_form.cleaned_data.get('followed_user')
            try:
                # nickname__iexact => insensible a la casse
                followed_user = CustomUser.objects.get(nickname__iexact=followed_user_nickname)
            except CustomUser.DoesNotExist:
                messages.error(request, "Cet utilisateur n'existe pas.")
                return render(request, 'ticket/subscription.html', {
                    'add_user_form': add_user_form,
                    'abonnements': request.user.following.all(),
                    'abonnes': request.user.followed_by.all()
                })

            # add_user_form.followed_user = followed_user_nickname
            # add_user_form.user = request.user
            # add_user_form.save()

            # Vérifie si l'utilisateur suit déjà l'autre utilisateur
            if UserFollows.objects.filter(user=request.user, followed_user=followed_user).exists():
                messages.error(request, "Vous suivez déjà cet utilisateur.")
            else:
                UserFollows.objects.create(user=request.user, followed_user=followed_user)
                messages.success(request, f'Utilisateur "{followed_user_nickname}" suivi avec succès.')
                return redirect('subscription')

    else:
        add_user_form = FollowerForm()

    abonnements = request.user.following.all()
    abonnes = request.user.followed_by.all()

    return render(request, 'ticket/subscription.html', {
        'add_user_form': add_user_form,
        'abonnements': abonnements,
        'abonnes': abonnes
    })


@login_required
def remove_subscription(request, subscription_id):
    try:
        subscription = UserFollows.objects.get(id=subscription_id, user=request.user)
        followed_user_nickname = subscription.followed_user.nickname
        subscription.delete()
        # TODO ajouter le nom de l'utilisateur
        messages.success(request, f"Abonnement à {followed_user_nickname} supprimé.")
    except UserFollows.DoesNotExist:
        messages.error(request, "Vous ne suivez pas cet utilisateur.")

    return redirect('subscription')

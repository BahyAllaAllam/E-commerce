from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from Ecommerce import settings
from .forms import UserUpdateForm, ProfileUpdateForm
from django.core.mail import send_mail


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('users:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'users/profile.html', context)


@login_required
def delete_user(request, username):
    user = User.objects.get(username=username)
    if request.user == user:
        if request.method == 'POST':
            user.delete()
            messages.success(request, 'Your account has been deleted successfully !')
            return redirect('/')
        return render(request, 'users/delete_user.html', {'user': user})
    else:
        messages.warning(request, 'Oops you do not have permission to do that!')
        return redirect('users:profile')

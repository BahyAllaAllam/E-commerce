from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UserUpdateForm, ProfileUpdateForm


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

    return render(request, 'users/profile.html', {'u_form': u_form, 'p_form': p_form})


@login_required
def delete_user(request, username):
    # Use get_object_or_404 — bare .get() raises an unhandled exception for unknown users
    user = get_object_or_404(User, username=username)

    if request.user != user:
        messages.warning(request, 'You do not have permission to do that.')
        return redirect('users:profile')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('/')

    return render(request, 'users/delete_user.html', {'user': user})

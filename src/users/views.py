from django.shortcuts import render, redirect, reverse
from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, EmailChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes, force_text
from Ecommerce import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from users.utils import account_activation_token
from django.core.mail import EmailMultiAlternatives


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, f'Your account has been successfully activated! You are now able to login {user.username} !')
        return redirect('login')
        # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        messages.warning(request, 'The activation link is invalid!')
        return redirect('users:register')


def register(request):
    # emails = User.objects.filter(is_active=True).exclude(email='').values_list('email', flat=True)
    if request.user.is_authenticated:
        messages.success(request, 'You have to logout first!')
        return redirect('/')

    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get('email')
            user.is_active = False
            user.save()
            # context= {'user':user, 'username':username, 'email': email}
            activate_user(request, user, email, username)
            return redirect('login')
    else:
        form = UserRegisterForm()

    return render(request, "users/register.html", {'form': form})


@login_required
def change_email(request, username):
    user = request.user
    old_email = request.user.email
    if request.method == 'POST':
        e_form = EmailChangeForm(request.POST, instance=request.user)
        if e_form.is_valid():
            email = e_form.cleaned_data.get('email')
            if email == old_email:
                messages.warning(request, 'Please Enter A Different Email Address !')
                return redirect('users:change_email', user.username)
            e_form.save(commit=False)
            request.user.is_active = False
            e_form.save()
            activate_user(request, user, email)
            return redirect('login')
        messages.success(request, 'Please write a valid email.')
        return redirect('users:change_email', user.username)
    e_form = EmailChangeForm(instance=request.user)
    return render(request, 'users/change_email.html', {'e_form': e_form, 'user': user})


def activate_user(request, *args):
    user = args[0]
    email = args[1]

    current_site = get_current_site(request)
    link_content = {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    }
    link = reverse('users:activate', kwargs={
        'uidb64': link_content['uid'], 'token': link_content['token']
    })
    activate_url = 'http://' + current_site.domain + link
    email_subject = 'Email Verification'
    c = dict({'username': user, 'activate_url': activate_url})
    text_content = render_to_string('mail_body.txt', c)
    html_content = render_to_string('mail_body.html', c)
    email_message = EmailMultiAlternatives(
        email_subject,
        text_content,
        settings.EMAIL_HOST_USER,
        [email],
    )
    email_message.attach_alternative(html_content, "text/html")
    email_message.send(fail_silently=False)
    messages.success(request, 'We have sent you an email to verify your account, please check your mail!')
    return redirect('login')


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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from apps.admin_soft.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, \
    UserPasswordChangeForm
from django.contrib.auth import logout
from django.views.generic import TemplateView, UpdateView, View
from django.contrib import messages
from apps.converter.models import UserSettings, Research, Transaction
from apps.payments.models import Payment


# Create your views here.

# Pages
def index(request):
    return render(request, 'pages/index.html', {'segment': 'index'})


# def billing(request):
#     return render(request, 'pages/billing.html', {'segment': 'billing'})


# def tables(request):
#     return render(request, 'pages/tables.html', {'segment': 'tables'})


# def profile(request):
#     return render(request, 'pages/profile.html', {'segment': 'profile'})


class ProfileView(LoginRequiredMixin, TemplateView, SuccessMessageMixin):
    template_name = 'pages/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context.update({
            'user_settings': UserSettings.objects.filter(user=self.request.user).first(),
            'user_id': self.request.user.id,
            'research': Research.objects.filter(user=self.request.user).order_by('-date_created'),
            'transaction': Payment.objects.filter(user=self.request.user).order_by('-created_at'),
        })
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'pages/edit_profile.html'
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    success_url = '/accounts/profile'
    success_message = 'Successfully updated your profile.'


# Authentication
class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = '/'

    def get_success_url(self):
        return self.success_url


class RegisterView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/accounts/login/', {
                messages.success(request, 'Ваш аккаунт создан! Теперь вы можете войти.')
            })  # Замените на ваш путь для входа
        return render(request, 'accounts/register.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = UserSetPasswordForm


class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = UserPasswordChangeForm

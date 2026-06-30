from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth import logout
from django.views.generic import TemplateView, UpdateView, View
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.converter.models import UserSettings, Research
from apps.payments.models import Payment
from apps.admin_soft.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, \
    UserPasswordChangeForm


RESEARCH_PER_PAGE = 15
VALID_STATUS_FILTERS = frozenset({'all', 'ready', 'processing', 'error'})


def _research_not_ready_q():
    return Q(ready_archive='') | Q(ready_archive__isnull=True)


def _filter_research_qs(qs, status_filter):
    if status_filter == 'ready':
        return qs.exclude(_research_not_ready_q())
    if status_filter == 'error':
        return qs.filter(status=False).filter(_research_not_ready_q())
    if status_filter == 'processing':
        return qs.filter(_research_not_ready_q()).exclude(status=False)
    return qs


def _research_stats(user):
    qs = Research.objects.filter(user=user)
    not_ready = _research_not_ready_q()
    return {
        'total': qs.count(),
        'ready': qs.exclude(not_ready).count(),
        'processing': qs.filter(not_ready).exclude(status=False).count(),
        'error': qs.filter(status=False).filter(not_ready).count(),
    }


class ProfileView(LoginRequiredMixin, TemplateView, SuccessMessageMixin):
    template_name = 'pages/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        user = self.request.user
        status_filter = self.request.GET.get('status', 'all')
        if status_filter not in VALID_STATUS_FILTERS:
            status_filter = 'all'

        research_qs = Research.objects.filter(user=user).order_by('-date_created')
        research_stats = _research_stats(user)
        filtered_qs = _filter_research_qs(research_qs, status_filter)

        paginator = Paginator(filtered_qs, RESEARCH_PER_PAGE)
        page_number = self.request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        context.update({
            'user_settings': UserSettings.objects.filter(user=user).first(),
            'user_id': user.id,
            'has_research': research_stats['total'] > 0,
            'page_obj': page_obj,
            'paginator': paginator,
            'status_filter': status_filter,
            'research_stats': research_stats,
            'transaction': Payment.objects.filter(user=user).order_by('-created_at'),
        })
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'pages/edit_profile.html'
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    success_url = '/accounts/profile'
    success_message = _('Профиль успешно обновлён.')

    def get_object(self, queryset=None):
        return self.request.user


# Authentication
class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = '/'

    def get_success_url(self):
        try:
            UserSettings.objects.get_or_create(user=self.request.user)
        except:
            pass
        return self.success_url


class RegisterView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            try:
                UserSettings.objects.get_or_create(user=self.request.user)
            except:
                pass
            return redirect('/accounts/login/', {
                messages.success(request, 'Ваш аккаунт создан! Теперь вы можете войти.')})
        return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/')



class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = UserSetPasswordForm


class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = UserPasswordChangeForm

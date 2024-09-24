from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from users.forms import RegisterForm, UserUpdateForm


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


class UserCreationView(generic.CreateView):
    model = get_user_model()
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("users:login")


class UserDetailView(LoginRequiredMixin, generic.DetailView):
    model = get_user_model()
    template_name = "users/detail.html"
    queryset = get_user_model().objects.prefetch_related("tasks")

    def get_object(self, queryset=None):
        return self.request.user


class UserUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = get_user_model()
    form_class = UserUpdateForm
    template_name = "users/update.html"
    success_url = reverse_lazy("users:detail")

    def get_object(self, queryset=None):
        return self.request.user

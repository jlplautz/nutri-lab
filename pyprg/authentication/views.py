import os

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.messages import constants
# from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .utils import email_html, password_is_valid

from hashlib import sha256
from .models import Ativacao


def cadastro(request):

    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'cadastro.html')
    elif request.method == "POST":
        username = request.POST.get('usuario')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not password_is_valid(request, senha, confirmar_senha):
            return redirect('/auth/cadastro')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=senha,
                is_active=False
            )
            user.save()

            # criar um token com o hash do email sha256 , necessario os dados
            # em binário depois converter para hexa
            token = sha256(f"{username}{email}".encode()).hexdigest()

            # quando usuario finalizar o cadastro é necessario criar um token
            # para ativar a conta com token criadoserá atruibuido a um user
            ativacao = Ativacao(token=token, user=user)

            ativacao.save()

            # chamar a função para enviar o email
            path_template = os.path.join(
                settings.BASE_DIR,
                'pyprg/authentication/templates/emails/cadastro_confirmado.html'
                )
            email_html(
                path_template, 'Cadastro confirmado', [email, ],
                username=username,
                link_ativacao=f"127.0.0.1:8000/auth/ativar_conta/{token}"
                )

            messages.add_message(
                request, constants.SUCCESS, 'User sucesslly created')
            return redirect('/auth/login')
        except Exception:
            messages.add_message(
                request, constants.ERROR, 'Intern System error')
            return redirect('/auth/cadastro')


def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'login.html')

    elif request.method == "POST":
        username = request.POST.get('usuario')
        senha = request.POST.get('senha')
        # Faz authnenticação do usuário no banco
        usuario = auth.authenticate(username=username, password=senha)

    if not usuario:
        messages.add_message(
            request, constants.ERROR, 'Username ou senha inválidos')
        return redirect('/auth/login')
    else:
        auth.login(request, usuario)
        return redirect('/')


def logout(request):
    auth.logout(request)
    return redirect('/auth/login')


def ativar_conta(request, token):
    token = get_object_or_404(Ativacao, token=token)
    if token.ativo:
        messages.add_message(
            request, constants.WARNING, 'Essa token já foi usado')
        return redirect('/auth/logar')
    user = User.objects.get(username=token.user.username)
    user.is_active = True
    user.save()

    token.ativo = True
    token.save()

    messages.add_message(
        request, constants.SUCCESS, 'Conta ativa com sucesso')
    return redirect('/auth/login')

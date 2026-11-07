from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOuUsuarioBackend(ModelBackend):
    """Permite entrar com o e-mail ou com o nome de usuário (sem diferenciar maiúsculas)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identificador = username or kwargs.get(User.USERNAME_FIELD) or kwargs.get('email')
        if not identificador or password is None:
            return None

        candidatos = User.objects.filter(
            Q(**{f'{User.USERNAME_FIELD}__iexact': identificador}) | Q(email__iexact=identificador)
        ).order_by('id')

        for usuario in candidatos:
            if usuario.check_password(password) and self.user_can_authenticate(usuario):
                return usuario

        if not candidatos:
            # Mantém o tempo de resposta parecido ao de um usuário existente.
            User().set_password(password)
        return None

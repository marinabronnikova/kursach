from django.core.mail import send_mail

from finance import settings


def send_staff_invitation(user_email, password, company_name):
    send_mail(
        'Приглашение сотрудника',
        f'Вы были приглашены в систему, компании - {company_name}.\n'
        f'Используете следующие данные для входа:\n'
        f'Email - {user_email},\n'
        f'Пароль - {password}\n',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )



from django.core.mail import send_mail

from finance import settings


def send_customer_invoice(company, invoice):
    products_details = (f"{item.product.name}, цена - {item.price}, кол-во - {item.amount}.\n " for item in invoice.payment_items.all())
    products_details = ''.join(products_details)
    send_mail(
        'Оплата счета',
        f'Продукты и услуги:\n'
        f'{products_details}'
        f'Общая цена - {invoice.total_price} BYN.\n'
        f'Используете следующие данные для оплаты:\n'
        f'Название банка - {company.bank_detail.name},\n'
        f'Адрес - {company.bank_detail.address}\n'
        f'Банковский счет - {company.bank_detail.bank_number},\n'
        f'Расчетный счет для оплаты - {company.bank_detail.settlement_account},\n'
        f'Доп. информация - {company.bank_detail.details}.\n'
        ,
        settings.EMAIL_HOST_USER,
        [invoice.organization.email],
        fail_silently=False,
    )



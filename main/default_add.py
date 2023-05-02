import datetime
import calendar
from .models import *

def default_add_month():
    clients = Client.objects.all()
    for client in clients:
        last_month = (str(client.months.last().created))[:7]
        this_month = str(datetime.date.today())[:7]
        if last_month != this_month:
            now = datetime.datetime.now()
            today = int(now.strftime("%d"))
            month_days = calendar.monthrange(int(now.strftime("%Y")), int(now.strftime("%m")))[1]
            res_days = month_days - today
            if res_days >= client.coming_type.days:
                coming_days = client.coming_type.days
                price = client.coming_type.price
                client.debt = True
                client.save()
            else:
                client.debt = True
                client.save()
                daily_price = client.coming_type.price / client.coming_type.days
                coming_days = res_days
                price = daily_price * coming_days
            month = Month.objects.create(
                client=client,
                coming_days=coming_days,
                payment=int(price)
            )



def default_add_day():
    clients = Client.objects.all()
    for client in clients:
        try:
            if client.months.last().coming_days > client.months.all().last().days.filter(came=True).count():
                m = client.months.all().last()
                if m.payment == 0 or m.payment < client.coming_type.price or m.payed == True  :
                    month = client.months.last() 
                    month.came = client.months.all().last().days.filter(came=True).count()
                    month.save()
                    today = datetime.date.today()
                    day = Day.objects.get_or_create(
                        month=month,date=today
                    )
        except:
            pass
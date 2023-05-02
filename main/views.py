from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from .models import *
import datetime
import calendar
from django.contrib import messages
from .filter import deco_login ,deco_login_fun

from .default_add import *


def add_day(request):
    default_add_day()
    return {"day":'added'}


def add_month(request):
    default_add_month()
    return {"month":'added'}



class HomeView(View):
    @deco_login
    def get(self,request):
        inactive = 0
        active = 0
        paused = 0
        daily_sum = 0
        expense_sum = 0
        now = datetime.datetime.now()

        clients = Client.objects.all()
        all_clients = clients.count()
        payment = Payment.objects.all().order_by("-id")
        day = Day.objects.filter(came=True,date=now).count()
        pay = payment.filter(date=now)
        expense= Expense.objects.filter(created=now)
        
        for e in expense:
            expense_sum += e.summa
    
        for p in pay:
            daily_sum += p.money
            
        total_sum = daily_sum - expense_sum
        
      
        for c in clients:
            if c.status == "ACTIVE":
                active += 1
            elif c.status == "INACTIVE":          
                inactive += 1
            else:
                paused += 1
        
        context = {
            "all_clients":all_clients,
            "came_day":day,
            "active":active,
            "inactive":inactive,
            "paused":paused,
            "payment":payment,
            'daily_sum':daily_sum,
            'expense_sum':expense_sum,
            'total_sum':total_sum,
            'now':now

        }
        
        return render (request,'index.html',context)


class RegisterView(View):
    @deco_login
    def get(self,request):
        tarif =  ComingType.objects.all()

        context = {'tarif':tarif}
        return render(request,'register.html',context)

    def post(self,request):
        user = request.user
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        ctypes = request.POST.get('tarif')
        if user and name and phone and ctypes:
            ctype = ComingType.objects.get(title=ctypes)
            status = request.POST.get('status')
            for c in Client.objects.all():
                if phone == c.phone:
                    messages.error(request, "Xatolik !!! Bu telefon raqam oldin ro'yxatdan o'tgan.")
                    return redirect('/register')
                else:
                    pass
            client = Client.objects.create(
                        user=user,
                        name=name,
                        phone=phone,
                        coming_type=ctype,
                        status=status,
                    )

            # month create

            now = datetime.datetime.now()
            today = int(now.strftime("%d"))
            month_days = calendar.monthrange(int(now.strftime("%Y")), int(now.strftime("%m")))[1]
            res_days = month_days - today
            if res_days >= client.coming_type.days:
                coming_days = client.coming_type.days
                price = client.coming_type.price
            else:
                daily_price = client.coming_type.price / client.coming_type.days
                coming_days = res_days
                price = daily_price * coming_days
            sunday = coming_days // 7
            # coming_days -= sunday
            month = Month.objects.create(
                client=client,
                coming_days=coming_days,
                payment=int(price)
            )
            
            tarifs =  ComingType.objects.all()
            context = {'tarif':tarifs,'client':client, "uid":client.uid,"name":client.name}
            messages.success(request, "Mijoz ro'yxatga olindi !")
            return render(request=request, template_name='register.html',context=context)
        else:
            messages.success(request, "Xatolik qaytadan harakat qiling ! ")
            tarifs = ComingType.objects.all()
            context = {'tarif':tarifs, "status":"Nimadur noto`g`ri ketdi"} 
            return render(request,'register.html', context)




class DetailView(View):
    @deco_login

    def get(self, request, id):

        queryset = Client.objects.get(id=id)
        months = Month.objects.filter(client=queryset).order_by("-id")
        payment = months
        tarif = ComingType.objects.all()
        month = queryset.months.all().last()
        month.came = queryset.months.all().last().days.filter(came=True).count()
        month.save()
        if queryset.coming_type.days == 1:
            month = queryset.months.all().last()
            month.payment =  queryset.coming_type.price
            month.save()
        return render(request, "detail.html", {"client":queryset, "months":months, "tarifs":tarif})

    def post(self, request, id):
        if request.POST.get('delete'):
            client = Client.objects.filter(id=int(id))
            client.delete()
            messages.success(request, "Mijoz ro'yxatdan o'chirildi !")
            return redirect("main:list_client")
        else:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            status = request.POST.get('status')
            tarifs = request.POST.get('tarif',False)
           
            client = Client.objects.get(id=id)
            client.name = name
            client.phone = phone
            client.status = status
            if tarifs:
                tarif = ComingType.objects.filter(title=tarifs)[0]
                client.coming_type = tarif
                client.coming_type.days
                month = Month.objects.filter(client=client.id).last()
                month.coming_days = client.coming_type.days
                month.payment = client.coming_type.price
                month.came = 0
                month.payed = False
                month.save()
            client.save()
        return redirect(f"/detail/{id}")

@deco_login_fun
def edit_day(request, day_id):
    day = get_object_or_404(Day, id=day_id)
    client =day.month.client.months.all().last().client
    resp = request.GET.get('day_result')
    if resp == "true":
        day.came = True
        day.save()
        if client.coming_type.days == 1:
            month = client.months.all().last()
            month.payment =  client.coming_type.price
            month.coming_days = month.days.filter(came= True).count()
            month.save()
        return JsonResponse({"came":"True"})
    if resp == "false":
        day.came = False
        day.save()
        return JsonResponse({"came":"False"})
    else:
        return JsonResponse({"came":"not valid"})

@deco_login_fun
def barcode_came(request, uid):
    try:
        client = get_object_or_404(Client, uid=uid)
        day = client.months.last().days.last()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if str(today) == str(day):
            day.came = True
            day.save()
            if client.coming_type.days == 1:
                month = client.months.all().last()
                month.payment =  client.coming_type.price
                month.coming_days = month.days.filter(came= True).count()
                month.save()

            status = f"{client.name} bugun mashg'ulotga keldi."
        else:
            status = f"{client.name} avval to'lovni amalga oshiring!"
        kelgan_kunlari = day.month.client.months.all().last().days.all().filter(came=True).count()+1
        if client.months.all().last().coming_days <= kelgan_kunlari:
            client.debt = True
            client.save()
    except:
        status = "UID noto`g`ri"
    return JsonResponse({"status":status})


class DavomatView(View):
    @deco_login

    def get(self,request):
        today = datetime.datetime.today()

        queryset = Client.objects.all().order_by("-id")
        tarif = ComingType.objects.all()
        data = {
            "clients":queryset,
            "tarif":tarif,
            'today':today

        }
        return render (request,'new_table.html', data)


class PaymentView(View):
    @deco_login
    def get(self, request):
        try:
            client_id = request.GET['client_id']
            client = Client.objects.get(uid=client_id)
            month = Month.objects.filter(client=client).last()
            data = {
                "name":client.name,
                "uid":client.uid,
                "payment":month.payment,
                "balance":client.balance

            }

            return JsonResponse(data)
        except:
            clients = Client.objects.all()
            return render(request, 'forms-layouts.html', {"clients":clients})

    def post(self, request):
        clients = Client.objects.all()
        uid = request.POST.get('uid')
        payment = int(request.POST.get('payment'))
        discount = int(request.POST.get('discount'))
        balance = int(request.POST.get('balance',0))
        discounted = payment + discount + balance

        try:
            obj = get_object_or_404(Client, uid=uid)
        except:
            obj = False
        if obj == False:
            return render(request, 'forms-layouts.html', {"response":"ID noto`g`ri berildi","status":"danger","clients":clients})
        else:
            month = Month.objects.filter(client=obj).last()
            if month.payment <= discounted:
                balances =  payment - month.payment
                if balances > 0:
                    obj.balance += balances
                if balance :
                    obj.balance -= balance

                month.payment = 0
                month.payed = True
                obj.debt = False

            else:
                month.payment -= discounted
                if balance :
                    obj.balance -= balance
                month.payed = False
                obj.debt = True
            month.save()
            obj.save()

            Payment.objects.create(
                month=month,
                money=payment,
                discount=discount,
            )
            today = datetime.date.today()
            Day.objects.get_or_create(
                    month=month,date=today
                    )
            messages.success(request, "To'lov amalga oshirildi ! ")
            if obj.coming_type.days == 1:
                m = obj.months.all().last()
                m.coming_days = obj.months.all().last().days.filter(came= True).count()+1
                m.save()
            return redirect('/payment')

@deco_login_fun
def detail_payment(request):
    month_id = int(request.POST.get('month_id'))
    payment = int(request.POST.get('payment'))
    month = Month.objects.get(id=month_id)

    obj = month.client
    balance = obj.balance
    py  = payment + balance
    if month.payment == py:
        month.payment = 0
        month.payed = True
        obj.debt = False
        obj.balance -= balance
    elif month.payment < payment:
        balance = payment - month.payment
        month.payment = 0
        month.payed = True
        obj.debt = False
        obj.balance += balance
    else:
        month.payment -= payment
        month.payed = False
        obj.debt = True
    month.save()
    today = datetime.date.today()
    if obj.coming_type.days == 1:
        m = obj.months.all().last()
        m.coming_days = obj.months.all().last().days.filter(came= True).count()+1
        m.save()
    Day.objects.get_or_create(
                    month=month,date=today
                    )
    obj.save()
    Payment.objects.create(
        month=month,
        money=payment
    )
    return JsonResponse({"status":"ok"})

def detail_month_sum(request):
    month_id = request.GET.get('id')
    month = Month.objects.get(id=month_id)
    balance = month.client.balance
    payment = month.payment
    return JsonResponse({'payment':payment-balance})

def handler_404(request,exception):
    return render(request, "404.html")

def handler_500(request):
    return render(request, "500.html")


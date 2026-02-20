from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection,IntegrityError
from django.contrib import auth
from decimal import Decimal, ROUND_HALF_UP
import json

# Create your views here.
def index(request):
    user_id = request.session.get('user_id')
    if not user_id:
       return redirect ("users:login")
    with connection.cursor() as cursor:

        cursor.execute("""SELECT p.portfolio_id,p.quantity,p.purchase_price,p.date_added,e.symbol, e.equity_name,e.type,e.current_price
            FROM personal_portfolio p
            JOIN global_equities e
            ON p.equity_id = e.equity_id
            WHERE p.user_id = %s""",
            [user_id])
        holdings = cursor.fetchall()
        cursor.execute("SELECT username from users where user_id = %s",[user_id])
        user_row = cursor.fetchone()
    connection.commit()
    username = user_row[0]
    holding_list = []
    total_p_l=total_invest=total_current=total_prcnt = 0
    for holding in holdings:
        hold = (
            {"id":holding[0],
             "quantity":holding[1],
             "purchase_price":round(holding[2],2),
             "date_added":holding[3],
             "symbol":holding[4],
             "name":holding[5],
             "type":holding[6],
             "current_price":round(holding[7],2),
             "profit_loss": holding[1]*(holding[7]-holding[2]),
             "percentage":round(((holding[7]-holding[2])*(100))/holding[2],2)}
        )
        hold['invest_value'] = hold['quantity']*hold['purchase_price']
        hold['current_value'] = hold['quantity']*hold['current_price']
        total_p_l += round(hold['profit_loss'],2)
        total_invest += round(hold['quantity']*hold['purchase_price'],2)
        total_current+= round(hold['quantity']*hold['current_price'],2)
        total_prcnt = round( ((total_current - total_invest) * 100) / total_invest, 2)
        holding_list.append(hold)
    print(holding_list)
    context = {
        'username': username,
        'holdings':holding_list,
        'total_p_l':total_p_l,
        'invest':total_invest,
        'current':total_current,
        'total_prcnt':total_prcnt
    }
    return render(request, "portfolio/overview.html",context)


def delete_holding(request,portfolio_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error':'Not Authenticated',
                             'redirect':'/login/'},status = 401)
    
    with connection.cursor() as cursor:
        cursor.execute("""
                SELECT user_id FROM Personal_Portfolio
                WHERE portfolio_id = %s
        """,[portfolio_id])
        result = cursor.fetchone()

        if not result:
            return JsonResponse({'error':'Holding not found'},status = 404)
        
        if result[0]!=user_id:
            return JsonResponse({'error':'Not Authorized'},status = 403)
        
        cursor.execute("""
                       DELETE FROM Personal_Portfolio
                       WHERE portfolio_id = %s
                    """,[portfolio_id])
    return JsonResponse({'success':True,'message':'Holding deleted successfully'})

def edit_holding(request, portfolio_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error':'Not Authenticated',
                             'redirect':'/login/'},status = 401)
    
    data = json.loads(request.body)
    quantity = data.get('quantity')
    if quantity is None or float(quantity)<=0:
        return JsonResponse({'error':'Invalid quantity'},status=400)
    
    with connection.cursor() as cursor:
        cursor.execute(""" SELECT user_id, purchase_price,equity_id FROM Personal_Portfolio
                       WHERE portfolio_id = %s  
        """,[portfolio_id])
        result = cursor.fetchone()

        if not result:
            return JsonResponse({'error':'Holding not found'},status= 404)
        
        if result[0]!=user_id:
            return JsonResponse({'error':'Not Authorized'},status = 403)
        
        purchase_price = float(result[1])
        equity_id = result[2]

        cursor.execute(""" UPDATE Personal_Portfolio 
                        SET quantity = %s WHERE portfolio_id = %s 
        """,[quantity,portfolio_id])
    
        cursor.execute(""" SELECT current_price,equity_name,type FROM global_equities WHERE equity_id = %s
                    """,[equity_id])
        equity = cursor.fetchone()
        current_price = float(equity[0])
        equity_name = equity[1]
        equity_type = equity [2]

        profit_loss = (current_price-purchase_price)*float(quantity)
        percentage = ((current_price-purchase_price)*100)/purchase_price

        if percentage >=0:
            percentage_html = f"<span class = 'text-green-500 flex items-center justify-end space-x-1'></span>{round(percentage,2)}%</span><i class='fa-solid fa-arrow-trend-up'></i></span>"
        else:
            percentage_html = f"<span class = 'text-red-500 flex items-center justify-end space-x-1'></span>{round(percentage,2)}%</span><i class='fa-solid fa-arrow-trend-down'></i></span>"

        cursor.execute("""SELECT p.quantity,p.purchase_price,e.current_price FROM 
                       personal_portfolio p
                       JOIN global_equities e ON p.equity_id = e.equity_id
                       WHERE p.user_id = %s""",[user_id])
        
        all_holdings = cursor.fetchall()
        totalInvest = sum(h[0]*h[1] for h in all_holdings)
        totalCurrent = sum(h[0]*h[2] for h in all_holdings)
        totalPL = totalCurrent-totalInvest
        totalPercent = (totalPL*100)/totalInvest if totalInvest!=0 else 0
    
    return JsonResponse({
        'success': True,
        'newQuantity': float(quantity),
        'profit_loss': round(profit_loss,2),
        'percentage_html': percentage_html,
        'cards': {
            'totalInvest': round(totalInvest,2),
            'totalCurrent': round(totalCurrent,2),
            'totalPL': round(totalPL,2),
            'totalPercent': round(totalPercent,2)
        }
    })


def portfolio_chart(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error':'Not Authenticated',
                             'redirect':'/login/'},status = 401)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                ph.price_date,
                SUM(pp.quantity * ph.price) as total_value
            FROM Personal_Portfolio pp
            JOIN (
                SELECT 
                    equity_id,
                    DATE(recorded_at) as price_date,
                    price
                FROM equity_price_history eph1
                WHERE recorded_at = (
                    SELECT MAX(recorded_at)
                    FROM equity_price_history eph2
                    WHERE eph2.equity_id = eph1.equity_id
                    AND DATE(eph2.recorded_at) = DATE(eph1.recorded_at)
                )
                AND DATE(recorded_at) >= CURRENT_DATE - INTERVAL '30 days'
            ) ph ON pp.equity_id = ph.equity_id
            WHERE pp.user_id = %s
            GROUP BY ph.price_date
            ORDER BY ph.price_date ASC
        """, [user_id])
        history = cursor.fetchall()


        chart_data = {
            'dates':[row[0].strftime('%b %d') for row in history],
            'values':[float(row[1]) for row in history]
        }
    
    return JsonResponse(chart_data)
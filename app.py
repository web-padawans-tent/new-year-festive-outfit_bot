import json
import json
import os
import time
from datetime import datetime, timedelta

from flask import Flask, render_template_string, request, jsonify

from functions import generate_merchant_signature, extract_user_id_from_reference, add_user_to_channel, \
    generate_signature, delete_user_from_channel, get_table_data, get_table_names
from loader import MERCHANT_ACCOUNT, MERCHANT_DOMAIN, db

app = Flask(__name__)


@app.route('/')
def index():
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kosovska</title>
<style>
* {
margin: 0;
padding: 0;
box-sizing: border-box;
}

body {
display: flex;
justify-content: center;
align-items: center;
height: 100vh;
background-color: #ffffff;
font-family: Arial, sans-serif;
}

.container {
display: flex;
width: 90%;
max-width: 600px;
flex-direction: column;
align-items: center;
gap: 20px;
background-color: #eeeeee;
padding: 40px;
border-radius: 10px;
box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.btn {
width: 100%;
display: inline-block;
padding: 15px 15px;
border-radius: 50px;
border: 1px solid #050505;
text-decoration: none;
text-align: center;
font-size: 18px;
font-weight: bold;
color: #050505;
cursor: pointer;
transition: background-color 0.3s ease;
}
.lookbook__btn{
    background-color: #000000;
    border: 1px solid #ffffff;
}
.lookbook__btn_white {
    color: #ffffff;
}
.lookbook__btn_red {
    color: #b84b27;
}
</style>
</head>
<body>

<div class="container">
<a href="https://t.me/sveta_kosovska" class="btn btn-telegram">Telegram</a>
<a href="https://www.instagram.com/sveta_kosovska" class="btn btn-instagram">Instagram</a>
<a href="https://t.me/+D6AUy8eFDxQ1YTQy" class="btn lookbook__btn lookbook__btn_red">Festive Lookbook</a>       
<a href="https://t.me/+i8D-g8m5_Ak2MDNi" class="btn lookbook__btn lookbook__btn_white">LookBook</a>
<a href="https://ssk24test.my.canva.site/daglhozlvg0" class="btn btn-other">Ціни на послуги</a>
<a href="https://t.me/kosovskamanager" class="btn btn-support">Підтримка</a>
</div>

</body>
</html>

    """
    return render_template_string(html_template)


@app.route('/tables', methods=['GET'])
def show_tables_data():
    try:
        # Получаем список всех таблиц
        table_names = get_table_names()

        all_tables_data = {}

        # Для каждой таблицы получаем данные и добавляем их в результат
        for table in table_names:
            all_tables_data[table] = get_table_data(table)

        return jsonify(all_tables_data), 200  # Возвращаем все данные таблиц в формате JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Возвращаем ошибку, если она произошла

@app.route('/payment_callback', methods=['POST'])
def callback():
    data_str = request.form.to_dict()
    data_json_str = list(data_str.keys())[0]  # Отримуємо перший ключ
    data = json.loads(data_json_str)
    order_reference = data['orderReference']
    processing_time = int(time.time()) 
    status = data.get('accept')
    user_id = extract_user_id_from_reference(order_reference)
    signature = generate_signature(order_reference, status, processing_time)

    if data.get("transactionStatus") == "Approved":
        paymentSys = data['paymentSystem']

        if not db.get_subs(user_id):
            add_user_to_channel(user_id)
            db.add_subs(user_id, paymentSys)
        else:
            db.update_subs(user_id)

        response = {
            "orderReference": order_reference,
            "status": status,
            "time": processing_time,
            "signature": signature        
            }

        return jsonify(response), 200
    elif status in ["Declined", "Expired", "Refunded"]:
        if db.get_subs(user_id):
            delete_user_from_channel(user_id)
            db.delete_subs(user_id)

        response = {
            "orderReference": order_reference,
            "status": status,
            "time": processing_time,
            "signature": signature
        }

        return jsonify(response), 200
    else:
        return jsonify({"response": "Payment failed!"}), 400

    print(data)
    return "200"

@app.route('/pay/<int:user_id>')
def pay(user_id):
    amount = 699
    currency = "UAH"
    product_name = ["Subscription to Telegram Channel"]
    product_price = [amount]
    product_count = [699]
    order_date = int(time.time())
    order_reference = f"invoice_{user_id}_{order_date}"

    # Генеруємо підпис
    signature = generate_merchant_signature(
        MERCHANT_ACCOUNT,
        MERCHANT_DOMAIN,
        order_reference,
        order_date,
        amount,
        currency,
        product_name,
        product_price,
        product_count
    )

    html_content = f"""
        <html>
          <body>
            <form id="wayforpay_form" action="https://secure.wayforpay.com/pay" method="POST">
                <input type="hidden" name="merchantAccount" value="{MERCHANT_ACCOUNT}">
                <input type="hidden" name="merchantDomainName" value="{MERCHANT_DOMAIN}">
                <input type="hidden" name="serviceUrl" value="{MERCHANT_DOMAIN}/payment_callback">
                <input type="hidden" name="orderReference" value="{order_reference}">
                <input type="hidden" name="orderDate" value="{order_date}">
                <input type="hidden" name="amount" value="{amount}">
                <input type="hidden" name="currency" value="{currency}">
                <input type="hidden" name="productName[]" value="{product_name[0]}">
                <input type="hidden" name="productPrice[]" value="{product_price[0]}">
                <input type="hidden" name="productCount[]" value="{product_count[0]}">
                <input type="hidden" name="merchantSignature" value="{signature}">
                <input type="submit" value="Оплатити">
            </form>
    
            <script type="text/javascript">
                document.getElementById('wayforpay_form').submit();
            </script>
          </body>
        </html>
    """
    return render_template_string(html_content)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 80))
    app.run(debug=True, host='0.0.0.0', port=port)
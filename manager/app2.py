from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app=app)


@app.route('/')
def index():
    response = requests.get('http://localhost:8080/view-order')
    total = 0
    if response.status_code == 200:
        order_list: list = response.json()
        for order in order_list:
            for food in order["foods"]:
                price = float(food["price"])
                if price:
                    total += price

        return {"total": total}


if __name__ == '__main__':
    app.run(debug=True, port=8090)

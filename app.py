from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, make_response, request, jsonify


app = Flask(__name__)
CORS(app=app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mysecretpassword@localhost/postgres'
db = SQLAlchemy(app)


order_foods = db.Table('order_foods',
                       db.Column('order_id', db.Integer, db.ForeignKey(
                           'order.id'), primary_key=True),
                       db.Column('food_id', db.Integer, db.ForeignKey(
                           'foods.id'), primary_key=True)
                       )


class EatingTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    available = db.Column(db.Boolean, default=True, nullable=False)
    waiter_id = db.Column(
        db.Integer, db.ForeignKey('waiter.id'), nullable=True)
    waiter = db.relationship('Waiter', back_populates='tables')
    orders = db.relationship('Order', back_populates='table')

    def as_dict(self):
        return {"id": self.id,
                "available": self.available}


class Waiter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tables = db.relationship('EatingTable', back_populates='waiter', lazy=True)

    def as_dict(self):
        return {"id": self.id,
                "name": self.name}


class Foods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship(
        'Order', secondary=order_foods, back_populates='foods')

    def as_dict(self):
        return {"id": self.id,
                "name": self.name,
                "price": self.price}


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('eating_table.id'))
    active = db.Column(db.Boolean, default=True, nullable=False)
    table = db.relationship('EatingTable', back_populates='orders')
    foods = db.relationship(
        'Foods', secondary=order_foods, back_populates='orders')
    datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def as_dict(self):
        food_list = [{"id": food.id, "name": food.name,
                      "price": food.price} for food in self.foods]
        return {
            "id": self.id,
            "table_id": self.table_id,
            "datetime": self.datetime,
            "active": self.active,
            "foods": food_list
        }


with app.app_context():
    db.drop_all()
    db.create_all()

    waiter1 = Waiter(name='John Waiter')
    db.session.add(waiter1)

    table1 = EatingTable()
    table2 = EatingTable()
    db.session.add(table1)
    db.session.add(table2)

    food1 = Foods(name='Pizza', price=10.99)
    food2 = Foods(name='Burger', price=8.49)
    db.session.add(food1)
    db.session.add(food2)

    waiter1.tables.append(table1)
    db.session.commit()

    db.session.commit()


@app.route('/foods', methods=['GET'])
def foods():
    return [food.as_dict() for food in Foods.query.all()]


@app.route('/tables', methods=['GET'])
def tables():
    tables_data = [table.as_dict()
                   for table in EatingTable.query.all() if table.available == True]
    response = jsonify(tables_data)
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route('/add-order', methods=['POST'])
def create_order():
    try:
        table_id = request.json['table_id']
    except Exception:
        return jsonify({"error": "Invalid table ID"}), 400

    table: EatingTable = next(
        (table for table in EatingTable.query.all() if table.id == table_id), None)

    if not table:
        return jsonify({"error": "Table not found"}), 404

    if table.available == False:
        return jsonify({"error": "Table is not available"}), 404
    table.available = False
    new_order = Order(table=table)
    db.session.add(table)
    db.session.add(new_order)
    db.session.commit()

    return jsonify(new_order.as_dict()), 201


@app.route('/add-food', methods=['POST'])
def add_foods_to_order():
    try:
        food_id = request.json['food_id']
        order_id = request.json['order_id']
    except Exception:
        return jsonify({"error": "Invalid table ID"}), 400

    food: Foods = next(
        (food for food in Foods.query.all() if food.id == food_id), None)
    order: Order = next(
        (order for order in Order.query.all() if order.id == order_id), None)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    if not food:
        return jsonify({"error": "Food not found"}), 404

    order.foods.append(food)
    db.session.commit()

    return jsonify(order.as_dict()), 200


@app.route('/remove-food', methods=['POST'])
def remove_foods_from_order():
    try:
        food_id = request.json['food_id']
        order_id = request.json['order_id']
    except Exception:
        return jsonify({"error": "Invalid table ID"}), 400

    order: Order = next(
        (order for order in Order.query.all() if order.id == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.foods = [food for food in order.foods if food.id != food_id]
    db.session.commit()

    return jsonify(order.as_dict()), 200


@app.route('/view-order', methods=['GET'])
def view_order():
    try:
        order_id = request.json['order_id']
    except Exception:
        return [order.as_dict() for order in Order.query.all()], 200

    order: Order = next(
        (order for order in Order.query.all() if order.id == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order.as_dict()), 200


@app.route('/close-order', methods=['POST'])
def close_order():
    try:
        order_id = request.json['order_id']
    except Exception:
        return jsonify({"error": "Invalid Order ID"}), 400

    order: Order = next(
        (order for order in Order.query.all() if order.id == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    order.active = False

    db.session.add(order)
    db.session.commit()
    return jsonify(order.as_dict()), 200


@app.route('/', methods=['GET'])
def index():
    return "hello"

if __name__ == '__main__':
    app.run(debug=True, port=8080)

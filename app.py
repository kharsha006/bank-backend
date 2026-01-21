import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import (
    init_db,
    get_connection
)

app = Flask(__name__)
CORS(app)

# Initialize database when server starts
init_db()


def get_balance_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM account WHERE id = 1")
    balance = cursor.fetchone()[0]
    conn.close()
    return balance


def update_balance(new_balance):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE account SET balance = ? WHERE id = 1",
        (new_balance,)
    )
    conn.commit()
    conn.close()


def add_transaction(tx_type, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (type, amount) VALUES (?, ?)",
        (tx_type, amount)
    )
    conn.commit()
    conn.close()


@app.route("/balance", methods=["GET"])
def get_balance():
    balance = get_balance_from_db()
    return jsonify({"balance": balance})


@app.route("/deposit", methods=["POST"])
def deposit():
    data = request.get_json()
    amount = data.get("amount", 0)

    if amount <= 0:
        return jsonify({"error": "Invalid deposit amount"}), 400

    balance = get_balance_from_db()
    balance += amount

    update_balance(balance)
    add_transaction("DEPOSIT", amount)

    return jsonify({
        "message": "Deposit successful",
        "balance": balance
    })


@app.route("/withdraw", methods=["POST"])
def withdraw():
    data = request.get_json()
    amount = data.get("amount", 0)

    if amount <= 0:
        return jsonify({"error": "Invalid withdrawal amount"}), 400

    balance = get_balance_from_db()

    if amount > balance:
        return jsonify({"error": "Insufficient funds"}), 400

    balance -= amount

    update_balance(balance)
    add_transaction("WITHDRAW", amount)

    return jsonify({
        "message": "Withdrawal successful",
        "balance": balance
    })

@app.route("/transactions", methods=["GET"])
def get_transactions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT type, amount FROM transactions ORDER BY id DESC"
    )
    rows = cursor.fetchall()

    conn.close()

    transactions = []
    for row in rows:
        transactions.append({
            "type": row[0],
            "amount": row[1]
        })

    return jsonify(transactions)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

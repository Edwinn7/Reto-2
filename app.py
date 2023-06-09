from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import random

app = Flask(__name__)

# Configuracion de la conexion a la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="BancoDB"
)


@app.route("/", methods=["GET", "POST"])
def home():
    mensaje = None  # mensaje en None

    if request.method == "POST":
        numero_cuenta = request.form["numero_cuenta"]

        cursor = db.cursor()

        # Ver si la cuenta existe
        cursor.execute(
            "SELECT COUNT(*) FROM Cuentas WHERE numero_cuenta = %s", (numero_cuenta,))
        cuenta_existe = cursor.fetchone()[0]

        cursor.close()

        if cuenta_existe:
            return redirect("/transacciones")
        else:
            mensaje = "La cuenta no existe. Intente nuevamente."

    return render_template("index.html", mensaje=mensaje)


@app.route("/registro", methods=["POST"])
def registro():
    titular = request.form["titular"]
    tipo_cuenta = request.form.get("tipo_cuenta")
    saldo = request.form["saldo"]
    cursor = db.cursor()

    # Verificar si el campo "tipo_cuenta" está presente
    if tipo_cuenta is None:
        mensaje = "Error: Tipo de cuenta no especificado."
        return render_template("index.html", mensaje=mensaje)

    # Generar un numero de cuenta al azar de 10 dígitos
    numero_cuenta = generar_numero_cuenta(cursor)

    # Insertar el nuevo usuario en la tabla Cuentas
    cursor.execute("INSERT INTO Cuentas (numero_cuenta, titular, tipo_cuenta, saldo) VALUES (%s, %s, %s, %s)",
                   (numero_cuenta, titular, tipo_cuenta, saldo))
    db.commit()

    cursor.close()

    mensaje = "Cuenta creada con éxito."
    return redirect(url_for("transacciones", cuenta_origen=numero_cuenta))


def generar_numero_cuenta(cursor):
    # Generar un numero de cuenta al azar de 10 digitos que no exista en la base de datos al crear el usuario
    while True:
        numero_cuenta = ''.join(random.choices("0123456789", k=10))
        cursor.execute(
            "SELECT COUNT(*) FROM Cuentas WHERE numero_cuenta = %s", (numero_cuenta,))
        cuenta_existe = cursor.fetchone()[0]
        if cuenta_existe == 0:
            break
    return numero_cuenta

# Ruta para el formulario de transacciones


@app.route("/transacciones", methods=["GET", "POST"])
def transacciones():
    if request.method == "POST":
        cuenta_destino = request.form["cuenta_destino"]
        cuenta_origen = request.form["cuenta_origen"]
        valor = float(request.form["valor"])
        tipo_transaccion = request.form.get("tipo_transaccion")
        cursor = db.cursor()

        if tipo_transaccion is None:
            mensaje = "Error: Tipo de transacción no especificado."
            return render_template("transacciones.html", mensaje=mensaje)

        # Obtener saldo de la cuenta origen
        cursor.execute(
            "SELECT saldo FROM Cuentas WHERE numero_cuenta = %s", (cuenta_origen,))
        saldo_origen = cursor.fetchone()

        if saldo_origen is None:
            mensaje = "La cuenta de origen no existe. Intente nuevamente."
            cursor.close()
            return render_template("transacciones.html", mensaje=mensaje)
        else:
            saldo_origen = saldo_origen[0]

        if saldo_origen >= valor:
            # Buscar la transacción en la tabla Tipo_Transaccion
            cursor.execute(
                "SELECT id FROM Tipo_Transaccion WHERE descripcion = %s", (tipo_transaccion,))
            tipo_transaccion_id = cursor.fetchone()

            if tipo_transaccion_id is None:
                # Si no existe, insertarla en la tabla Tipo_Transaccion
                cursor.execute(
                    "INSERT INTO Tipo_Transaccion (descripcion) VALUES (%s)", (tipo_transaccion,))
                db.commit()
                tipo_transaccion_id = cursor.lastrowid
            else:
                tipo_transaccion_id = tipo_transaccion_id[0]

            # Realizar transaccion
            cursor.execute(
                "UPDATE Cuentas SET saldo = saldo - %s WHERE numero_cuenta = %s", (valor, cuenta_origen))
            cursor.execute(
                "UPDATE Cuentas SET saldo = saldo + %s WHERE numero_cuenta = %s", (valor, cuenta_destino))

            cursor.execute("INSERT INTO Movimientos (valor, numero_cuenta, cuenta_origen, fecha, tipo_transaccion_id) VALUES (%s, %s, %s, NOW(), %s)",
                           (valor, cuenta_destino, cuenta_origen, tipo_transaccion_id))

            db.commit()
            mensaje = "Transacción realizada con éxito."
        else:
            mensaje = "Saldo insuficiente para realizar la transacción."

        cursor.close()
        return render_template("transacciones.html", mensaje=mensaje)
    else:
        return render_template("transacciones.html")


# Ruta para cancelar una cuenta
@app.route("/cancelar_cuenta", methods=["POST"])
def cancelar_cuenta():
    numero_cuenta = request.form["numero_cuenta"]

    cursor = db.cursor()

    # Obtener saldo actual de la cuenta
    cursor.execute(
        "SELECT saldo FROM Cuentas WHERE numero_cuenta = %s", (numero_cuenta,))
    saldo_actual = cursor.fetchone()

    if saldo_actual is None:
        mensaje = "La cuenta no existe. Intente nuevamente."
    else:
        saldo_actual = saldo_actual[0]
        # Actualizar el saldo de la cuenta a cero
        cursor.execute(
            "UPDATE Cuentas SET saldo = 0 WHERE numero_cuenta = %s", (numero_cuenta,))
        db.commit()

        mensaje = f"La cuenta {numero_cuenta} ha sido cancelada. El saldo actual era {saldo_actual}."

    cursor.close()

    return render_template("transacciones.html", mensaje=mensaje)


# evitar reiniciar la consola cada vez que realizas cambios
if __name__ == '__main__':
    app.run(debug=True)
from django.shortcuts import render
import mysql.connector


# Create your views here.


def normalization(cursor, table, column, val, reverse=False):
    cursor.execute(f"SELECT MAX({column}) FROM {table}")
    max_val = 0
    min_val = 0
    for x in cursor:
        max_val = x[0]
    cursor.execute(f"SELECT MIN({column}) FROM  {table}")
    for x in cursor:
        min_val = x[0]
    if reverse:
        return 1 - ((val - min_val) / (max_val - min_val))
    return (val - min_val) / (max_val - min_val)


def date_normalization(cursor, val):
    cursor.execute(f"SELECT MAX(DATEDIFF(CURDATE(),DATA_POWSTANIA)) FROM MIESZKANIA")
    max_val = 0
    min_val = 0
    for x in cursor:
        max_val = x[0]
    cursor.execute(f"SELECT MIN(DATEDIFF(CURDATE(),DATA_POWSTANIA)) FROM MIESZKANIA")
    for x in cursor:
        min_val = x[0]
    cursor.execute(f"SELECT DATEDIFF(CURDATE(),'{val}')")
    for x in cursor:
        val = x[0]
    return 1 - ((val - min_val) / (max_val - min_val))


def indicator(cursor, cursor2, meters, cost, traffic, safety, busy, transport, age):
    cursor.execute(
        "SELECT P.NR_OFERTY, P.METRY, P.CENA, P.DATA_POWSTANIA, Z.RUCH, Y.ZALUDNIENIE,Y.BEZPIECZENSTWO, Y.KOMUNIKACJA FROM  "
        "MIESZKANIA P  JOIN ULICE Z  ON  P.ID_ULICA = Z.ID  JOIN DZIELNICE Y ON Z.DZIELNICA=Y.NAZWA")
    sums = []
    indexes = []
    for x in cursor:
        a1 = normalization(cursor2, 'MIESZKANIA', 'METRY', int(x[1])) * meters
        a2 = normalization(cursor2, 'MIESZKANIA', 'CENA', int(x[2]), reverse=True) * cost
        a3 = date_normalization(cursor2, x[3]) * age
        a4 = normalization(cursor2, 'ULICE', 'RUCH', int(x[4])) * traffic
        a5 = normalization(cursor2, 'DZIELNICE', 'ZALUDNIENIE', int(x[5]), reverse=True) * busy
        a6 = normalization(cursor2, 'DZIELNICE', 'BEZPIECZENSTWO', int(x[6])) * safety
        a7 = normalization(cursor2, 'DZIELNICE', 'KOMUNIKACJA', int(x[7])) * transport

        sum1 = float(a1) + float(a2) + float(a3) + float(a4) + float(a5) + float(a6) + float(a7)
        sums.append(sum1)
        indexes.append(int(x[0]))

    for k in range(0, len(sums)):
        cursor.execute(f"UPDATE MIESZKANIA SET WSKAZNIK = {round(sums[k], 3)} WHERE NR_OFERTY = {indexes[k]}")


def home(request):
    numerl = []
    streetl = []
    costl = []
    metersl = []
    telephonel = []
    indil = []
    if request.method == 'POST':
        meters = int(request.POST.get('metry'))
        cost = int(request.POST.get('cena'))
        traffic = int(request.POST.get('ruch'))
        safety = int(request.POST.get('bezp'))
        busy = int(request.POST.get('zalud'))
        transport = int(request.POST.get('kom'))
        age = int(request.POST.get('wiek'))

        db = mysql.connector.connect(
            host="mysql.agh.edu.pl",
            port="3306",
            user="pdul1",
            passwd="5qLuH4Uf5c5cB0nT",
            database="pdul1"
        )

        mycursor = db.cursor(buffered=True)
        mycursor1 = db.cursor(buffered=True)

        indicator(mycursor, mycursor1, meters, cost, traffic, safety, busy, transport, age)
        mycursor.execute(
            "SELECT P.NR_OFERTY, P.METRY, P.CENA, P.WSKAZNIK, P.TELEFON, Z.NAZWA FROM MIESZKANIA P"
            "  JOIN ULICE Z  ON  P.ID_ULICA = Z.ID ORDER BY P.WSKAZNIK DESC LIMIT 10")
        for x in mycursor:
            numerl.append(x[0])
            streetl.append(x[5])
            costl.append(x[2])
            metersl.append(x[1])
            telephonel.append(x[4])
            indil.append(x[3])

    ofers = zip(numerl, streetl, costl, metersl, telephonel, indil)
    return render(request, 'homePage.html', {"ofers": ofers})

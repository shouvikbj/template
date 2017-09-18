from flask import Flask, flash, redirect, render_template, request, session, url_for, Response, make_response
from flask_session import Session
from tempfile import gettempdir
import json
from sql import *
from helpers import *

db = SQL("sqlite:///arthasastra.db")
hsn = SQL("sqlite:///hsn.db")

app = Flask(__name__)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
@login_required
def index():
    """
    Our index method
    displays relevant information of company
    """
    company = db.execute("""SELECT * FROM master WHERE company_id=:id""",
                        id=session["company_id"])
    return render_template('dash.html',company=company[0])

@app.route('/master/ledger/add/<group>',methods=["GET","POST"])
@login_required
def add_ledger_master(group):
    """
    Adds a new ledger group
    returns form if the request type is get
    """
    if request.method == "GET":
        # Just render the form
        return render_template("add_ledger.html",under_group=group)
    else:
        #return str(request.form)
        # Lets define our table & fetch info
        table_name =  str(session["company_id"])+"_ledgers"
        rows = db.execute("""SELECT * FROM :tbl
            WHERE ledger_name = :ldgr_name
            AND ledger_group = :ldgr_grp""",
            tbl=table_name,ldgr_name=request.form.get("name"),
            ldgr_grp=request.form.get("group"))
        if len(rows) > 0:
            flash("Duplicate Entry","error")
            return render_template("add_ledger.html",under_group=request.form.get("group"))
        else:
            # checks for group name in a malformed request
            rows = db.execute("""SELECT * FROM ledger_groups
                WHERE group_name=:group""",group=request.form.get("group"))
            if len(rows) == 0:
                flash("Invalid Group Name","warning")
                return render_template("add_ledger.html",under_group=request.form.get("group"))
            else:
                # insert it
                db.execute("""INSERT INTO :tbl
                    (ledger_name,ledger_group,opening_balance,address,gstin)
                    VALUES (:lname,:lg,:ob,:add,:gstin)""",
                    tbl=table_name,lname=request.form.get("name"),
                    lg=request.form.get("group"),ob=request.form.get("balance"),
                    add=request.form.get("address"),
                    gstin=request.form.get("gstin"))
                flash("Ledger Created: "+request.form.get("name"),"success")
                return render_template("add_ledger.html",under_group=request.form.get("group"))
        # Debug purposes
        return str(rows)
@app.route("/master/ledger/display")
@login_required
def display_ledger_master():
    """
    The search for ledger"""
    return render_template("display_ledger.html")

@app.route('/master/ledger/getgroups/<grp>')
@login_required
def getgroups_ledger_master(grp):
    # Returns jsonified data about a group
    grp = "%"+grp+"%"
    rows = db.execute("SELECT * FROM ledger_groups WHERE group_name LIKE :group",group=grp)
    return json.dumps(rows)

@app.route("/master/ledger/getledgers/byname/<ledger_name>")
@login_required
def getledgers_ledger_master(ledger_name):
    # returns jsonified ledger
    ledger_name = "%"+ledger_name+"%"
    table_name =  str(session["company_id"])+"_ledgers"
    rows = db.execute("SELECT * FROM :tbl WHERE ledger_name LIKE :lname",tbl=table_name,lname=ledger_name)
    return json.dumps(rows)

@app.route('/master/ledger/edit/<id>',methods=["GET","POST"])
@login_required
def edit_ledger_master(id):
    # Edit method for ledger
    table_name =  str(session["company_id"])+"_ledgers"
    if request.method == "GET":
        rows = db.execute("SELECT * FROM :tbl WHERE id = :id",tbl=table_name,id=id)
        # fetch data & return form
        if len(rows) == 1:
            return render_template("edit_ledger.html",row=rows[0])
        else:
            return "Server Fault"
    else:
        # update
        db.execute("""UPDATE :tbl
            SET ledger_name=:lname,ledger_group=:lg,
            opening_balance=:ob,address=:add,gstin=:gstin
            WHERE id=:id""",
            tbl=table_name,lname=request.form.get("name"),
            lg=request.form.get("group"),ob=request.form.get("balance"),
            add=request.form.get("address"),gstin=request.form.get("gstin"),
            id=id)
        flash("Ledger updated: "+request.form.get("name"),"success")
        return redirect(url_for('display_ledger_master'))

@app.route('/master/inventory/add/stock/group',methods=["GET","POST"])
@login_required
def add_stock_group_inventory_master():

    table_name =  str(session["company_id"])+"_stockgroup"
    if request.method == "GET":
        return render_template("add_stock_group.html")
    else:
        rows = db.execute("""SELECT * FROM :tbl WHERE group_name=:group_name""",
            tbl=table_name,group_name=request.form.get("group_name"))
        if len(rows) > 0:
            flash("Duplicate Entry","error")
        else:
            db.execute("""INSERT INTO :tbl
            (group_name,hsn,taxrate,uom)
            VALUES (:group_name,:hsn,:taxrate,:uom)""",
            tbl=table_name,group_name=request.form.get("group_name"),
            hsn=request.form.get("hsn"),taxrate=request.form.get("taxrate"),
            uom=request.form.get("uom"))
            flash("Stock Created: "+request.form.get("group_name"),"success")
        return render_template("add_stock_group.html")

@app.route("/master/inventory/display/stock/group")
@login_required
def display_stockgroup_inventory_master():
    return render_template("display_stock_group.html")

@app.route("/master/inventory/stock/getgroups/<grp>")
@login_required
def getstock_groups_inventory_master(grp):
    grp = "%"+grp+"%"
    table_name =  str(session["company_id"])+"_stockgroup"
    rows = db.execute("SELECT * FROM :tbl WHERE group_name LIKE :group",tbl=table_name,group=grp)
    return json.dumps(rows)

@app.route('/master/inventory/add/stock/item',methods=["GET","POST"])
@login_required
def add_stock_item_inventory_master():
    if request.method == "GET":
        return render_template("add_stock_item.html")
    else:
        #return str(request.form)
        table_name =  str(session["company_id"])+"_stockitems"
        rows = db.execute("""SELECT * FROM :table
            WHERE stock_item_name=:itm_name""",
            table=table_name,itm_name=request.form.get("stock_name"))
        if len(rows) > 0:
            flash("Duplicate Entry","error")
            return render_template("add_stock_item.html")
        else:
            table_name =  str(session["company_id"])+"_stockgroup"
            rows = db.execute("""SELECT * FROM :tbl WHERE group_name=:id""",
                tbl=table_name,id=request.form.get("under_group"))
            if len(rows) < 1:
                flash("Given Stock Group Not Found","warning")
                return render_template("add_stock_item.html")
            else:
                hsns = hsn.execute("SELECT * FROM hsn_codes WHERE HSN=:hsn",hsn=str(request.form.get('hsn')))
                if len(hsns) == 0:
                    flash("Invalid HSN code","warning")
                    #return render_template("add_stock_item.html")
                table_name =  str(session["company_id"])+"_stockitems"
                db.execute("""INSERT INTO :table_name (stock_item_name,stock_item_group,
                stock_item_hsn,stock_item_taxrate,stock_item_uom,rate)
                VALUES (:name,:group,:hsn,:taxrate,:uom,:rate)"""
                ,table_name=table_name,name=request.form.get('stock_name'),
                group=request.form.get('under_group'),hsn=request.form.get('hsn'),
                taxrate=request.form.get('taxrate'),uom=request.form.get('units_om'),
                rate=request.form.get('rate'))
                flash("Stock Item Added","success")
                return render_template("add_stock_item.html")

@app.route("/master/inventory/display/stock/item")
@login_required
def display_stock_item_iventory_master():
    return render_template("display_stock_items.html")

@app.route("/master/inventory/stock/getitems/<s>")
@login_required
def search_stock_items_inventory_master(s):
    table_name =  str(session["company_id"])+"_stockitems"
    s = "%"+s+"%"
    rows = db.execute("SELECT * FROM :table_name WHERE stock_item_name LIKE :s",table_name=table_name,s=s)
    return json.dumps(rows)

@app.route('/voucher/sale/add',methods=["GET","POST"])
@login_required
def add_sale_voucher():
    if request.method == "GET":
        return render_template('add_sale_voucher.html')
    else:
        s = dict(request.form)
        #return str(request.form)
        if s['date'][0] == '':
            flash("No Date Selected","error")
            return render_template('add_sale_voucher.html')
        date = s['date'][0].split("-")[0]
        month = s['date'][0].split("-")[1]
        year = s['date'][0].split("-")[2]
        inv_no = s['sino'][0]

        debtor_id = get_ledger_id(s['partyacname'][0])
        if debtor_id == 0:
            flash("Invalid  Reciever A/C Name","error")
            return render_template("add_sale_voucher.html",date=s['date'][0])

        creditor_id = get_ledger_id(s['saleacname'][0])
        if debtor_id == 0:
            flash("Invalid Sales A/C Name","error")
            return render_template("add_sale_voucher.html",date=s['date'][0])
        if s["itm_id"] == ['']:
            flash("Empty Voucher","error")
            return render_template("add_sale_voucher.html",date=s['date'][0])
        for name,id in zip(s['itm_name'],s['itm_id']):
            if int(id) != int(get_stock_item_id(name)):
                flash("Voucher name NOT given","error")
                return render_template("add_sale_voucher.html",date=s['date'][0])

        table_name =  str(session["company_id"])+"_master_sales"
        voucher_rows = db.execute("""SELECT id FROM :table_name
        WHERE date=:voucher_date AND month=:voucher_month
        AND inv_no=:inv AND debtor_id=:did""",
        table_name=table_name,
        voucher_date=date,voucher_month=month,inv=inv_no,did=debtor_id)
        if len(voucher_rows) > 0:
            flash("Duplicate Entry","error")
            return render_template("add_sale_voucher.html",date=s['date'][0])
        db.execute("""
            INSERT INTO :table_name (debtor_id,creditor_id,inv_no,date,
            month,year,place_of_supply,roundoff)
            VALUES (:did,:cid,:invc_n,:date,:month,:year,:place_of_supply,:roundoff)""",
            table_name=table_name,invc_n=inv_no,
            did=debtor_id,cid=creditor_id,place_of_supply=request.form.get("pos"),
            date=date,month=month,year=year,roundoff=request.form.get("roundoff"))
        voucher_rows = db.execute("""SELECT id FROM :table_name
            WHERE date=:voucher_date AND month=:voucher_month
            AND inv_no=:inv AND debtor_id=:did""",
            table_name=table_name,
            voucher_date=date,voucher_month=month,inv=inv_no,did=debtor_id)
        master_id=voucher_rows[0]['id']
        table_name =  str(session["company_id"])+"_sales"
        for id,qty,rate,disc,am in zip(s['itm_id'],s['qty'],s['rate'],s['discount'],s['amount']):
            db.execute("""
                INSERT INTO :table_name (bill_id,item_id,qty,rate,amount,disc)
                VALUES (:mid,:iid,:qty,:rate,:amount,:disc)""",
                table_name=table_name,mid=master_id,iid=id,qty=qty,rate=rate,amount=am,disc=disc)
        flash("Voucher Added Successfully","success")
        return render_template("add_sale_voucher.html",date=s['date'][0])
        return str(s)

@app.route('/gstr1',methods=["GET","POST"])
@login_required
def gstr1_main():
    if request.method == "POST":
        if request.form.get("category") == "b2b":
            return redirect(url_for('gstr1_b2b',m=request.form.get('month')))
        if request.form.get("category") == "b2cl":
            return redirect(url_for('gstr1_b2cl',m=request.form.get('month')))
        if request.form.get("category") == "b2cs":
            return redirect(url_for('gstr1_b2cs',m=request.form.get('month')))
        if request.form.get("category") == "r3":
            return redirect(url_for('gstr3',m=request.form.get('month')))
    return render_template('gstr1.html')
@app.route('/gstr1/b2b/<m>',methods=["GET","POST"])
@login_required
def gstr1_b2b(m):
    rows = get_gstr1_vouchers("b2b",m)
    return render_template("gstr1_b2b.html",data=rows,month=m,state_codes=state_codes)
@app.route('/gstr1/b2b/<m>/print')
@login_required
def print_gstr1_b2b(m):
    rows = get_gstr1_vouchers("b2b",m)
    return render_template("gstr1_b2b_print.html",data=rows,month=m,state_codes=state_codes)
@app.route('/gstr1/b2cl/<m>')
@login_required
def gstr1_b2cl(m):
    rows = get_gstr1_vouchers("b2cl",m)
    return render_template("gstr1_b2cl.html",data=rows,month=m,state_codes=state_codes)
@app.route('/gstr1/b2cl/<m>/print')
@login_required
def print_gstr1_b2cl(m):
    rows = get_gstr1_vouchers("b2cl",m)
    return render_template("gstr1_b2cl_print.html",data=rows,month=m,state_codes=state_codes)
@app.route('/gstr1/b2cs/<m>')
@login_required
def gstr1_b2cs(m):
    rows = get_gstr1_vouchers("b2cs",m)
    return render_template("gstr1_b2cs.html",data=rows,month=m,state_codes=state_codes)
@app.route('/gstr1/b2cs/<m>/print')
@login_required
def print_gstr1_b2cs(m):
    rows = get_gstr1_vouchers("b2cs",m)
    return render_template("gstr1_b2cs_print.html",data=rows,month=m,state_codes=state_codes)
@app.route('/gstr1/download/<t>/<m>')
@login_required
def gstr1_download(t,m):
    company = db.execute("SELECT * FROM master WHERE company_id=:id",id=session["company_id"])
    filename = company[0]["company_name"].strip()

    if t == "b2b":
        csv = "GSTIN/UIN of Recipient,Invoice Number,Invoice date,Invoice Value,Place Of Supply,Reverse Charge,Invoice Type,E-Commerce GSTIN,Rate,Taxable Value,Cess Amount"
        rows = get_gstr1_vouchers("b2b",m)
        for row in rows:
            csv += "\n"
            if len(str(row["date"])) == 1:
                row["date"] = "0"+str(row["date"])
            csv += row["gstin"]+","
            csv += row["inv_no"]+","
            csv += str(row["date"]) + "-" + row["month"] + "-20" + str(row["year"])+","
            csv += str("%0.2f"%round(row["invoice_value"]+row["roundoff"]))+","
            csv += state_codes[row["place_of_supply"]]+","
            csv += "N," #Reverse Charge
            csv += "Regular,," #Invoice Type,E-Commerce
            csv += str(row["stock_item_taxrate"])+","
            csv += str("%0.2f"%row["amount"])+","
    if t == "b2cs":
        csv = "Type,Place Of Supply,Rate,Taxable Value,Cess Amount,E-Commerce GSTIN"
        rows = get_gstr1_vouchers("b2cs",m)
        for row in rows:
            csv += "\nOE,"
            csv += state_codes[row["place_of_supply"]]+","
            csv += str(row["stock_item_taxrate"])+","
            csv += str("%0.2f"%round(row["invoice_value"]+row["roundoff"]))+","
            csv += ","
    if t == "b2cl":
        csv = "Invoice Number,Invoice date,Invoice Value,Place Of Supply,Rate,Taxable Value,Cess Amount,E-Commerce GSTIN"
        rows = get_gstr1_vouchers("b2cs",m)
        for row in rows:
            csv += "\n"
            if len(str(row["date"])) == 1:
                row["date"] = "0"+str(row["date"])
            csv += row["inv_no"]+","
            csv += str(row["date"]) + "-" + row["month"] + "-20" + str(row["year"])+","
            csv += str("%0.2f"%round(row["invoice_value"]+row["roundoff"]))+","
            csv += state_codes[row["place_of_supply"]]+","
            csv += str(row["stock_item_taxrate"])+","
            csv += str("%0.2f"%row["amount"])+","
            csv += ""
    # We need to modify the response, so the first thing we
    # need to do is create a response out of the CSV string
    response = make_response(csv)
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers["Content-Disposition"] = "attachment;filename="+filename+" "+m+"_"+t+".csv"
    return response
@app.route("/gstr3/<m>")
@login_required
def gstr3(m):
    data = get_gstr3_data(m)
    return render_template("gstr3.html",data=data)
# The Login route
@app.route('/login',methods=["GET","POST"])

def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        s = dict(request.form)
        #return str(s)
        rows = db.execute("""SELECT * FROM login
            WHERE userid=:userid AND password=:password""",
            userid=s['userid'][0],password=s['password'][0])
        if len(rows) == 0:
            # Nothing there
            flash("Invalid ID/Password","error")
            return render_template('login.html')
        else:
            # Grant access
            flash("Welcome to Chanakya","primary")
            company = db.execute("""SELECT * FROM master WHERE company_id=:id""",
            id=rows[0]["company_id"])
            session["company_name"] = company[0]["company_name"]
            session["company_id"] = company[0]["company_id"]
            return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("Successfully Logged out","info")
    return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])

def register():
    #return str(Session)
    if request.method == "GET":
        return render_template("register.html")
    else:
        s = dict(request.form)
        rows = db.execute("""SELECT * FROM master
            WHERE company_name=:name OR company_gstin=:gstin""",
            name=s["company_name"][0],gstin=s["gstin"][0])
        if len(rows) > 0:
            flash("Duplicate Entry","error")
            return render_template("register.html")
        if s["password"][0] != s["repassword"][0]:
            flash("Passwords Don't Match","error")
            return render_template("register.html")
        rows = db.execute("SELECT * FROM login WHERE userid=:uid",uid=s["userid"][0])
        if len(rows) > 0:
            flash("User-ID already taken","error")
            return render_template("register.html")
        row = db.execute("""
        INSERT INTO master (company_name,company_gstin,company_address)
        VALUES (:cname,:cgstin,:cadd)
        """,cname=s["company_name"][0],cgstin=s["gstin"][0],cadd=s["address"][0])
        company_id = row
        #return str(row)
        db.execute("""INSERT INTO login
            (userid,password,company_name,company_id)
            VALUES (:uid,:passw,:cname,:cid)""",uid=s["userid"][0],
            passw=s["password"][0],cname=s["company_name"][0],cid=company_id)

        #Ledgers table
        table = str(company_id)+"_ledgers"
        db.execute("""
        CREATE TABLE :table
        ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'ledger_name' TEXT,
        'ledger_group' TEXT, 'opening_balance' REAL, 'address' TEXT, 'gstin' TEXT)
        """,table=table)

        #Master Sales table
        table = str(company_id)+"_master_sales"
        db.execute("""
        CREATE TABLE :table ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
         'debtor_id' INTEGER, 'creditor_id' INTEGER, 'inv_no' TEXT, 'date' INTEGER,
         'month' INTEGER, 'year' INTEGER, 'place_of_supply' TEXT DEFAULT '19',
         'roundoff' REAL DEFAULT 0.00)
        """,table=table)
        #Sales table
        table = str(company_id)+"_sales"
        db.execute("""
        CREATE TABLE :table ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        'bill_id' INTEGER, 'item_id' INTEGER, 'qty' REAL, 'rate' REAL,
        'amount' REAL, 'disc' REAL)
        """,table=table)
        #Stock Group table
        table = str(company_id)+"_stockgroup"
        db.execute("""
        CREATE TABLE :table ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        'group_name' TEXT, 'hsn' TEXT, 'taxrate' TEXT, 'uom' TEXT)
        """,table=table)
        #Stock Items table
        table = str(company_id)+"_stockitems"
        db.execute("""
        CREATE TABLE :table ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        'stock_item_name' TEXT, 'stock_item_group' TEXT, 'stock_item_hsn' TEXT,
        'stock_item_taxrate' REAL, 'stock_item_uom' TEXT, 'rate' REAL DEFAULT 0.00)
        """,table=table)
        #Sales View table
        table = str(company_id)+"_gstr1_sales"
        master_sales = str(company_id)+"_master_sales"
        sales = str(company_id)+"_sales"
        stock_items = str(company_id)+"_stockitems"
        ledgers = str(company_id)+"_ledgers"
        db.execute("""
        CREATE VIEW :table AS SELECT * FROM :sales
        INNER JOIN :master_sales ON :master_sales.id = bill_id
        INNER JOIN :stock_items ON :stock_items.id = item_id
        INNER JOIN :ledgers ON :ledgers.id = debtor_id
        INNER JOIN (
                    SELECT bill_id AS invoice_number,
                    SUM(amount + (amount*:stock_items.stock_item_taxrate)/100)
                    AS invoice_value
                    FROM :sales
                    INNER JOIN :stock_items ON :stock_items.id = item_id
                    GROUP BY bill_id
                    ) ON invoice_number = bill_id
        """,table=table,master_sales=master_sales,sales=sales,stock_items=stock_items,
        ledgers=ledgers)
        # INSERT Purchase,Sales,Unregistered
        table = str(company_id)+"_ledgers"
        db.execute("INSERT INTO :table (ledger_name,ledger_group) VALUES ('Purchase','Purchase')",table=table)
        db.execute("INSERT INTO :table (ledger_name,ledger_group) VALUES ('Sales Acc','Sales')",table=table)
        db.execute("""INSERT INTO :table
            (ledger_name,ledger_group)
            VALUES ('Unregistered Sale','Sundry Debtors')""",table=table)
        return redirect(url_for('logout'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

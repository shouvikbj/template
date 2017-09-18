from flask import redirect, render_template, request, session, url_for
from functools import wraps
from sql import *
db = SQL("sqlite:///arthasastra.db")
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("company_name") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
def get_ledger_id(ledger_name):
    table_name =  str(session["company_id"])+"_ledgers"
    rows = db.execute("SELECT * FROM :tbl WHERE ledger_name LIKE :lname",tbl=table_name,lname=ledger_name)
    if len(rows) == 1:
        return rows[0]["id"]
    else:
        return 0
def get_stock_item_id(stock_name):
    table_name =  str(session["company_id"])+"_stockitems"
    rows = db.execute("SELECT * FROM :table_name WHERE stock_item_name LIKE :s",table_name=table_name,s=stock_name)
    if len(rows) == 1:
        return rows[0]["id"]
    else:
        return 0

def get_gstr1_vouchers(type,m):
    ur_id = get_ledger_id("Unregistered Sale")
    if type == "b2b":
        b2b = str(session["company_id"])+"_gstr1_sales"
        rows = db.execute("""
            SELECT ledger_name,bill_id,
                date,month,year,gstin,
                inv_no,invoice_value,roundoff,
                place_of_supply,stock_item_taxrate,
                SUM(amount) as amount
            FROM :table
            WHERE month=:month AND debtor_id != :ur_id
            GROUP BY "bill_id","stock_item_taxrate"
            ORDER BY date ASC""",
            table=b2b,month=m,ur_id=ur_id)
        return rows
    if type == "b2cs":
        b2cs = str(session["company_id"])+"_gstr1_sales"
        home_state = '19'
        ur_id = get_ledger_id("Unregistered Sale")
        rows = db.execute("""
            SELECT ledger_name,bill_id,
                date,month,year,gstin,
                inv_no,invoice_value,roundoff,
                place_of_supply,stock_item_taxrate,
                SUM(amount) as amount
            FROM :table
            WHERE month=:month
                AND debtor_id = :ur_id
                AND ((place_of_supply = :hs)
                OR (place_of_supply != :hs AND invoice_value < 250001))
            GROUP BY "bill_id","stock_item_taxrate"
            ORDER BY date ASC""",
            table=b2cs,month=m,ur_id=ur_id,hs=home_state)
        return rows
    if type == "b2cl":
        b2cl = str(session["company_id"])+"_gstr1_sales"
        ur_id = get_ledger_id("Unregistered Sale")
        home_state = '19'
        rows = db.execute("""
            SELECT ledger_name,bill_id,
                date,month,year,gstin,
                inv_no,invoice_value,roundoff,
                place_of_supply,stock_item_taxrate,
                SUM(amount) as amount
            FROM :table
            WHERE month=:month
                AND debtor_id = :ur_id AND invoice_value > 250000
                AND place_of_supply!=:hs
            GROUP BY "bill_id","stock_item_taxrate"
            ORDER BY date ASC""",
            table=b2cl,month=m,ur_id=ur_id,hs=home_state)
        return rows
def get_gstr3_data(m):
    tbl = str(session["company_id"])+"_gstr1_sales"
    home_state = 19
    total_taxable_value = db.execute("""
        SELECT sum(amount) as total_taxable
        FROM :table
        WHERE month=:month
        """,table=tbl,month=m)[0]["total_taxable"]
    total_tax_value = db.execute("""
        SELECT sum(amount*stock_item_taxrate/100) as total_tax
        FROM :table
        WHERE month=:month
        """,table=tbl,month=m)[0]["total_tax"]
    total_igst = db.execute("""
        SELECT sum(amount*stock_item_taxrate/100) as total_tax
        FROM :table
        WHERE month=:month
        AND place_of_supply != :hs
        """,table=tbl,hs=home_state,month=m)[0]["total_tax"]
    data = {}
    data["total_taxable_value"] = total_taxable_value
    data["total_tax_value"] = total_tax_value
    if total_igst is None:
        total_igst = 0
    data["total_igst"] = total_igst
    data["total_cgst"] = (total_tax_value - total_igst)/2
    return data
state_codes = {"35":"35-Andaman and Nicobar Islands","37":"37-Andhra Pradesh","12":"12-Arunachal Pradesh","18":"18-Assam","10":"10-Bihar","04":"04-Chandigarh","22":"22-Chhattisgarh","26":"26-Dadra and Nagar Haveli","25":"25-Daman and Diu","07":"07-Delhi","30":"30-Goa","24":"24-Gujarat","06":"06-Haryana","02":"02-Himachal Pradesh","01":"01-Jammu and Kashmir","20":"20-Jharkhand","29":"29-Karnataka","32":"32-Kerala","31":"31-Lakshadweep","23":"23-Madhya Pradesh","27":"27-Maharashtra","14":"14-Manipur","17":"17-Meghalaya","15":"15-Mizoram","13":"13-Nagaland","21":"21-Odisha","34":"34-Puducherry","03":"03-Punjab","08":"08-Rajasthan","11":"11-Sikkim","33":"33-Tamil Nadu","36":"36-Telangana","16":"16-Tripura","09":"09-Uttar Pradesh","05":"05-Uttarakhand","97":"97-Other Territory","19":"19-West Bengal"}

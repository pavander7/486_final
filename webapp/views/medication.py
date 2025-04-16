from os import abort
import re

from flask import render_template
from psycopg2.extras import RealDictCursor

from . import views_bp
from postgres.helpers import get_db_conn

openfda_cols = ["set_id", "effective_time", "application_number", "manufacturer_name", "product_ndc", "product_type", "administration_route", "rxcui", "spl_id", "spl_id_primary", "spl_set_id", "package_ndc", "nui", "pharm_class_epc", "pharm_class_moa", "unii"]

@views_bp.route("/medication/<drugid>", methods=["GET"])
def med_info(drugid):
    conn = get_db_conn()
    curr = conn.cursor(cursor_factory=RealDictCursor)

    curr.execute("""
        SELECT * 
        FROM openfda.drugs
        WHERE drugid = %s;
    """, (drugid,))

    info_raw = curr.fetchone()
    if info_raw is None:
        abort(404)  # or show a nice error template

    drugname = None
    generic_name = []
    brand_name = []
    substance_name = []
    openfda_fields = {}
    other_fields = {}

    for colname, content in info_raw.items():
        match colname:
            case "generic_name":
                if content and isinstance(content, list) and len(content) > 0:
                    drugname = content[0]
                    generic_name = content
                else:
                    abort(500)
            case "brand_name":
                if content and isinstance(content, list) and len(content) > 0:
                    brand_name = content
            case "substance_name":
                if content and isinstance(content, list) and len(content) > 0:
                    substance_name = content
            case "spl_id_primary":
                pass  # should never be included
            case col if col in openfda_cols:
                pretty_title = re.sub(r'_', ' ', col).title()
                openfda_fields[pretty_title] = content
            case _:
                if content is not None:
                    pretty_title = re.sub(r'_', ' ', colname).title()
                    other_fields[pretty_title] = content

    curr.close()
    conn.close()

    if len(brand_name) == 0:
        brand_name = None
    if len(substance_name) == 0:
        substance_name = None
    if openfda_fields.empty():
        openfda_fields = None
    if other_fields.empty():
        other_fields = None

    context = {"drug_name": drugname, "generic_name": generic_name, "brand_name": brand_name, "substance_name": substance_name, "openfda": openfda_fields, "fields": other_fields}
    return render_template('medication.html', **context)
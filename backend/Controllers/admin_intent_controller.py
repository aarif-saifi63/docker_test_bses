import csv
import io
from flask import Response, request, jsonify, send_file
import pandas as pd
from Models.intent_model import IntentV
from Models.intent_example_model import IntentExampleV
from Models.sub_menu_option_model import SubMenuOptionV
from utils.input_validator import InputValidator

def sanitize_for_csv(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value

def create_intent():
    try:
        data = request.json
        intent_name = data.get("intent_name")
        examples = data.get("examples", [])
        sub_menu_id = data.get("sub_menu_id", None)

        if not intent_name:
            return jsonify(status=False, message="intent_name is required"), 400

        # Create new intent
        new_intent = IntentV(intent_name=intent_name, sub_menu_id=sub_menu_id)
        intent_id = new_intent.save()

        # Save each example separately
        for example in examples:
            example_obj = IntentExampleV(intent_id=intent_id, example=example)
            example_obj.save()

        return jsonify(status=True, message="Intent created successfully", intent_id=intent_id), 201

    except Exception as e:
        return jsonify(status=False, message=str(e)), 500

def get_intents():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        search = request.args.get("intent_name", "").strip()

        # Base fetch from your repository
        intents, total = IntentV.find(search="", page=1, limit=5000)  # fetch full for search ranking

        search_upper = search.upper()
        has_search = bool(search)

        filtered = []

        for intent in intents:
            examples = IntentExampleV.find_by_intent(intent.id)
            example_texts = [ex.example for ex in examples]

            # Skip intents with examples ending in BYPL
            if any(ex.strip().upper().endswith("BYPL") for ex in example_texts):
                continue

            # ---- Fuzzy Search Logic ----
            score = 0
            name_up = intent.name.upper()

            if has_search:
                # EXAMPLE MATCH
                example_up_list = [e.upper() for e in example_texts]

                # Exact match
                if name_up == search_upper:
                    score = 100
                elif any(ex == search_upper for ex in example_up_list):
                    score = 100

                # Starts-with
                elif name_up.startswith(search_upper):
                    score = 80
                elif any(ex.startswith(search_upper) for ex in example_up_list):
                    score = 80

                # Contains
                elif search_upper in name_up:
                    score = 60
                elif any(search_upper in ex for ex in example_up_list):
                    score = 60

                if score == 0:
                    continue  # skip unmatched items

            # ----- Submenu details -----
            submenu_details = []
            submenu_ids = []

            if getattr(intent, "submenu_id", None):
                if isinstance(intent.submenu_id, (list, tuple)):
                    submenu_ids = intent.submenu_id
                elif isinstance(intent.submenu_id, str):
                    submenu_ids = [int(x) for x in intent.submenu_id.split(",") if x.strip().isdigit()]
                elif isinstance(intent.submenu_id, int):
                    submenu_ids = [intent.submenu_id]

            if submenu_ids:
                submenus = SubMenuOptionV.find_by_ids(submenu_ids)
                submenu_details = [
                    {"submenu_name": sm.name, "lang": sm.lang}
                    for sm in submenus
                ]

            filtered.append({
                "id": intent.id,
                "intent_name": intent.name,
                "examples": example_texts,
                "submenus": submenu_details,
                "score": score
            })

        # Sort only when searching
        if has_search:
            filtered.sort(key=lambda i: i["score"], reverse=True)

        # Pagination on final results
        total = len(filtered)
        total_pages = (total + limit - 1) // limit

        start = (page - 1) * limit
        end = start + limit

        paginated = filtered[start:end]

        return jsonify(
            status=True,
            message="Intents fetched successfully",
            data=paginated,
            total=total,
            total_pages=total_pages,
            page=page,
            limit=limit
        ), 200

    except Exception as e:
        print(e)
        return jsonify(status=False, message=str(e)), 500


def get_intent_by_id(intent_id):
    try:
        intent = IntentV.find_by_id(intent_id)
        if not intent:
            return jsonify(status=False, message="Intent not found"), 404

        examples = IntentExampleV.find_by_intent(intent.id)
        data = {
            "id": intent.id,
            "intent_name": intent.intent_name,
            "examples": [ex.example for ex in examples],
            "created_at": intent.created_at,
            "updated_at": intent.updated_at
        }

        return jsonify(status=True, data=data), 200
    except Exception as e:
        return jsonify(status=False, message=str(e)), 500


def update_intent(intent_id):
    try:
        data = request.json
        intent_name = data.get("intent_name")
        examples = data.get("examples", [])

        intent_name = sanitize_for_csv(intent_name)

        is_valid, msg = InputValidator.validate_name(intent_name, "intent_name")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        intent = IntentV.find_by_id(intent_id)
        if not intent:
            return jsonify(status=False, message="Intent not found"), 404

        # Update the intent name
        IntentV.update(intent_id, {"intent_name": intent_name})

        # Delete old examples
        IntentExampleV.delete_by_intent(intent_id)

        # Add new examples
        for example in examples:

            example = sanitize_for_csv(example)

            is_valid, msg = InputValidator.validate_name(example, "example")
            if not is_valid:
                return jsonify({"status": False, "message": msg}), 400
            
            ex = IntentExampleV(intent_id=intent_id, example=example)
            ex.save()

        return jsonify(status=True, message="Intent updated successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=str(e)), 500


def delete_intent(intent_id):
    try:
        deleted = IntentV.delete(intent_id)
        if not deleted:
            return jsonify(status=False, message="Intent not found"), 404

        IntentExampleV.delete_by_intent(intent_id)
        return jsonify(status=True, message="Intent deleted successfully"), 200
    except Exception as e:
        return jsonify(status=False, message=str(e)), 500


## Export Intents


def export_intents():
    """
    Export intents in JSON, CSV, or XLSX format with improved structure:
    - S.No instead of ID
    - Intent Language instead of Chatmenu
    - Count of Examples
    - Alphabetically sorted by Intent Name
    """
    try:
        export_format = request.args.get("format", "json").lower()

        # Fetch all intents fully
        intents, _ = IntentV.find(search="", page=1, limit=5000)

        export_data = []

        for intent in intents:
            examples = IntentExampleV.find_by_intent(intent.id)
            example_texts = [ex.example for ex in examples]

            # Skip BYPL examples (same logic as original)
            if any(ex.strip().upper().endswith("BYPL") for ex in example_texts):
                continue

            # Collect submenu details
            submenu_ids = []
            submenu_details = []

            if getattr(intent, "submenu_id", None):
                if isinstance(intent.submenu_id, (list, tuple)):
                    submenu_ids = intent.submenu_id
                elif isinstance(intent.submenu_id, str):
                    submenu_ids = [int(x) for x in intent.submenu_id.split(",") if x.isdigit()]
                elif isinstance(intent.submenu_id, int):
                    submenu_ids = [intent.submenu_id]

            if submenu_ids:
                submenus = SubMenuOptionV.find_by_ids(submenu_ids)
                submenu_details = [{"submenu_name": sm.name, "lang": sm.lang} for sm in submenus]

            # Determine intent language from submenus or default to English
            intent_language = "English"
            if submenu_details:
                # Check if any submenu is Hindi
                if any(sm["lang"].lower() in ["hi", "hindi", "hin"] for sm in submenu_details):
                    intent_language = "Hindi"

            export_data.append({
                "id": intent.id,
                "intent_name": intent.name,
                "intent_language": intent_language,
                "submenus": submenu_details,
                "examples_count": len(example_texts),
                "examples": example_texts
            })

        # Sort alphabetically by intent_name
        export_data.sort(key=lambda x: x["intent_name"].lower())

        print(f"Prepared {len(export_data)} intents for export in {export_format} format.")
        print(f"Sample data: {export_data[:2]}")

        # Add sequential S.No
        for idx, item in enumerate(export_data, start=1):
            item["s_no"] = idx

        # Return based on format
        if export_format == "json":
            return jsonify(
                status=True,
                message="Export generated",
                data=export_data
            ), 200

        elif export_format == "csv":
            return generate_csv(export_data)

        elif export_format == "xlsx":
            return generate_excel(export_data)

        else:
            return jsonify(
                status=False, 
                message="Invalid format. Use json, csv, or xlsx"
            ), 400

    except Exception as e:
        print(f"Error in export_intents: {e}")
        return jsonify(status=False, message=str(e)), 500


def generate_excel(data):
    """
    Generate Excel file with improved formatting:
    - S.No (sequential)
    - Intent Language instead of Chatmenu
    - Count of Examples
    - Alphabetically sorted
    """
    # Prepare data for Excel
    df = pd.DataFrame([
        {
            "S.No": d["s_no"],
            "Intent Name": d["intent_name"],
            "Intent Language": d["intent_language"],
            # "Submenus": "\n".join([f'{s["submenu_name"]} ({s["lang"]})' for s in d["submenus"]]) if d["submenus"] else "",
            "Count of Examples / Training Phrases": d["examples_count"],
            "Examples / Training Phrases": "\n".join(d["examples"])
        }
        for d in data
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Intents")
        workbook = writer.book
        worksheet = writer.sheets["Intents"]

        # Define formats
        wrap_format = workbook.add_format({
            "text_wrap": True, 
            "valign": "top",
            "border": 1
        })
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": "#4472C4",
            "font_color": "white",
            "border": 1,
            "valign": "vcenter",
            "align": "center"
        })
        center_format = workbook.add_format({
            "align": "center",
            "valign": "top",
            "border": 1
        })

        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Set column widths and formats
        column_widths = {
            0: (8, center_format),   # S.No
            1: (30, wrap_format),     # Intent Name
            2: (15, center_format),   # Intent Language
            # 3: (30, wrap_format),     # Submenus
            4: (12, center_format),   # Count
            5: (50, wrap_format)      # Examples
        }

        for col_idx, (width, fmt) in column_widths.items():
            worksheet.set_column(col_idx, col_idx, width, fmt)

        # Adjust row heights dynamically based on content
        for row_idx in range(1, len(df) + 1):
            # Calculate row height based on examples count
            examples_count = df.iloc[row_idx - 1]["Count of Examples / Training Phrases"]
            row_height = max(30, min(examples_count * 15, 200))  # Min 30, max 200
            worksheet.set_row(row_idx, row_height)

        # Freeze the header row
        worksheet.freeze_panes(1, 0)

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="intents_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def generate_csv(data):
    """
    Generate CSV file with improved structure:
    - S.No (sequential)
    - Intent Language instead of Chatmenu
    - Count of Examples
    - Alphabetically sorted
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "S.No",
        "Intent Name",
        "Intent Language",
        # "Submenus",
        "Count of Examples / Training Phrases",
        "Examples / Training Phrases"
    ])

    for row in data:
        # submenu_text = "\n".join([
        #     f'{sm["submenu_name"]} ({sm["lang"]})' 
        #     for sm in row["submenus"]
        # ]) if row["submenus"] else ""
        
        examples_text = "\n".join(row["examples"])

        writer.writerow([
            row["s_no"],
            row["intent_name"],
            row["intent_language"],
            # submenu_text,
            row["examples_count"],
            examples_text
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=intents_export.csv"}
    )   
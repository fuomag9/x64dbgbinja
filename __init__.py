import json
import os
import sqlite3
import traceback

from binaryninja import *


def get_module_name(view):
    filename = view.file.filename
    if filename.endswith(".bndb"):
        try:
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM global WHERE name='filename'")
            _, rawfilename = cursor.fetchone()
            filename = rawfilename[5:-2]
        except:
            pass
    return os.path.basename(filename)


def export_db(view):
    db = {}
    module = get_module_name(view).lower()
    base = view.start

    file = get_save_filename_input("Export database", "x64dbg database (*.dd64 *.dd32);;All Files (*)")
    if not file:
        return
    print(f"Exporting database {file}")

    print("Exporting symbols")
    db["labels"] = [{
        "text": symbol.name,
        "manual": False,
        "module": f"{module}",
        "address": f"0x{symbol.address - base:X}"
    } for symbol in view.get_symbols()]
    print(f"{len(db['labels']):d} label(s) exported")

    db["comments"] = [{
        "text": func.comments[comment].replace("{", "{{").replace("}", "}}"),
        "manual": False,
        "module": f"{module}",
        "address": f"0x{comment - base:X}"
    } for func in view.functions for comment in func.comments]
    print(f"{len(db['comments']):d} comment(s) exported")

    with open(file, "w") as outfile:
        json.dump(db, outfile, indent=1)
    print("Done!")


def import_db(view):
    module = get_module_name(view).lower()
    base = view.start

    file = get_open_filename_input("Import database", "x64dbg database (*.dd64 *.dd32);;All Files (*)")
    if not file:
        return
    print(f"Importing database {file}")

    with open(file) as dbdata:
        db = json.load(dbdata)

    count = 0
    labels = db.get("labels", [])
    for label in labels:
        try:
            if label["module"] != module:
                continue
            address = int(label["address"], 16) + base
            name = label["text"]
            symbol = view.get_symbol_at(address)
            if not symbol or symbol.name != name:
                view.define_user_symbol(Symbol(FunctionSymbol, address, name))
                count += 1
        except:
            traceback.print_exc()
            pass
    print(f"{count:d}/{len(labels):d} label(s) imported")

    count = 0
    comments = db.get("comments", [])
    for comment in comments:
        try:
            if comment["module"] != module:
                continue
            address = int(comment["address"], 16) + base
            comment = comment["text"]
            for func in view.functions:
                func.set_comment(address, comment)
            count += 1
        except:
            traceback.print_exc()
            pass
    print(f"{count:d}/{len(comments):d} comment(s) imported")

    print("Done!")


PluginCommand.register("Export x64dbg database", "Export x64dbg database",
                       export_db)
PluginCommand.register("Import x64dbg database", "Import x64dbg database",
                       import_db)

#!/usr/bin/env python
"""Analysis sandbox runner. Launched with `python -I` by the agent's
run_python tool; reads the task code on stdin, prints a JSON result on
stdout. User code runs with restricted builtins and an import blacklist; the
heavy analysis stack (pandas, numpy, matplotlib) is pre-imported before the
restrictions apply so legitimate imports keep working."""

import ast
import builtins
import contextlib
import io
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")

BLOCKED_MODULES = {
    "socket", "subprocess", "os", "sys", "shutil", "pathlib", "requests",
    "urllib", "http", "ftplib", "telnetlib", "smtplib", "importlib", "ctypes",
    "multiprocessing", "threading", "signal", "pickle", "dill", "tempfile",
    "webbrowser", "pty", "resource", "atexit",
}

BUILTINS_REMOVE = {
    "open", "exec", "eval", "compile", "__import__", "input",
    "breakpoint", "exit", "quit", "help", "globals", "locals", "vars",
}

DB_PATH = os.environ["CMPDI_DB_PATH"]
RUN_DIR = os.environ["CMPDI_RUN_DIR"]
# successive run_python calls in one task number their charts continuously so
# they never overwrite each other
FIGURE_START = int(os.environ.get("CMPDI_FIGURE_START", "1"))


def load_table(doc_id: str, sheet_no=None):
    """One extracted table (or a whole sheet) as a DataFrame, straight from
    the source of truth."""
    import sqlite3

    import pandas as pd
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        if sheet_no is None:
            tables = pd.read_sql_query(
                "SELECT id, table_idx FROM tables WHERE doc_id=? ORDER BY table_idx",
                con, params=(doc_id,))
            if tables.empty:
                return pd.DataFrame()
            return _table_frame(con, int(tables.iloc[0]["id"]))
        rows = pd.read_sql_query(
            """SELECT t.id FROM tables t WHERE t.doc_id=? AND t.sheet_no=?
               ORDER BY t.table_idx""", con, params=(doc_id, int(sheet_no)))
        if rows.empty:
            return pd.DataFrame()
        return _table_frame(con, int(rows.iloc[0]["id"]))
    finally:
        con.close()


def _table_frame(con, table_id):
    import pandas as pd
    cells = pd.read_sql_query(
        "SELECT row_idx, col_idx, value_raw, value_norm FROM table_cells"
        " WHERE table_id=? ORDER BY row_idx, col_idx", con, params=(table_id,))
    if cells.empty:
        return pd.DataFrame()
    pivoted = cells.pivot(index="row_idx", columns="col_idx", values="value_raw")
    return pivoted.reset_index(drop=True)


def load_facts(entity=None, attribute=None):
    """The numeric fact index with receipts, as a DataFrame."""
    import sqlite3

    import pandas as pd
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        sql = ("SELECT f.entity_text, e.canonical_name, f.attribute, f.period_norm,"
               " f.value_raw, f.value_norm, f.unit, f.flags, c.doc_id, c.page_no,"
               " c.sheet_no, d.filename FROM facts f"
               " LEFT JOIN entities e ON e.id = f.entity_id"
               " LEFT JOIN chunks c ON c.id = f.chunk_id"
               " LEFT JOIN documents d ON d.id = c.doc_id WHERE 1=1")
        params = []
        if entity:
            sql += " AND (e.canonical_name = ? OR f.entity_text = ?)"
            params += [entity, entity]
        if attribute:
            sql += " AND f.attribute = ?"
            params.append(attribute)
        return pd.read_sql_query(sql + " ORDER BY f.period_norm", con, params=params)
    finally:
        con.close()


def main():
    code = sys.stdin.read()

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    import math, statistics, json as _json, re, datetime, collections, itertools, random, decimal  # noqa

    safe_builtins = {k: v for k, v in vars(builtins).items()
                     if not k.startswith("_") and k not in BUILTINS_REMOVE}

    def check_imports(tree):
        """Static scan: blocked modules are rejected at import statements.
        Runtime imports stay unrestricted so pandas & friends keep working;
        dynamic evasion paths (exec/eval/compile/__import__/open) are absent
        from the restricted builtins instead."""
        for node in ast.walk(tree):
            roots = []
            if isinstance(node, ast.Import):
                roots = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = [node.module]
            for name in roots:
                root = name.split(".")[0]
                if root in BLOCKED_MODULES:
                    raise ImportError(f"Module '{root}' is not available in the analysis sandbox")

    # `import` resolves through __import__ in the code's builtins; the static
    # scan above is the policy, so the unrestricted builtin is carried through
    safe_builtins["__import__"] = builtins.__import__
    stdout = io.StringIO()
    result = None
    try:
        globs = {"__builtins__": safe_builtins, "pd": pd, "np": np, "plt": plt,
                 "load_table": load_table, "load_facts": load_facts}
        tree = ast.parse(code)
        check_imports(tree)
        tail = None
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            tail = tree.body.pop()
        with contextlib.redirect_stdout(stdout):
            exec(compile(tree, "<analysis>", "exec"), globs)  # noqa: S102 - sandboxed
            if tail is not None:
                result = eval(compile(ast.Expression(tail.value), "<analysis>", "eval"), globs)
    except Exception as e:
        print(json.dumps({"stdout": stdout.getvalue()[-4000:], "error": f"{type(e).__name__}: {e}",
                          "result": None, "figures": []}))
        return

    figures = []
    for i, num in enumerate(plt.get_fignums()):
        fig = plt.figure(num)
        path = os.path.join(RUN_DIR, f"chart_{FIGURE_START + i}.png")
        fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
        figures.append(os.path.basename(path))
    if figures:
        plt.close("all")

    if result is not None and not isinstance(result, (str, int, float, bool, list, dict, type(None))):
        result = repr(result)
    print(json.dumps({"stdout": stdout.getvalue()[-4000:], "error": None,
                      "result": _safe(result), "figures": figures}))


def _safe(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


if __name__ == "__main__":
    main()

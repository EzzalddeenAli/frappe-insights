# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from sqlalchemy.sql import text

from insights.insights.doctype.insights_table_import.insights_table_import import (
    InsightsTableImport,
)
from insights.utils import ResultColumn

from .utils import (
    Timer,
    add_limit_to_sql,
    compile_query,
    create_execution_log,
    replace_query_tables_with_cte,
)


class BaseDatabase:
    def __init__(self):
        self.engine = None
        self.data_source = None
        self.connection = None
        self.query_builder = None
        self.table_factory = None

    def test_connection(self):
        return self.execute_query("SELECT 1")

    def connect(self):
        try:
            return self.engine.connect()
        except Exception as e:
            frappe.log_error(title="Error connecting to database", message=e)
            frappe.throw("Error connecting to database")

    def build_query(self, query, with_cte=False):
        """Build insights query and return the sql"""
        query_str = self.query_builder.build(query, dialect=self.engine.dialect)
        if with_cte and frappe.db.get_single_value(
            "Insights Settings", "allow_subquery"
        ):
            query_str = replace_query_tables_with_cte(query_str, self.data_source)
        return query_str if query_str else None

    def run_query(self, query):
        """Run insights query and return the result"""
        self.before_run_query(query)

        sql = self.build_query(query)
        if sql is None:
            return []
        if frappe.db.get_single_value("Insights Settings", "allow_subquery"):
            sql = replace_query_tables_with_cte(sql, self.data_source)
        # set a hard max limit to prevent long running queries
        max_rows = (
            frappe.db.get_single_value("Insights Settings", "query_result_limit")
            or 1000
        )
        sql = add_limit_to_sql(sql, max_rows)
        return self.execute_query(
            sql, return_columns=True, is_native_query=query.is_native_query
        )

    def before_run_query(self, query):
        pass

    def execute_query(
        self,
        sql,
        pluck=False,
        return_columns=False,
        replace_query_tables=False,
        is_native_query=False,
    ):
        if not isinstance(sql, str) and not is_native_query:
            # since db.execute() is also being used with Query objects i.e non-compiled queries
            compiled = compile_query(sql, self.engine.dialect)
            sql = str(compiled) if compiled else None

        if sql is None:
            return []

        allow_subquery = frappe.db.get_single_value(
            "Insights Settings", "allow_subquery"
        )
        if replace_query_tables and allow_subquery:
            sql = replace_query_tables_with_cte(sql, self.data_source)

        self.validate_query(sql)
        # to fix special characters in query like %
        sql = sql.replace("%%", "%") if is_native_query else sql
        sql = text(sql) if is_native_query else sql
        with self.connect() as connection:
            with Timer() as t:
                res = connection.execute(sql)
            create_execution_log(sql, self.data_source, t.elapsed)
            columns = [ResultColumn.make(d[0], d[1]) for d in res.cursor.description]
            rows = [list(r) for r in res.fetchall()]
            rows = [r[0] for r in rows] if pluck else rows
            return [columns] + rows if return_columns else rows

    def validate_query(self, query):
        select_or_with = str(query).strip().lower().startswith(("select", "with"))
        if not select_or_with:
            frappe.throw("Only SELECT and WITH queries are allowed")

    def table_exists(self, table: str):
        """
        While importing a table, check if the table exists in the database
        """
        raise NotImplementedError

    def import_table(self, import_doc: InsightsTableImport):
        """
        Imports the table into the database
        """
        raise NotImplementedError

    def sync_tables(self):
        raise NotImplementedError

    def get_table_columns(self, table):
        raise NotImplementedError

    def get_column_options(self, table, column, search_text=None, limit=50):
        raise NotImplementedError

    def get_table_preview(self):
        raise NotImplementedError

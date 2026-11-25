import os
import sys
import django
import pymysql

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexgrad.settings')
django.setup()

from django.apps import apps

def main():
    print("--- NEXGRAD Database Foreign Key Constraints Fix ---")
    
    # 1. Build dictionary of expected ON DELETE rules from Django models
    rules = {}
    for model in apps.get_models():
        table = model._meta.db_table
        for field in model._meta.fields:
            if field.is_relation and (field.many_to_one or field.one_to_one):
                on_del = getattr(field.remote_field, 'on_delete', None)
                if on_del:
                    name = on_del.__name__
                    if name == 'CASCADE':
                        rule = 'CASCADE'
                    elif name == 'SET_NULL':
                        rule = 'SET NULL'
                    elif name == 'SET_DEFAULT':
                        rule = 'SET DEFAULT'
                    elif name == 'PROTECT':
                        rule = 'RESTRICT'
                    elif name == 'DO_NOTHING':
                        rule = 'NO ACTION'
                    else:
                        rule = 'RESTRICT'
                else:
                    rule = 'RESTRICT'
                
                rules[(table, field.column)] = (
                    rule,
                    field.null,
                    field.related_model._meta.db_table,
                    field.related_model._meta.pk.column
                )

        # Handle many-to-many through tables
        for m2m in model._meta.many_to_many:
            through = m2m.remote_field.through
            through_table = through._meta.db_table
            for f in through._meta.fields:
                if f.is_relation and (f.many_to_one or f.one_to_one):
                    rules[(through_table, f.column)] = (
                        'CASCADE',
                        False,
                        f.related_model._meta.db_table,
                        f.related_model._meta.pk.column
                    )

    # 2. Connect to MySQL database
    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='nexgrad',
        autocommit=True
    )
    cursor = conn.cursor()

    # Query all foreign key constraints in nexgrad
    cursor.execute("""
        SELECT k.TABLE_NAME, k.COLUMN_NAME, k.CONSTRAINT_NAME, 
               k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME, r.DELETE_RULE
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
        JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS r
          ON k.CONSTRAINT_NAME = r.CONSTRAINT_NAME AND k.CONSTRAINT_SCHEMA = r.CONSTRAINT_SCHEMA
        WHERE k.TABLE_SCHEMA = 'nexgrad' AND k.REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY k.TABLE_NAME, k.COLUMN_NAME;
    """)
    current_fks = cursor.fetchall()
    print(f"Total foreign key constraints in database: {len(current_fks)}")

    mismatches = []
    for tbl, col, cname, ref_tbl, ref_col, del_rule in current_fks:
        rule_info = rules.get((tbl, col))
        if rule_info:
            exp_rule, is_nullable, exp_ref_tbl, exp_ref_col = rule_info
            if del_rule != exp_rule:
                mismatches.append((tbl, col, cname, ref_tbl, ref_col, del_rule, exp_rule, is_nullable))
        else:
            print(f"Warning: No Django model mapping for {tbl}.{col}")

    print(f"Found {len(mismatches)} constraints requiring ON DELETE updates.\n")

    if not mismatches:
        print("All foreign key constraints already match intended rules!")
        return

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    success_count = 0
    error_count = 0

    for tbl, col, cname, ref_tbl, ref_col, del_rule, exp_rule, is_nullable in mismatches:
        try:
            # Drop old foreign key constraint
            drop_sql = f"ALTER TABLE `{tbl}` DROP FOREIGN KEY `{cname}`;"
            cursor.execute(drop_sql)

            # Re-add with explicit ON DELETE rule
            add_sql = (
                f"ALTER TABLE `{tbl}` ADD CONSTRAINT `{cname}` "
                f"FOREIGN KEY (`{col}`) REFERENCES `{ref_tbl}` (`{ref_col}`) "
                f"ON DELETE {exp_rule};"
            )
            cursor.execute(add_sql)
            print(f"OK: `{tbl}`.`{col}` ({cname}) -> {del_rule} => {exp_rule}")
            success_count += 1
        except Exception as e:
            print(f"ERROR: Failed updating `{tbl}`.`{col}` ({cname}): {e}")
            error_count += 1

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.close()

    print(f"\nCompleted: {success_count} updated, {error_count} errors.")

if __name__ == '__main__':
    main()


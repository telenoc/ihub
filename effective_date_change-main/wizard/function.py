from odoo.http import request
from .query import QueryList


def do_query(query, key):
    request.env.cr.execute(query, [key])


def do_update(query, key1, key2):
    request.env.cr.execute(query, [key1, key2])


def concat(pulled_name):
    percent_pulled_name = str(pulled_name + "%")
    return percent_pulled_name


def account_move_concat(year, date):
    stj_account_move_find_sequence = str("STJ" + "/" + year + "/" + date.zfill(2) + "/")
    return stj_account_move_find_sequence


def account_move_new_name(year, date, number):
    stj_account_move_new_name = str("STJ" + "/" + year + "/" + date.zfill(2) + "/" + str(number).zfill(4))
    return stj_account_move_new_name


# SilkSoft addition
def update_manufacturing_products_entry(context, year, month, ref, seq):
    query = QueryList()  # instantiation query
    stj = "STJ"
    stj_man_cost_year = str(year)
    stj_man_cost_month = str(month)
    stj_find_sequence = str(
        stj + "/" + stj_man_cost_year + "/" + stj_man_cost_month.zfill(2) + "/")

    stj_sequences = [stj for stj in context.env['account.move'].search(
        [('name', 'ilike', stj_find_sequence)]).mapped('name')]
    if stj_sequences == []:
        stj_sequences_addition = 1
        stj_sequences_new_name = stj + "/" + stj_man_cost_year + "/" + stj_man_cost_month.zfill(
            2) + "/" + str(stj_sequences_addition).zfill(4)
        do_update(query.update_journal_sequence_by_ref, stj_sequences_addition, ref)
        do_update(query.update_journal_prefix_by_ref, stj_find_sequence, ref)
        context.env.cr.execute("UPDATE account_move SET name = (%s) WHERE ref = %s", [stj_sequences_new_name, ref])
    else:
        if seq == 0 or None:
            stj_sequences_max = str(max(stj_sequences))
            if stj_sequences_max[:12] == stj_find_sequence:
                stj_sequences_trim = int(stj_sequences_max.replace(stj_find_sequence, ''))
            else:
                stj_sequences_trim = len(stj_sequences)
        else:
            stj_sequences_trim = seq
        stj_sequences_addition = str(stj_sequences_trim + 1)
        stj_sequences_new_name = stj + "/" + stj_man_cost_year + "/" + stj_man_cost_month.zfill(
            2) + "/" + stj_sequences_addition.zfill(4)
        do_update(query.update_journal_sequence_by_ref, stj_sequences_addition, ref)
        do_update(query.update_journal_prefix_by_ref, stj_find_sequence, ref)
        context.env.cr.execute("UPDATE account_move SET name = (%s) WHERE ref = %s", [stj_sequences_new_name, ref])

    return int(stj_sequences_addition)

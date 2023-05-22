from odoo import api, models, fields
from .query import QueryList
from .function import *
from datetime import datetime
from odoo.exceptions import UserError


class ChangeEffectiveWizard(models.TransientModel):
    _name = "change.effective.wizard"

    # Definisikan field wizard
    effective_date = fields.Datetime(string="Effective Date", help="Date at which the transfer is processed")
    rewrite_related_picking = fields.Boolean(string="Apply to Other Stock Picking", default=False, help="Also Apply to Other Stock Picking Which Has the Same Source Document Name")

    # Onchange sebagai reminder ketika memilih tanggal masa depan untuk memilih tanggal di masa lalu saja
    @api.onchange('effective_date')
    def effective_future(self):
        selected = self.env['stock.picking'].browse(self._context.get('active_ids', []))
        current_date = datetime.now()

        # Bandingkan tanggal hari ini dengan tanggal yang terpilih
        # Jika tanggal tidak sesuai (lebih ke masa depan) maka tidak bisa proses
        if self.effective_date and self.effective_date > current_date:
            raise UserError('The date selected is still in the future. Make sure to only do a backdate!')

    # Simpan record
    def update_effective_date(self):
        query = QueryList()  # instantiation query
        product_journal_sequence = 0  # Journal sequence for manufacturing product
        if self._context.get("active_model") != "mrp.production":
        # Memanggil record active_id ke dalam transient model
            for picking in self.env['stock.picking'].browse(self._context.get('active_ids', [])):

                # Mendefinisikan field yang ada di wizard (model.Transient)
                picking_name = picking.name
                wildcard_picking_name = concat(picking_name)
                picking_source_document = picking.origin
                selected_effective_date = self.effective_date

                # Melakukan pengecekan internal atau eksternal transfer
                # Jika picking_source_document ada, maka itu adalah eksternal transfer
                if picking_source_document:
                    # Jika rewrite_related_picking tidak dicentang, maka update satu picking terpilih saja
                    if self.rewrite_related_picking == False:
                        # Update picking
                        do_update(query.update_stock_picking_by_name, self.effective_date, picking_name)

                        # Update Sale Order
                        do_update(query.update_sale_order, self.effective_date, picking_source_document)

                        # Update Purchase Order
                        do_update(query.update_purchase_order, self.effective_date, picking_source_document)

                        # Update account_move date
                        do_update(query.update_journal_entry, self.effective_date, wildcard_picking_name)

                        # Update account_move (journal entry)
                        stj_account_move_find_sequence = account_move_concat(str(selected_effective_date.year), str(selected_effective_date.month))
                        stj_account_move_sequences = [stj_account_move for stj_account_move in self.env['account.move'].search([('name', 'ilike', stj_account_move_find_sequence)]).mapped('name')]
                        if stj_account_move_sequences == []:
                            ids = self.env['account.move'].search([('ref', 'ilike', wildcard_picking_name)]).mapped('id')
                            number = 1
                            while number <= len(ids):
                                for id in ids:
                                    stj_account_move_new_name = account_move_new_name(str(selected_effective_date.year), str(selected_effective_date.month), str(number))
                                    self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE id = (%s)", [stj_account_move_new_name, id])
                                    number += 1
                        else:
                            stj_sequences_max = str(max(stj_account_move_sequences))
                            stj_sequences_trim = int(stj_sequences_max.replace(stj_account_move_find_sequence, ''))
                            stj_sequences_addition = stj_sequences_trim + 1

                            ids = self.env['account.move'].search([('ref', 'ilike', wildcard_picking_name)]).mapped('id')
                            starter = stj_sequences_addition
                            number = 1
                            while number <= len(ids):
                                for id in ids:
                                    stj_account_move_new_name = account_move_new_name(str(selected_effective_date.year), str(selected_effective_date.month), str(starter))
                                    self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE id = %s", [stj_account_move_new_name, id])
                                    starter += 1
                                    number += 1

                        # Update account_move_line
                        do_update(query.update_journal_entry_line, self.effective_date, wildcard_picking_name)

                        # Update stock_move
                        do_update(query.update_stock_move, self.effective_date, picking_name)

                        # Update stock_move_line
                        do_update(query.update_stock_move_line, self.effective_date, picking_name)

                        # Update stock valuation
                        stock_move_id = self.env['stock.move'].search([('reference','=', picking_name)])
                        do_update(query.update_inventory_valuation_date, self.effective_date, stock_move_id.id)


                        # Update landed cost record
                        # Cek apakah system menggunakan landed cost atau tidak
                        # jika iya, pastikan apakah yang sekarang di update merupakan sales order
                        # jika bukan, consider itu adalah purchase atau pembelian
                        find_module = self.env['ir.module.module'].search([('name', '=', 'stock_landed_costs')])
                        if find_module.state == 'installed':
                            for so_sale_id in [self.env['stock.picking'].search([('origin', '=', picking_source_document)])]:
                                is_so = int(so_sale_id.sale_id)
                                if is_so > 0:
                                    pass
                                else:
                                    vendor_bill = self.env['account.move'].search([('invoice_origin', '=', picking_source_document)])
                                    landed_cost = self.env['stock.landed.cost'].search([('vendor_bill_id', '=', int(vendor_bill.id))])
                                    check_landed_cost = [landed_cost.id]
                                    if check_landed_cost == [False]:
                                        print("Landed cost might not created yet, skipping landed cost update")
                                        pass
                                    else:
                                        # Ubah Date
                                        # Ubah date landed cost STJ Line
                                        self.env.cr.execute("UPDATE account_move_line SET date = (%s) WHERE ref = %s", [selected_effective_date, landed_cost.name])

                                        # Ubah date landed cost STJ
                                        landed = self.env['account.move'].search([('ref', '=', landed_cost.name)])
                                        self.env.cr.execute("UPDATE account_move SET date = (%s) WHERE ref = %s", [selected_effective_date, landed_cost.name])

                                        # Ubah date landed cost
                                        landed_cost.date = self.effective_date

                                        # UBAH NAMA
                                        # Ubah landed cost STJ name
                                        landed_cost_stj = self.env['account.move'].search([('ref', '=', landed_cost.name)])

                                        stj = "STJ"
                                        stj_landed_cost_year = str(selected_effective_date.year)
                                        stj_landed_cost_month = str(selected_effective_date.month)
                                        stj_find_sequence = str(stj + "/" + stj_landed_cost_year + "/" + stj_landed_cost_month.zfill(2) + "/")

                                        stj_sequences = [stj for stj in self.env['account.move'].search([('name', 'ilike', stj_find_sequence)]).mapped('name')]
                                        if stj_sequences == []:
                                            stj_sequences_addition = 1
                                            stj_sequences_new_name = stj + "/" + stj_landed_cost_year + "/" + stj_landed_cost_month.zfill(2) + "/" + str(stj_sequences_addition).zfill(4)
                                            do_update(query.update_journal_sequence_by_ref, stj_sequences_addition, landed_cost.name)
                                            do_update(query.update_journal_prefix_by_ref, stj_find_sequence, landed_cost.name)
                                            self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE ref = %s", [stj_sequences_new_name, landed_cost.name])
                                        else:
                                            stj_sequences_max = str(max(stj_sequences))
                                            stj_sequences_trim = int(stj_sequences_max.replace(stj_find_sequence, ''))
                                            stj_sequences_addition = str(stj_sequences_trim + 1)
                                            stj_sequences_new_name = stj + "/" + stj_landed_cost_year + "/" + stj_landed_cost_month.zfill(2) + "/" + stj_sequences_addition.zfill(4)
                                            do_update(query.update_journal_sequence_by_ref, stj_sequences_addition, landed_cost.name)
                                            do_update(query.update_journal_prefix_by_ref, stj_find_sequence, landed_cost.name)
                                            self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE ref = %s", [stj_sequences_new_name, landed_cost.name])

                                        # Ubah landed cost name
                                        landed_cost_ir_sequence = self.env['ir.sequence'].search([('code', '=', 'stock.landed.cost')])
                                        # Split Sequence Prefix of Landed Cost
                                        newstring, _ = landed_cost_ir_sequence.prefix.split('/%')
                                        landed_cost_prefix = newstring.strip()

                                        # Next number
                                        landed_cost_next_number = str(int(landed_cost_ir_sequence.number_next_actual))
                                        zfill = landed_cost_next_number.zfill(landed_cost_ir_sequence.padding)

                                        # Landed Cost Ubah nama
                                        landed_cost_new_name = landed_cost_prefix + "/" + str(selected_effective_date.year) + "/" + zfill

                                        self.env.cr.execute("UPDATE stock_landed_cost SET name = (%s) WHERE vendor_bill_id = %s", [landed_cost_new_name, int(vendor_bill.id)])

                                        # Reset landed_cost_sequence
                                        landed_cost_ir_sequence.number_next_actual = landed_cost_ir_sequence.number_next_actual + 1

                                        # Update STJ Ref
                                        self.env.cr.execute("UPDATE account_move SET ref = (%s) WHERE name = %s", [landed_cost_new_name, stj_sequences_new_name])

                        else:
                            print("Skipping landed cost update, there might be no landed cost settings applied")
                    else:
                        do_query(query.find_name_from_stock_picking, picking_source_document)
                        stock_picking = [pulled_stock_picking_as_row[0] for pulled_stock_picking_as_row in self.env.cr.fetchall()]
                        percentage_stock_picking = [pickings_found + "%" for pickings_found in stock_picking]

                        pulled_stock_picking_tuples = tuple(stock_picking)
                        if pulled_stock_picking_tuples == ():
                            # Not changing anything because origin is not set
                            pass
                        else:
                            # Update stock_picking
                            do_update(query.update_stock_picking_by_origin, self.effective_date, picking_source_document)

                            # Update sale_order
                            do_update(query.update_sale_order, self.effective_date, picking_source_document)

                            # Update purchase_order
                            do_update(query.update_purchase_order, self.effective_date, picking_source_document)

                            # Update account_move date
                            do_update(query.update_journal_entry_by_ref_tuple, self.effective_date, percentage_stock_picking)

                            # Update account_move name
                            stj_account_move_find_sequence = account_move_concat(str(selected_effective_date.year), str(selected_effective_date.month))
                            stj_account_move_sequences = [stj_account_move for stj_account_move in self.env['account.move'].search( [('name', 'ilike', stj_account_move_find_sequence)]).mapped('name')]

                            if stj_account_move_sequences == []:
                                print("Generate dari awal")
                                ids = self.env['account.move'].search([('ref', 'ilike', wildcard_picking_name)]).mapped('id')
                                number = 1
                                while number <= len(ids):
                                    for id in ids:
                                        stj_account_move_new_name = account_move_new_name(str(selected_effective_date.year), str(selected_effective_date.month), str(number))
                                        self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE id = (%s)", [stj_account_move_new_name, id])
                                        number += 1
                            else:
                                print("Lanjutkan nomor sebelumnya")
                                stj_sequences_max = str(max(stj_account_move_sequences))
                                stj_sequences_trim = int(stj_sequences_max.replace(stj_account_move_find_sequence, ''))
                                stj_sequences_addition = stj_sequences_trim + 1

                                ids = self.env['account.move'].search([('ref', 'ilike', wildcard_picking_name)]).mapped('id')
                                starter = stj_sequences_addition
                                number = 1
                                while number <= len(ids):
                                    for id in ids:
                                        stj_account_move_new_name = account_move_new_name(str(selected_effective_date.year), str(selected_effective_date.month), str(starter))
                                        self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE id = %s", [stj_account_move_new_name, id])
                                        starter += 1
                                        number += 1

                            # Update account_move_line
                            do_update(query.update_journal_entry_line_by_ref_tuple, self.effective_date, percentage_stock_picking)

                            # Update Stock Move
                            do_update(query.update_stock_move_by_ref_tuple, self.effective_date, pulled_stock_picking_tuples)

                            # Update stock move line
                            do_update(query.update_stock_move_line_by_ref_tuple, self.effective_date, pulled_stock_picking_tuples)

                            # Update stock valuation
                            for pickings in stock_picking:
                                for stock_move_id in self.env['stock.move'].search([('reference', '=', pickings)]):
                                    do_update(query.update_inventory_valuation_date, self.effective_date, int(stock_move_id))
                                    print(f"stock picking dengan nomor {pickings} dan stock move id {stock_move_id} telah berhasil diganti")

                            # Update landed cost record
                            # Cek apakah system menggunakan landed cost atau tidak
                            # jika iya, pastikan apakah yang sekarang di update merupakan sales order
                            # jika bukan, consider itu adalah purchase atau pembelian
                            find_module = self.env['ir.module.module'].search([('name', '=', 'stock_landed_costs')])
                            if find_module.state == 'installed':
                                for so_sale_id in [self.env['stock.picking'].search([('origin', '=', picking_source_document)])]:
                                    is_so = int(so_sale_id.sale_id)
                                    if is_so > 0:
                                        pass
                                    else:
                                        vendor_bill = self.env['account.move'].search( [('invoice_origin', '=', picking_source_document)])
                                        landed_cost = self.env['stock.landed.cost'].search([('vendor_bill_id', '=', int(vendor_bill.id))])
                                        check_landed_cost = [landed_cost.id]
                                        if check_landed_cost == [False]:
                                            print("Landed cost might not created yet, skipping landed cost update")
                                            pass
                                        else:
                                            # Ubah Date
                                            # Ubah date landed cost STJ Line
                                            self.env.cr.execute("UPDATE account_move_line SET date = (%s) WHERE ref = %s",
                                                                [selected_effective_date, landed_cost.name])

                                            # Ubah date landed cost STJ
                                            landed = self.env['account.move'].search([('ref', '=', landed_cost.name)])
                                            self.env.cr.execute("UPDATE account_move SET date = (%s) WHERE ref = %s",
                                                                [selected_effective_date, landed_cost.name])

                                            # Ubah date landed cost
                                            landed_cost.date = self.effective_date

                                            # UBAH NAMA
                                            # Ubah landed cost STJ name
                                            landed_cost_stj = self.env['account.move'].search([('ref', '=', landed_cost.name)])

                                            stj = "STJ"
                                            stj_landed_cost_year = str(selected_effective_date.year)
                                            stj_landed_cost_month = str(selected_effective_date.month)
                                            stj_find_sequence = str(
                                                stj + "/" + stj_landed_cost_year + "/" + stj_landed_cost_month.zfill(2) + "/")

                                            stj_sequences = [stj for stj in self.env['account.move'].search(
                                                [('name', 'ilike', stj_find_sequence)]).mapped('name')]
                                            if stj_sequences == []:
                                                stj_sequences_new_name = stj + "/" + stj_landed_cost_year + "/" + stj_landed_cost_month.zfill(
                                                    2) + "/" + str(1).zfill(4)
                                                self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE ref = %s",
                                                                    [stj_sequences_new_name, landed_cost.name])
                                            else:
                                                stj_sequences_max = str(max(stj_sequences))
                                                stj_sequences_trim = int(stj_sequences_max.replace(stj_find_sequence, ''))
                                                stj_sequences_addition = str(stj_sequences_trim + 1)
                                                stj_sequences_new_name = stj + "/" + stj_landed_cost_year + "/" + stj_landed_cost_month.zfill(
                                                    2) + "/" + stj_sequences_addition.zfill(4)
                                                self.env.cr.execute("UPDATE account_move SET name = (%s) WHERE ref = %s",
                                                                    [stj_sequences_new_name, landed_cost.name])

                                            # Ubah landed cost name
                                            landed_cost_ir_sequence = self.env['ir.sequence'].search(
                                                [('code', '=', 'stock.landed.cost')])
                                            # Split Sequence Prefix of Landed Cost
                                            newstring, _ = landed_cost_ir_sequence.prefix.split('/%')
                                            landed_cost_prefix = newstring.strip()

                                            # Next number
                                            landed_cost_next_number = str(int(landed_cost_ir_sequence.number_next_actual))
                                            zfill = landed_cost_next_number.zfill(landed_cost_ir_sequence.padding)

                                            # Landed Cost Ubah nama
                                            landed_cost_new_name = landed_cost_prefix + "/" + str(
                                                selected_effective_date.year) + "/" + zfill

                                            self.env.cr.execute(
                                                "UPDATE stock_landed_cost SET name = (%s) WHERE vendor_bill_id = %s",
                                                [landed_cost_new_name, int(vendor_bill.id)])

                                            # Reset landed_cost_sequence
                                            landed_cost_ir_sequence.number_next_actual = landed_cost_ir_sequence.number_next_actual + 1

                                            # Update STJ Ref
                                            self.env.cr.execute("UPDATE account_move SET ref = (%s) WHERE name = %s",
                                                                [landed_cost_new_name, stj_sequences_new_name])
                            else:
                                print("Skipping landed cost update, there might be no landed cost settings applied")

                else:
                    # Update internal transfer
                    do_update(query.update_stock_picking_by_name, self.effective_date, picking_source_document)

                    # Update stock move
                    do_update(query.update_stock_move, self.effective_date, picking_source_document)

                    # Update stock_move_line
                    do_update(query.update_stock_move_line, self.effective_date, picking_source_document)
        # SilkSoft Additions
        else:
            for picking in self.env['mrp.production'].browse(self._context.get('active_ids', [])):
                picking_document_name = picking.name
                picking_product_name = picking.product_id.name
                old_date_month = picking.date_planned_start.month
                old_date_year = picking.date_planned_start.year
                do_update(query.update_manufacturing_by_name, self.effective_date, picking_document_name)

                # Update stock move
                do_update(query.update_stock_move, self.effective_date, picking_document_name)

                # Update stock_move_line
                do_update(query.update_stock_move_line, self.effective_date, picking_document_name)

                # Update scraps
                for scraps in self.env['stock.scrap'].search([('production_id', '=', picking.id)]):
                    scrap_id = scraps.id
                    do_update(query.update_scraps_by_id, self.effective_date, scrap_id)

                # Update stock_valuation_layer
                valuation_product_name = picking_document_name + " - " + picking_product_name
                do_update(query.update_inventory_valuation_date_desc, self.effective_date, valuation_product_name)

                # Update account_move date & ref
                produced_product_entry = self.env['account.move'].search([('ref', 'ilike', picking_document_name)])
                for rec in produced_product_entry:
                    do_update(query.update_journal_entry_date, self.effective_date, rec.ref)
                    do_update(query.update_journal_entry_line, self.effective_date, rec.ref)
                    do_update(query.update_inventory_valuation_date, self.effective_date, rec.id)
                    if old_date_year != self.effective_date.year or old_date_month != self.effective_date.month:
                        product_journal_sequence = update_manufacturing_products_entry(self, self.effective_date.year
                                                                                       , self.effective_date.month
                                                                                       , rec.ref
                                                                                       , product_journal_sequence)

                for products in picking.move_raw_ids:
                    # product = products.product_id.name
                    # valuation_name = picking_document_name + " - " + product
                    check_inventory = self.env['stock.valuation.layer'].search([('description', 'ilike', picking_document_name)])
                    for rec in check_inventory:
                        do_update(query.update_inventory_valuation_date_desc, self.effective_date, rec.description)
                #
                #     # Update account_move date & ref
                #     material_used_entry = self.env['account.move'].search([('ref', 'ilike', picking_document_name)])
                #     for rec in material_used_entry:
                #         do_update(query.update_journal_entry_date, self.effective_date, rec.ref)
                #         do_update(query.update_journal_entry_line, self.effective_date, rec.ref)
                #     if old_date_year != self.effective_date.year or old_date_month != self.effective_date.month:
                #         product_journal_sequence = update_manufacturing_products_entry(self, self.effective_date.year
                #                                                                        , self.effective_date.month
                #                                                                        , valuation_name
                #                                                                        , product_journal_sequence)

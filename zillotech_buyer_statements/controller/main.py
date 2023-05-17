from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.payment import utils as payment_utils
from odoo import http, Command, SUPERUSER_ID
from odoo.addons.http_routing.models.ir_http import unslug, slug
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.tools import consteq


class CustomerPortalStatements(PortalAccount):

    @http.route(['/report/statements/page/<int:partner>/<string:filename>'], type='http', auth="user", website=True)
    def portal_statements_datas(self, partner=None, filename=None, **kw):
        partner_id = request.env['res.partner'].sudo().browse(int(partner))

        if filename == 'zillotech_buyer_statements.report_buyer_statements':
            docids = [partner_id.id]
            report_datas = request.env['report.zillotech_buyer_statements.report_buyer_statements'].sudo()._get_report_values(
                docids, data={'partner_id': partner_id})
            report_datas['buyer_statement'] = True
            report_datas['weekly_buyer_statement'] = report_datas['monthly_buyer_statement'] = report_datas[
                'filtered_buyer_statement'] = report_datas['custom_buyer_statement'] = report_datas[
                'overdue_buyer_statement'] = False
            report_datas['content_dict']['file_name'] = filename
            return request.render('zillotech_buyer_statements.portal_my_statement_invoices', report_datas)

        if filename == 'zillotech_buyer_statements.report_buyer_fil_statements':
            docids = [partner_id.id]
            report_datas = request.env[
                'report.zillotech_buyer_statements.report_buyer_fil_statements'].sudo()._get_report_values(
                docids, data={'partner_id': partner_id})
            report_datas['filtered_buyer_statement'] = True
            report_datas['weekly_buyer_statement'] = report_datas['monthly_buyer_statement'] = report_datas[
                'buyer_statement'] = report_datas['custom_buyer_statement'] = report_datas[
                'overdue_buyer_statement'] = False
            report_datas['content_dict']['file_name'] = filename
            return request.render('zillotech_buyer_statements.portal_my_statement_invoices', report_datas)

        if filename == 'zillotech_buyer_statements.report_buyer_w_statements':
            docids = [partner_id.id]
            report_datas = request.env[
                'report.zillotech_buyer_statements.report_buyer_w_statements'].sudo()._get_report_values(
                docids, data={'partner_id': partner_id})
            report_datas['weekly_buyer_statement'] = True
            report_datas['monthly_buyer_statement'] = report_datas['filtered_buyer_statement'] = report_datas[
                'buyer_statement'] = report_datas['custom_buyer_statement'] = report_datas[
                'overdue_buyer_statement'] = False
            report_datas['content_dict']['file_name'] = filename
            return request.render('zillotech_buyer_statements.portal_my_statement_invoices', report_datas)

        if filename == 'zillotech_buyer_statements.report_buyer_m_statements':
            docids = [partner_id.id]
            report_datas = request.env[
                'report.zillotech_buyer_statements.report_buyer_m_statements'].sudo()._get_report_values(
                docids, data={'partner_id': partner_id})
            report_datas['monthly_buyer_statement'] = True
            report_datas['weekly_buyer_statement'] = report_datas['filtered_buyer_statement'] = report_datas[
                'buyer_statement'] = report_datas['custom_buyer_statement'] = report_datas[
                'overdue_buyer_statement'] = False
            report_datas['content_dict']['file_name'] = filename
            return request.render('zillotech_buyer_statements.portal_my_statement_invoices', report_datas)

        if filename == 'zillotech_buyer_statements.report_buyer_c_statements':
            docids = [partner_id.id]
            report_datas = request.env[
                'report.zillotech_buyer_statements.report_buyer_c_statements'].sudo()._get_report_values(
                docids, data={'partner_id': partner_id})
            report_datas['custom_buyer_statement'] = True
            report_datas['weekly_buyer_statement'] = report_datas['filtered_buyer_statement'] = report_datas[
                'buyer_statement'] = report_datas['monthly_buyer_statement'] = report_datas[
                'overdue_buyer_statement'] = False
            report_datas['content_dict']['file_name'] = filename
            return request.render('zillotech_buyer_statements.portal_my_statement_invoices', report_datas)

        if filename == 'zillotech_buyer_statements.report_buyer_o_statements':
            docids = [partner_id.id]
            report_datas = request.env[
                'report.zillotech_buyer_statements.report_buyer_o_statements'].sudo()._get_report_values(
                docids, data={'partner_id': partner_id})
            report_datas['overdue_buyer_statement'] = True
            report_datas['weekly_buyer_statement'] = report_datas['filtered_buyer_statement'] = report_datas[
                'buyer_statement'] = report_datas['monthly_buyer_statement'] = report_datas[
                'custom_buyer_statement'] = False
            report_datas['content_dict']['file_name'] = filename
            return request.render('zillotech_buyer_statements.portal_my_statement_invoices', report_datas)

    @http.route(['/report/statements/<partner>'], type='http', auth="user", website=True)
    def meta_data(self, partner, **kw):
        _, partner_id = unslug(partner)
        if partner_id:
            partner_data = request.env['res.partner'].sudo().browse(partner_id)
            return request.redirect(
                '/report/statements/page/%i' % partner_data.id + '/' + '%s' % partner_data.report_name)

    @http.route(['/portal_pay'], type='http', auth="user", website=True)
    def portal_pay_multi_invoices(self, partner=None, **kw):
        partner_data = request.env['res.partner'].sudo().browse(int(partner))
        if request.httprequest.form.getlist('selected_invoice_ids'):
            selected_list = [request.env['account.move'].browse(int(x)) for x in
                             request.httprequest.form.getlist('selected_invoice_ids')]
            partner_data.write({'multi_inv_ids': [val.id for val in selected_list]})
        else:
            selected_list = [x for x in partner_data.multi_inv_ids]

        logged_in = not request.env.user._is_public()
        if not selected_list:
            partner_data.inv_null = True
            return request.redirect(
                '/report/statements/page/%i' % partner_data.id + '/' + '%s' % partner_data.report_name)
        else:
            partner_data.inv_null = False
            sel_inv_reference = [x.ref if x.ref else x.name for x in selected_list]
            partner_data.inv_reference = ",".join(sel_inv_reference)
            invoices = request.env['account.move'].browse([x.id for x in selected_list])
            currency = [y for y in
                        request.env['account.move'].browse([x.id for x in selected_list]).mapped('currency_id')]
            if len(currency) > 1:
                return request.redirect(
                    '/report/statements/page/%i' % partner_data.id + '/' + '%s' % partner_data.report_name)
            inv_partner_id = invoices.mapped("partner_id")
            partner_id = request.env.user.partner_id.id if logged_in else inv_partner_id[0].id
            amount = sum([x.amount_total for x in invoices])
            partner_data.multi_inv_total = float(amount)
            access_token = payment_utils.generate_access_token(partner_id, amount, currency[0].id)
            if invoices:
                for inv in invoices:
                    inv.multi_access_token = access_token
            try:
                invoices_sudo = self._document_multi_check_access('account.move', [z.id for z in selected_list],
                                                                  access_token)
            except (AccessError, MissingError):
                return request.redirect('/my')

            values = self._multiple_invoice_get_page_view_values(invoices_sudo, access_token, amount, currency[0],
                                                                 partner_data, **kw)
            return request.render("zillotech_buyer_statements.portal_invoice_payment_option", values)

    def _multiple_invoice_get_page_view_values(self, invoices, access_token, amount, currency, partner_data, **kw):
        logged_in = not request.env.user._is_public()
        values = {
            'page_name': 'invoices',
            'partner': partner_data,
            'invoices': invoices,
            'invoice': False,
        }
        amount = 0
        for inv in invoices:
            amount += inv.amount_total
        company_id = invoices.mapped("company_id")[0]
        inv_partner_id = invoices.mapped("partner_id")[0]
        partner_id = request.env.user.partner_id.id if logged_in else inv_partner_id.id
        acquirers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            company_id.id or request.env.company.id,
            partner_id,
            amount,
            currency_id=currency[0].id,
        )  # In sudo mode to read the fields of acquirers and partner (if not logged in)
        tokens = request.env['payment.token'].search(
            [('provider_id', 'in', acquirers_sudo.ids)]
        )  # Tokens are cleared at the end if the user is not logged in
        fees_by_acquirer = {
            acq_sudo: acq_sudo._compute_fees(
                amount, currency[0].id, inv_partner_id.country_id
            ) for acq_sudo in acquirers_sudo.filtered('fees_active')
        }
        q = ','.join([str(x.id) for x in invoices])
        values.update({
            'acquirers': acquirers_sudo,
            'tokens': tokens,
            'fees_by_acquirer': fees_by_acquirer,
            'show_tokenize_input': logged_in,  # Prevent public partner from saving payment methods
            'amount': amount,
            'currency': currency,
            'partner_id': partner_id,
            'access_token': access_token,
            'transaction_route': f'/multi_invoice/transaction/{partner_data.id}/{str(q)}',
            'landing_route': '/multi_invoice/success'
        })

        if not logged_in:
            values.update({
                'existing_token': bool(tokens),
                'tokens': request.env['payment.token'],
            })
        return values

    def _document_multi_check_access(self, model_name, document_id, access_token=None):
        # Multi invoice access token check
        documents = request.env[model_name].browse(document_id)
        for document in documents:
            document_sudo = document.with_user(SUPERUSER_ID).exists()
            if not document_sudo:
                raise MissingError(_("This document does not exist."))
            try:
                document.check_access_rights('read')
                document.check_access_rule('read')
            except AccessError:
                if not access_token or not document_sudo.multi_access_token or not consteq(
                        document_sudo.multi_access_token,
                        access_token):
                    raise
        return documents

    @http.route(['/multi_invoice/success'], type='http', auth="user", website=True)
    def portal_multi_payment_success(self, **kw):
        # Landing route redirect template
        return request.render("zillotech_buyer_statements.portal_invoice_payment_success", {})


class CustomerPortalPayment(payment_portal.PaymentPortal):

    @http.route('/multi_invoice/transaction/<int:partner>/<string:invoices>', type='json', auth='public')
    def multi_invoice_transaction(self, partner, invoices, access_token, **kwargs):
        inv_char = [int(x) for x in invoices.split(',')]
        # Check access token
        try:
            self._document_multi_check_access('account.move', inv_char, access_token)
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError("The access token is invalid.")

        kwargs['reference_prefix'] = request.env['res.partner'].browse(
            partner).inv_reference
        kwargs.pop('custom_create_values', None)  # Don't allow passing arbitrary create values
        tx_sudo = self._create_transaction(
            custom_create_values={'invoice_ids': [Command.set(inv_char)]}, **kwargs,
        )

        return tx_sudo._get_processing_values()

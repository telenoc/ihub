/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { AccountPaymentField } from '@account/components/account_payment_field/account_payment_field';
console.log('AccountPaymentField------------', AccountPaymentField);
patch(AccountPaymentField.prototype, 'account_partial_payment', {
    
    async assignOutstandingCredit(id) {
        console.log('1_ id : ', id);
        console.log('1_ this : ', this);
        console.log('this.props.record.resModel',this.props.record.resModel);
        // const action = await this.orm.call('partial.payment.wizard', 'sr_partial_payment_wizard_action', [this.move_id], {'line_id' : id, 'move_id' : this.move_id});
        // this.action.doAction(action);

        this.action.doAction({
            type: "ir.actions.act_window",
            target: "new",
            name: 'Partial Payment Wizard',
            res_model: "partial.payment.wizard",
            views: [[false, "form"]],
            context: {
                active_id: this.move_id,
                line_id: id,
            }
        });

        // await this.orm.call(this.props.record.resModel, 'js_assign_outstanding_line', [this.move_id, id], {});
        // await this.props.record.model.root.load();
        // this.props.record.model.notify();
    }
});
# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    master_graph_db_url = fields.Char(u'Master Graph DB HOST')
    master_graph_db_account = fields.Char(u'Master Graph DB 帐号', default='admin')
    master_graph_db_password = fields.Char(u'Master Graph DB 密码', default='admin')

    slave_graph_db_url = fields.Char(u'Slave Graph DB HOST')
    slave_graph_db_account = fields.Char(u'Slave Graph DB 帐号', default='admin')
    slave_graph_db_password = fields.Char(u'Slave Graph DB 密码', default='admin')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        res.update(
            master_graph_db_url=ICPSudo.get_param('master.graph.db.url'),
            master_graph_db_account = ICPSudo.get_param('master.graph.db.account'),
            master_graph_db_password = ICPSudo.get_param('master.graph.db.password'),
            slave_graph_db_url=ICPSudo.get_param('slave.graph.db.url'),
            slave_graph_db_account=ICPSudo.get_param('slave.graph.db.account'),
            slave_graph_db_password=ICPSudo.get_param('slave.graph.db.password')            
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('master.graph.db.url', self.master_graph_db_url)
        ICPSudo.set_param('master.graph.db.account', self.master_graph_db_account)
        ICPSudo.set_param('master.graph.db.password', self.master_graph_db_password)
        ICPSudo.set_param('slave.graph.db.url', self.slave_graph_db_url)
        ICPSudo.set_param('slave.graph.db.account', self.slave_graph_db_account)
        ICPSudo.set_param('slave.graph.db.password', self.slave_graph_db_password)

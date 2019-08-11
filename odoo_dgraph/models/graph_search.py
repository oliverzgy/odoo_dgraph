# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning, UserError, DeferredException

_logger = logging.getLogger(__name__)


class GraphSearch(models.Model):
    _name = 'graph.search'
    _inherit = 'graph.mixin'
    _description = 'Graph Search'

    @api.model
    def query(self, query, variables=None):
        """
        定义搜索引擎搜索方法，以供应用调用
        :param kwargs:
        :return:
        """
        res = self.graph_query(query, variables=variables)
        return res


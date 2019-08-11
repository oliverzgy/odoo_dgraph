# -*- coding: utf-8 -*-

import logging
import pydgraph
import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning, UserError, DeferredException

_logger = logging.getLogger(__name__)


class GraphMixin(models.AbstractModel):
    _name = 'graph.mixin'
    _description = 'Graph Mixin'

    @api.model
    def _get_graph_db_api_credential(self):
        res = {}
        ICPSudo = self.env['ir.config_parameter'].sudo()
        master_graph_db_url = ICPSudo.get_param('master.graph.db.url')
        master_graph_db_account = ICPSudo.get_param('master.graph.db.account')
        master_graph_db_password = ICPSudo.get_param('master.graph.db.password')

        slave_graph_db_url = ICPSudo.get_param('slave.graph.db.url')
        slave_graph_db_account = ICPSudo.get_param('slave.graph.db.account')
        slave_graph_db_password = ICPSudo.get_param('slave.graph.db.password')


        if not master_graph_db_url:
            raise ValidationError(_(u"Master Graph DB URL not provided!"))

        res.update(
            master_graph_db_url = master_graph_db_url,
            master_graph_db_account = master_graph_db_account or '',
            master_graph_db_password = master_graph_db_password or '',
            slave_graph_db_url = slave_graph_db_url or '',
            slave_graph_db_account = slave_graph_db_account or '',
            slave_graph_db_password = slave_graph_db_password or ''
        )

        return res

    @api.model
    def prepare_master_client_stub(self):
        credential = self._get_graph_db_api_credential()
        db_url = credential.get('master_graph_db_url')
        account = credential.get('master_graph_db_account')
        password = credential.get('master_graph_db_password')
        url = "%s".strip() % (db_url)
        _logger.info('client_stub url %s' % url)
        client_stub = pydgraph.DgraphClientStub(url)
        _logger.info(client_stub)
        return client_stub

    @api.model
    def prepare_slave_client_stub(self):
        credential = self._get_graph_db_api_credential()
        db_url = credential.get('slave_graph_db_url')
        account = credential.get('slave_graph_db_account')
        password = credential.get('slave_graph_db_password')
        url = "%s".strip() % (db_url)
        _logger.info('client_stub url %s' % url)
        client_stub = pydgraph.DgraphClientStub(url)
        _logger.info(client_stub)
        return client_stub

    @api.model
    def _graph_db_connection(self, client_stub):
        client = pydgraph.DgraphClient(client_stub)
        # _logger.info(client)
        return client

    @api.model
    def db_alter(self, client_stub, op):
        """
        https://github.com/dgraph-io/pydgraph#alter-the-database
        :param op:
        :return:
        """
        if not (isinstance(op, pydgraph.Operation) and isinstance(client_stub, pydgraph.DgraphClientStub)):
            raise ValidationError('Please check if the arguments are pydgraph.Operation or pydgraph.DgraphClientStub ...')
        client = self._graph_db_connection(client_stub)
        _logger.info(client)
        action = client.alter(op)
        return action

    @api.model
    def db_mute(self, client_stub, mu):
        """
        https://github.com/dgraph-io/pydgraph#run-a-mutation
        :param op:
        :return:
        """
        if not isinstance(mu, pydgraph.Mutation):
            raise ValidationError('Please check if the arguments are pydgraph.Mutation...')
        client = self._graph_db_connection(client_stub)
        txn = client.txn()
        try:
            action = txn.mutate(mu=mu)
            txn.commit()
            return action
        finally:
            txn.discard()

    @api.model
    def db_txn(self, client_stub):
        """
        https://github.com/dgraph-io/pydgraph#run-a-mutation
        :param op:
        :return:
        """
        client = self._graph_db_connection(client_stub)
        txn = client.txn()
        return txn

    @api.model
    def db_query(self, client_stub, query, variables=None):
        """
        https://github.com/dgraph-io/pydgraph#run-a-query
        :param query:
        :param variables:
        :return:
        """
        if not isinstance(query, str):
            raise ValidationError('Please check if the arguments are String...')

        txn = self.db_txn(client_stub)
        # client_stub = pydgraph.DgraphClientStub('192.168.1.44:9080')
        # client = pydgraph.DgraphClient(client_stub)
        # txn = client.txn()
        try:
            res = txn.query(query, variables=variables)
            res = json.loads(res.json)
            return res
        finally:
            txn.discard()

    @api.model
    def graph_query(self, query, variables=None):
        """
        https://github.com/dgraph-io/pydgraph#run-a-query
        :param query:
        :param variables:
        :return:
        """
        if not isinstance(query, str):
            raise ValidationError('Please check if the arguments are String...')

        client_stub = self.prepare_master_client_stub()

        txn = self.db_txn(client_stub)

        try:
            res = txn.query(query, variables=variables)
            res = json.loads(res.json)
            return res
        finally:
            txn.discard()

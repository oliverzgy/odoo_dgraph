# -*- coding: utf-8 -*-

import logging
import pydgraph
import json
import rfc3339

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning, UserError, DeferredException

_logger = logging.getLogger(__name__)


class GraphIndex(models.Model):
    _name = 'graph.index'
    _inherit = 'graph.mixin'
    _description = 'Graph Index'

    name = fields.Char('Name', readonly=True, compute='_compute_name', compute_sudo=True, store=True)
    type = fields.Selection([('master', 'Master'), ('slave', 'Slave')], string='Type')
    state = fields.Selection([('normal', 'Normal'),('abnormal','Abnormal')], string='Satus', required=True, default='normal')
    note = fields.Text('Note')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', _('Index must be unique!'))
    ]

    @api.multi
    def action_add_graph_db_data(self):
        """

        :return:
        """
        self.ensure_one()
        self._action_add_graph_db_data()

    @api.multi
    def _action_add_graph_db_data(self):
        """
        分批取数据处理（降低一次取数据对系统造成的压力），然后同步到图数据库 #todo: 考虑异步处理方式或者辅助线程处理
        :return:
        """
        self.ensure_one()
        model_list = self._get_model_list()

        if self.type == 'master':
            client_stub = self.prepare_master_client_stub()
        else:
            client_stub = self.prepare_slave_client_stub()

        _logger.info(client_stub)

        for model in model_list:
            _logger.info('开始处理 %s 模型数据！' % model)
            model_fields = self._get_model_fields(model)
            records_count = self._get_model_records_count(model)
            _logger.info('开始处理 %s 模型 %s 条数据！' % (model, records_count))

            if records_count:
                count = records_count
                limit = 100
                turns = count // limit

                for turn in range(0, turns + 1):
                    offset = limit * turn
                    start_position = limit * turn
                    end_position = (start_position + limit) if (count - start_position) > limit else count
                    val1 = {}
                    set_list = []

                    records = self._get_model_records(model, limit=limit, offset=offset)
                    for rec in records:
                        val = self._construct_graph_mute_val(model, rec, model_fields, client_stub)
                        set_list.append(val)
                        # print(333333, val)

                    val1['set'] = set_list
                    txn = self.db_txn(client_stub)
                    try:
                        action = txn.mutate(set_obj=val1)
                        # print(action)
                        txn.commit()
                        logs1 = _('模型更新进度：%s - 已经处理 %s / %s 条记录！\n') % (model, end_position, count)
                        _logger.info(logs1)
                    finally:
                        txn.discard()
        client_stub.close()
        return True

    @api.one
    def action_update_graph_db_data(self):
        """

        :return:
        """
        self.ensure_one()
        self._action_add_graph_db_data()


    @api.model
    def _get_model_list(self):
        model_obj = self.env['ir.model'].sudo()
        model_ids = model_obj.search([
            ('model','not in', ['mail.thread', 'account.generic.tax.report', 'ir.attachment', 'account.report', 'address.mixin', 'ir.module']),
            ('transient','=',False),
            ('model','not ilike','ir.')
        ])
        model_list = model_ids.mapped('model')
        # print(222222, model_list)
        return model_list

    @api.model
    def _get_model_records(self, model, limit=None, offset=None):
        model_obj = self.env[model].sudo()
        # if model_obj._abstract or  model_obj._auto:
        if model_obj._abstract:
            return False
        record_ids = model_obj.search_read([])
        return record_ids

    @api.model
    def _get_model_records_count(self, model):
        """
        获取模型记录数，product.product和product.template模型记录取数用search_count方法很慢(原因待查),改用sql直接取数！
        :param model:
        :return:
        """
        model_obj = self.env[model].sudo()

        if model_obj._abstract:
            return False

        if model in ['product.product','product.template']:
            query_str = 'SELECT count(1) FROM %s' % model.replace('.','_')
            self._cr.execute(query_str)
            res = self._cr.fetchone()
            count = res[0]
        else:
            count = model_obj.search_count([])
        return count

    @api.model
    def _get_model_fields(self, model):
        model_obj = self.env[model].sudo()
        fields = model_obj.fields_get()
        # print(fields)
        return fields

    @api.model
    def _construct_graph_mute_val(self, model, record, model_fields, client_stub):
        """
        构造图数据库更新数据，https://docs.dgraph.io/query-language/
        :param model:
        :param record:
        :param fields:
        :return:
        """
        val = {}
        val['id-integer'] = '%s-%s' % (model, record.get('id'))
        val['xid'] = '%s-%s' % (model, record.get('id'))
        val['uid'] = '_:%s-%s' % (model, record.get('id'))
        val[model] = '%s' % model

        query = """query uid($a: string) {
                all(func: eq(xid, $a)) {
                    uid
                }
            }"""
        variables = {'$a': '%s-%s' % (model, record.get('id'))}
        # client_stub = self.prepare_client_stub()
        res = self.db_query(client_stub, query,variables)
        # print('before upsert: %s' % res)
        if res and res.get('all'):
            val['uid'] = res['all'][0]['uid']

        for k, v in model_fields.items():
            # print(k, v.get('type'), v.get('relation'))

            if v.get('type') in ['char','integer','float','monetary']:
                if record.get(k):
                    j = '%s-%s' % (k, v.get('type'))
                    val[j] = record[k]
            elif v.get('type') in ['date','datetime']:
                if record.get(k):
                    j = '%s-%s' % (k, v.get('type'))
                    d = fields.Datetime.from_string(record[k])
                    d = rfc3339.rfc3339(d)
                    val[j] = d
            elif v.get('type') in ['boolean']:
                j = '%s-%s' % (k, v.get('type'))
                val[j] = record[k]
            elif v.get('type') in ['many2one']:
                if record.get(k):
                    j = '%s-%s' % (k, v.get('type'))
                    val[j] = {
                        'id-integer': '%s-%s' % (v.get('relation'), record[k][0]),
                        'xid': '%s-%s' % (v.get('relation'), record[k][0]),
                        'uid': '_:%s-%s' % (v.get('relation'), record[k][0]),
                        'name-char': record[k][1]
                    }

                    query = """query uid($a: string) {
                                    all(func: eq(xid, $a)) {
                                        uid
                                    }
                                }"""
                    variables = {'$a': '%s-%s' % (v.get('relation'), record[k][0])}
                    res = self.db_query(client_stub, query, variables)
                    # print('before many2one upsert: %s' % res)
                    if res and res.get('all'):
                        val[j]['uid'] = res['all'][0]['uid']

            elif v.get('type') in ['many2many','one2many']:
                if record.get(k):
                    j = '%s-%s' % (k, v.get('type'))
                    val[j] = []
                    for x in record[k]:
                        d = {
                            'id-integer': '%s-%s' % (v.get('relation'), x),
                            'xid': '%s-%s' % (v.get('relation'), x),
                            'uid': '_:%s-%s' % (v.get('relation'), x)
                        }

                        query = """query uid($a: string) {
                                                            all(func: eq(xid, $a)) {
                                                                uid
                                                            }
                                                        }"""
                        variables = {'$a': '%s-%s' % (v.get('relation'), x)}
                        res = self.db_query(client_stub, query, variables)
                        # print('before one2many many2many upsert: %s' % res)
                        if res and res.get('all'):
                            d['uid'] = res['all'][0]['uid']

            else:
                pass

        return val

    @api.multi
    def action_set_graph_db_schema(self):
        """
        异步调用
        :return:
        """
        self.ensure_one()
        self._action_set_graph_db_schema()


    @api.multi
    def _action_set_graph_db_schema(self):
        """
        关系型数据库的字段相当于图数据库的scala和uid predicates
        :return:
        """
        self.ensure_one()
        all_fields = self._get_local_fields()
        all_models = self._get_local_models()
        schema = self._process_local_fields(all_fields, all_models)
        op = pydgraph.Operation(schema=schema)

        if self.type == 'master':
            client_stub = self.prepare_master_client_stub()
        else:
            client_stub = self.prepare_slave_client_stub()

        _logger.info(client_stub)

        res = self.db_alter(client_stub, op)
        client_stub.close()
        return res

    @api.one
    def action_drop_graph_db_schema(self):
        """
        清除图库所有schema
        :return:
        """
        op = pydgraph.Operation(drop_all=True)

        if self.type == 'master':
            client_stub = self.prepare_master_client_stub()
        else:
            client_stub = self.prepare_slave_client_stub()

        _logger.info(client_stub)

        res = self.db_alter(client_stub, op)
        client_stub.close()
        return res

    def _get_local_fields(self):
        fields_obj = self.env['ir.model.fields'].sudo()
        all_fields = fields_obj.search([])
        return all_fields

    def _get_local_models(self):
        fields_obj = self.env['ir.model'].sudo()
        all_models = fields_obj.search([])
        return all_models

    def _process_local_fields(self, all_fields, all_models):
        """
        生成图数据库schema/predicates创建语句
        :param all_fields:
        :param all_models:
        :return: 返回数据list
        """
        predicates_fields = all_fields.mapped(lambda r: {'name': "%s-%s" % (r.name, r.ttype), 'tname':"%s" % r.name , 'ttype':"%s" % r.ttype})
        predicates_models = all_models.mapped(lambda r: {'name': "%s" % r.model})

        new_list = []
        schema = ''
        schema += 'xid: string @index(exact) .\n'
        for item in predicates_fields:
            if item not in new_list:
                new_list.append(item)
            # print(len(predicates_fields), item)
        for item in new_list:
            # print(len(new_list), item)
            if item.get('ttype') == 'char' and item.get('tname') == 'name':
                schema += '%s: string @index(exact,fulltext,term,hash,trigram) @count @upsert . \n' % (item.get('name'))
            elif item.get('ttype') == 'char':
                schema += '%s: string @index(fulltext) @upsert . \n' % (item.get('name'))
            elif item.get('ttype') == 'integer' and item.get('tname') == 'id':
                schema += '%s: string @index(exact) @upsert . \n' % (item.get('name'))
            elif item.get('ttype') == 'integer':
                schema += '%s: int @index(int) @upsert . \n' % (item.get('name'))
            elif item.get('ttype') in ['float','monetary']:
                schema += '%s: float @index(float) @upsert . \n' % (item.get('name'))
            elif item.get('ttype') in ['date','datetime']:
                schema += '%s: datetime @index(day) @upsert . \n' % (item.get('name'))
            elif item.get('ttype') in ['many2one','one2many']:
                schema += '%s: uid @count . \n' % (item.get('name'))
            elif item.get('ttype') in ['many2many']:
                schema += '%s: uid @count . \n' % (item.get('name')) # 去掉 reverse, 是否revser由数据模型控制
            elif item.get('ttype') in ['boolean']:
                schema += '%s: bool @index(bool) @upsert . \n' % (item.get('name'))
            else:
                pass

        for item in predicates_models:
            schema += '%s: string @index(exact) @count @upsert . \n' % (item.get('name'))

        # print(schema)
        return schema

    @api.depends('type')
    def _compute_name(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        database_uuid = ICPSudo.get_param('database.uuid')
        suffix = "%s" % (database_uuid[0:8])
        for rec in self:
            if rec.type:
                val = {
                    'name': "%s-graph-db-engine-%s" % (rec.type, suffix)
                }
                rec.update(val)
        return True

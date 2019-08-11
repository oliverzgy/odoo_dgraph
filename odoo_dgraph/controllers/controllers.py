# -*- coding: utf-8 -*-
from odoo import http

# class BaseGraph(http.Controller):
#     @http.route('/base_graph/base_graph/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_graph/base_graph/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_graph.listing', {
#             'root': '/base_graph/base_graph',
#             'objects': http.request.env['base_graph.base_graph'].search([]),
#         })

#     @http.route('/base_graph/base_graph/objects/<model("base_graph.base_graph"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_graph.object', {
#             'object': obj
#         })
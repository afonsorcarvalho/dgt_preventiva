# -*- coding: utf-8 -*-
from odoo import http

class DgtPreventiva(http.Controller):
     @http.route('/dgt_preventiva/dgt_preventiva/', auth='public')
     def index(self, **kw):
         return "Hello, world"

     @http.route('/dgt_preventiva/dgt_preventiva/objects/', auth='public')
     def list(self, **kw):
         return http.request.render('dgt_preventiva.listing', {
             'root': '/dgt_preventiva/dgt_preventiva',
             'objects': http.request.env['dgt_preventiva.dgt_preventiva'].search([]),
         })

     @http.route('/dgt_preventiva/dgt_preventiva/objects/<model("dgt_preventiva.dgt_preventiva"):obj>/', auth='public')
     def object(self, obj, **kw):
         return http.request.render('dgt_preventiva.object', {
             'object': obj
         })
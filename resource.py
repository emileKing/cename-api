from datetime import datetime
from flask import request

from flask_restful import Resource, reqparse
# from flask_restful.utils import cors

from app import start_app as get_app
from models import Invoice, Batch, Region, Distribution
import json

_, t_db = get_app()

class BaseResource(Resource):
    """
    Abstraction of major functionalities and methods for resources.
    """

    def __init__(self):
        self.arg_parser = reqparse.RequestParser()
        self.arguments_list = [] # abstract a list of arguments pasrsing

    def add_argument(self, arg):
        """Add an argument to the parser"""
        self.arg_parser.add_argument(arg['name'], arg['type'], help=arg['help'])

    def init_args(self):
        """Initialize the arguments for parsing"""
        if len(self.arguments_list) == 0:
            return 
        for arg in self.arguments_list:
            self.add_argument(arg)
    
    def parse_args(self):
        """Parse the request arguments"""
        return self.arg_parser.parse_args()

    def parse_query(self, query_res):
        parsed_response = []
        if len(query_res) > 0:
            for data in query_res:
                parsed_response.append(data.jsonify())
        return parsed_response
        
    @staticmethod
    def convert_to_date(s):
        return datetime.strptime(s, "%m/%d/%y")
    


class Get_invoice(BaseResource):
    def __init__(self):
        super().__init__()
        self.arguments_list = []

    def get(self, invoice_no=None):
        if invoice_no:
            # if the request is for a particular row
            inv = Invoice.query.get(invoice_no) 
            if inv:
                query = [inv] 
                bat = inv.batches
                response = {"invoice": self.parse_query(query)[0],
                            "batches": self.parse_query(bat)}
            else:
                query = [] # should be a list
                response = {}
        else:
            # else get all the tables
            query = Invoice.query.all()
            response = self.parse_query(query)

        return response

class Add_invoice(BaseResource):
    def __init__(self):
        super().__init__()

    def missing_args(self):
        if request.data == "":
            return True
        return False
    
    def post(self):
        if self.missing_args():
            return {'message': "Sorry but 'data' argument value is missing!"}, 500
        else:
            json_data = self.convert_data_to_dict(request.data)
            invoice_data = json_data['invoice_data']
            batches_data = json_data['batches']

            if len(batches_data) > 0:
                if not self.row_exist(Invoice, invoice_data['invoice_no']):
                    invoice_no = self.add_invoice(invoice_data)
                    for batch in batches_data:
                        if not self.row_exist(Batch, batch['batch_no']):
                            self.add_batch(batch, invoice_no)
                        else:
                            return {'message': "Cannot add batch. Duplicate 'batch_no' '%s'"%(batch['batch_no'])}, 500
                    return {'message': "Invoice and batche(s) added successfully!"}, 200
                else:
                    return {'message': "Cannot add Invoice. Duplicate 'invoice_no' '%s'"%(invoice_data['invoice_no'])}, 500
            else:
                return {'message': "No batch data recieved. Cannot add invoice"}, 500

    @staticmethod
    def convert_data_to_dict(raw_json):
        """Convert the data argument value into a python dictionary"""
        return json.loads(raw_json)

    def add_invoice(self, invoice_dict):
        invoice_dict['invoice_date'] = self.convert_to_date(invoice_dict['invoice_date'])
        inv = Invoice(**invoice_dict)
        t_db.session.add(inv)
        t_db.session.commit()
        return inv.invoice_no
        return invoice_dict['invoice_no']

    def add_batch(self, batch_dic, invoice_no):
        batch_dic['exp_date'] = self.convert_to_date(batch_dic['exp_date'])
        batch_dic['mfg_date'] = self.convert_to_date(batch_dic['mfg_date'])
        batch_dic['invoice_no'] = invoice_no

        t_db.session.add(Batch(**batch_dic))
        t_db.session.commit()

    def row_exist(self, model, pk):
        if model.query.get(pk):
            return True
        return False

class Get_batches(BaseResource):
    def __init__(self):
        super().__init__()
        self.arguments_list = []
        self.init_args()
        self.args = self.parse_args()

    def get(self, batch_no=None):
        if batch_no:
            # if the request is for a particular row
            temp = Batch.query.get(batch_no) 
            if temp:
                query = [temp] 
            else:
                query = [] # should be a list
        else:
            # else get all the tables
            query = Batch.query.all()
        return self.parse_query(query)

class Get_regions(BaseResource):
    def __init__(self):
        super().__init__()
        self.arguments_list = []
        self.init_args()
        self.args = self.parse_args()

    def get(self):
        query = Region.query.all()
        return self.parse_query(query)

class Update_invoice(BaseResource):
    def __init__(self):
        super().__init__()
        self.arguments_list = []
        self.init_args()
        self.args = self.parse_args()

    def put(self):
        data = request.data
        if data != "":
            json_data = json.loads(data)
            invoice_no = json_data['invoice_no']
            
            inv = Invoice.query.get(invoice_no)
            if inv:
                for k in json_data.keys():
                    try:
                        if k != "invoice_no":
                            if k.endswith("date"):
                                json_data[k] = self.convert_to_date(json_data[k])
                            setattr(inv, k, json_data[k])
                    except:
                        return {"messsage": "Error while updating"}, 500
                t_db.session.commit()
                return {"message": "invoice updated successfully"}, 200
            else:
                return {"message": "no such invoice"}, 500
                
        else:
            return {"message": "no invoice data recieved"}, 500

class Update_batch(BaseResource):
    def __init__(self):
        super().__init__()
        self.arguments_list = []
        self.init_args()
        self.args = self.parse_args()

    def put(self):
        data = request.data
        if data != "":
            json_data = json.loads(data)
            batch_no = json_data['batch_no']
            
            _batch = Batch.query.get(batch_no)
            if _batch:
                for k in json_data.keys():
                    try:
                        if k != "batch_no":
                            if k.endswith("date"):
                                json_data[k] = self.convert_to_date(json_data[k])
                            setattr(_batch, k, json_data[k])
                    except Exception as e:
                        print(e)
                        return {"messsage": "Error while updating"}, 500
                t_db.session.commit()
                return {"message": "batch updated successfully"}, 200
            else:
                return {"message": "no such batch"}, 500
                
        else:
            return {"message": "no batch data recieved"}, 500
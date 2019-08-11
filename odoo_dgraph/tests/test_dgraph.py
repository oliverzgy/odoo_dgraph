import pydgraph
import datetime

d = datetime.datetime(1980, 1, 1, 23, 0, 0, 0).isoformat()
print(type(d), d)

client_stub = pydgraph.DgraphClientStub('192.168.1.44:9080')
client = pydgraph.DgraphClient(client_stub)
print(client)
op = pydgraph.Operation(drop_all=True)
action = client.alter(op)
print(action)

# p = {
#         "set": [
#             {
#                 "uid": "_:company1",
#                 "industry": "Machinery",
#                 "name": "CompanyABC"
#             },
#             {
#                 "uid": "_:company2",
#                 "industry": "High Tech",
#                 "name": "The other company"
#             },
#             {
#                 "uid": "_:jack",
#                 "works_for": { "uid": "_:company1"},
#                 "name": "Jack"
#             },
#             {
#                 "uid": "_:ivy",
#                 "works_for": { "uid": "_:company1"},
#                 "boss_of": { "uid": "_:jack"},
#                 "name": "Ivy"
#             },
#             {
#                 "uid": "_:zoe",
#                 "works_for": { "uid": "_:company1"},
#                 "name": "Zoe"
#             },
#             {
#                 "uid": "_:jose",
#                 "works_for": { "uid": "_:company2"},
#                 "name": "Jose"
#             },
#             {
#                 "uid": "_:alexei",
#                 "works_for": { "uid": "_:company2"},
#                 "boss_of": { "uid": "_:jose"},
#                 "name": "Alexei"
#             }
#         ]
#     }
#
# txn = client.txn()
# assigned = txn.mutate(set_obj=p)
# print(assigned)
# txn.commit()





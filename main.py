import os, os.path
import random
import string
import pandas
import json
import requests

import cherrypy

# Global config entries apply on the entire project
cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 8080,})


def graphQuery(query):
  graph_url = 'NEO4J DatabaseURL'
  payload = {"statements": [{"statement": query}]}
  headers = {'content-type': 'application/json'}
  r = requests.post(graph_url, data=json.dumps(payload), headers=headers)
  return r.json()


#Test euqries
"""
testColumns = graphQuery("MATCH (n:Business) return n.id, n.name, n.city limit 20")["results"][0]["columns"]
print(testColumns)
testRowsRaw = graphQuery("MATCH (n:Business) return n.id, n.name, n.city limit 20")["results"][0]["data"]

testRows = []
for row in testRowsRaw:
  testRows.append(row["row"])
print(testRows)
print(pandas.DataFrame.from_records(testRows, columns=testRows).to_html())
"""

#Function with query request to extract the properties for 
def graphProperties(label):
  graph_url = 'NEO4J DatabaseURL'
  payload = {
    "statements": [
        {
            "statement": "CALL apoc.meta.schema() YIELD value"
        }
    ]}
  headers = {'content-type': 'application/json'}
  r = requests.post(graph_url, data=json.dumps(payload), headers=headers).json()
  properties = [k  for  k in  r["results"][0]["data"][0]["row"][0][str(label)]["properties"].keys()] 
  return properties

#test = graphProperties(label = "Category")
#print(test)


def startNodeListToHTML():
  nodelist = [d["row"] for d in graphQuery("CALL apoc.schema.nodes() yield label")["results"][0]["data"]]
  list_html = "" 
  for label in nodelist:
    #give aprropriate id for easy access the list item later via  html DOM/Java Script on client side
    list_html += '<li id="list-node-' + str(label[0]) +'">' + label[0] + "</li> \n"
  return list_html

mynode = startNodeListToHTML()
print(mynode)

class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return open('index.html')

@cherrypy.expose
class StringGeneratorWebService(object):

    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        return cherrypy.session['mystring']

    def POST(self, function, node):
        if function == "startnode":
          list_of_nodes = startNodeListToHTML()
          return list_of_nodes
        if function == "firstnodes":
          #query properties to use in dataframe as column names
          nodeProperties = graphProperties(node)
          #transform properties to string to use later in query
          testColumns = ", ".join(["n."+k for k in nodeProperties])
          testRowsRaw = graphQuery("MATCH (n:"+node+") return " + testColumns + " limit 50")["results"][0]["data"]
          testRows = [testRowsRaw["row"] for testRowsRaw in testRowsRaw]
          mypandas = pandas.DataFrame.from_records(testRows, columns=nodeProperties)
          mypandas.index += 1
          mypandasHtml = mypandas.to_html(classes="table table-hover table-dark")
          return mypandasHtml

    def PUT(self, another_string):
        cherrypy.session['mystring'] = another_string

    def DELETE(self):
        cherrypy.session.pop('mystring', None)

if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/data': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    
webapp = StringGenerator()
webapp.data = StringGeneratorWebService()
cherrypy.quickstart(webapp, '/', conf)

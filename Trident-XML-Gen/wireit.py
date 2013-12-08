#!/usr/bin/env python


import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import os.path
import os
import uuid
import json
import xml.etree.cElementTree as ET
from lxml import etree

from tornado import gen
from tornado.options import define, options, parse_command_line


define("port", default=8088, help="run on the given port", type=int)

#define namespaces
xmlns = "http://www.springframework.org/schema/beans"
p = "http://www.springframework.org/schema/p"
c = "http://www.springframework.org/schema/c"
xsi =  "http://www.w3.org/2001/XMLSchema-instance"
util = "http://www.springframework.org/schema/util"
schemaLocation = "http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-2.5.xsd http://www.springframework.org/schema/util http://www.springframework.org/schema/util/spring-util-2.5.xsd"
#TODO - FINALIZE AND SET THE NAME
Topology_submission_class = "com.kaseya.trident.SingleTopologySubmission"
#TODO - define the spout/stream.  this stream will be fixed. The only variable should be the topic/partition. 
inputStream_id = "inputStream"
xml_file_name = "trident.xml"
dsl_file_extension = ".dsl"
#TODO - assumption here is its a DAG of 1 dimension

each_class = "com.kaseya.trident.operations.EachOperation"
groupby_class = "com.kaseya.trident.operations.GroupByOperation"
aggregate_class = "com.kaseya.trident.operations.AggregateOperation"

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("workflow/index.html")


class XMLHandler(tornado.web.RequestHandler):
    def get(self):

        self.write("Method Not Supported")

    def post(self):
        topology_data = self.get_argument("json_data", None)
        topology_name = self.get_argument("name", None)
        data = json.loads(topology_data)
        #### Start XML generation #######
        #Construct the header
        beans = etree.Element("{"+xmlns+"}beans", attrib={"{" + xsi + "}schemaLocation" : schemaLocation }, nsmap={"xsi":xsi, "p": p,"c" : c, "util" : util , None:xmlns})      
        ##Trident Config
        bean_config = etree.SubElement(beans, "bean", attrib={"id":"config", "class":"storm.trident.TridentTopology"})
        ##Topology
        bean_topology = etree.SubElement(beans, "bean", attrib={"id":"topology", "class":"backtype.storm.Config", "{" + p + "}debug":"true"})
        #Topology submissing bean
        bean_topology_submission = etree.SubElement(beans, "bean", attrib={"id":topology_name, "class":Topology_submission_class, "{" + c + "}topology-ref":"topology",  "{" + c + "}config-ref":"config", "{" + c + "}topologyId":"topology", "{" + p + "}streams-ref":"streams" })
        
        #Define spout - this stream will be fixed. The only variable should be the topic/partition. 
        #TODO - For this to work there should be only one input stream ???
        bean_spout = etree.SubElement(beans, "bean", attrib={"id":"stream1", "class":"com.kaseya.trident.StreamFactory", "{" + c + "}spout-ref":inputStream_id, "{" + p + "}spoutNodeName":"spout1", "{" + c + "}topology-ref":"topology", "{" + p + "}operations-ref":"operations1"})

        #Define util_lists
        util_stream = etree.SubElement(beans, "{" + util + "}list", attrib={"id":"streams"})       
        util_stream_ref = etree.SubElement(util_stream, "ref", attrib={"bean":"stream1"}) 

        stream_index = 0
        index = 0 

        for module in data["modules"]:
            if module["name"] == "Stream":
                stream_index = index
            index=index+1
        wire_graph = {}
        for wire in data["wires"]:
            wire_graph[wire["src"]["moduleId"]] = wire["tgt"]["moduleId"]

        # build operations list
        util_operations= etree.SubElement(beans, "{" + util + "}list", attrib={"id":"operations1"})    
        modules = data["modules"]
        op = wire_graph[stream_index]
        index = 0 
        dsl_files = {}
        while True: 
            index=index+1
            #build the operations beans
            if modules[op]["name"] == "Each":
                util_operations_bean  = etree.SubElement(util_operations, "bean", attrib={"class": each_class})
                dsl_files["each_" + modules[op]["value"]["name"] + dsl_file_extension] = modules[op]["value"]["code"] 
            elif modules[op]["name"] == "GroupBy":
                util_operations_bean  = etree.SubElement(util_operations, "bean", attrib={"class": groupby_class})
            elif modules[op]["name"] == "Aggregate":
                util_operations_bean  = etree.SubElement(util_operations, "bean", attrib={"class": aggregate_class})
                dsl_files["aggregate_" + modules[op]["value"]["name"] + dsl_file_extension] = modules[op]["value"]["code"] 
            if op in wire_graph:
                op = wire_graph[op]
            else:
                break 
            #TODO - add argument beans to above operations. 
        xml_gen = etree.tostring(beans, xml_declaration=True, encoding="UTF-8", pretty_print=True)

        dir = os.path.join(os.path.dirname(__file__), "ouput")
        try:
            os.makedirs(dir)
        except OSError as exception:
            print "the folder already exists"
        for x in dsl_files: 
            f = open(os.path.join(dir, x), 'wb')
            f.write(dsl_files[x]) 
        f = open(os.path.join(dir, xml_file_name), 'wb')
        f.write(xml_gen) 
        f.close() 
        self.write(xml_gen)



def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/xml/generate", XMLHandler),
        ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "templates/static"),
        xsrf_cookies=False,

        )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

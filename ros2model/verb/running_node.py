from pathlib import Path
import sys
from typing import List
from ros2cli.node.strategy import NodeStrategy
from ros2cli.node.strategy import add_arguments
from ros2cli.node.direct import DirectNode
from ros2node.api import TopicInfo
from ros2node.api import get_absolute_node_name
from ros2node.api import get_action_client_info
from ros2node.api import get_action_server_info
from ros2node.api import get_node_names
from ros2node.api import get_publisher_info
from ros2node.api import get_service_client_info
from ros2node.api import get_service_server_info
from ros2node.api import get_subscriber_info
from ros2node.api import INFO_NONUNIQUE_WARNING_TEMPLATE
from ros2node.api import NodeNameCompleter
from ros2param.api import call_list_parameters
from ros2param.api import call_describe_parameters
from ros2model.api import fix_topic_types
from ros2model.api import fix_topic_names
from ros2model.verb import VerbExtension
from ros2model.api import get_parameter_type_string
from ament_index_python import get_package_share_directory
from jinja2 import Environment, FileSystemLoader




class RunningNodeVerb(VerbExtension):
    """Dump information about a running node into a model."""

    def add_arguments(self, parser, cli_name):
        add_arguments(parser)
        argument = parser.add_argument(
            'node_name',
            help='Node name to request information')
        argument.completer = NodeNameCompleter()
        parser.add_argument(
            '--include-hidden', action='store_true',
            help='Display hidden topics, services, and actions as well')
        parser.add_argument(
            "-o", 
            "--output", 
            default=".", 
            required=True, 
            help="The output file for the generated model.")

    def main(self, *, args):
        subscribers : List[TopicInfo] = []
        publishers : List[TopicInfo] = []
        service_clients : List[TopicInfo] = []
        service_servers : List[TopicInfo] = []
        actions_clients : List[TopicInfo] = []
        actions_servers : List[TopicInfo] = []
        parameters : List[TopicInfo] = []
        with NodeStrategy(args) as node:
            node_name =  get_absolute_node_name(args.node_name)
            node_names = get_node_names(node=node, include_hidden_nodes=args.include_hidden)
            count = [n.full_name for n in node_names].count(node_name)
            if count > 1:
                print(
                    INFO_NONUNIQUE_WARNING_TEMPLATE.format(
                        num_nodes=count, node_name=args.node_name),
                    file=sys.stderr)
            if count > 0:
                print(args.node_name)
                subscribers = get_subscriber_info(
                    node=node, remote_node_name=args.node_name, include_hidden=args.include_hidden)
                fix_topic_types(node_name, subscribers)
                subscribers = fix_topic_names(node_name, subscribers)
                
                publishers = get_publisher_info(
                    node=node, remote_node_name=args.node_name, include_hidden=args.include_hidden)
                fix_topic_types(node_name, publishers)
                publishers = fix_topic_names(node_name, publishers)
                
                service_servers = get_service_server_info(
                    node=node, remote_node_name=args.node_name, include_hidden=args.include_hidden)
                fix_topic_types(node_name, service_servers)
                service_servers = fix_topic_names(node_name, service_servers)
                
                service_clients = get_service_client_info(
                    node=node, remote_node_name=args.node_name, include_hidden=args.include_hidden)
                fix_topic_types(node_name, service_clients)
                service_clients = fix_topic_names(node_name, service_clients)
                
                actions_servers = get_action_server_info(
                    node=node, remote_node_name=args.node_name, include_hidden=args.include_hidden)
                fix_topic_types(node_name, actions_servers)
                actions_servers = fix_topic_names(node_name, actions_servers)
                
                actions_clients = get_action_client_info(
                    node=node, remote_node_name=args.node_name, include_hidden=args.include_hidden)
                fix_topic_types(node_name, actions_clients)
                actions_clients = fix_topic_names(node_name, actions_clients)
            else:
                return "Unable to find node '" + args.node_name + "'"
            
        with DirectNode(args) as node:
            response = call_list_parameters(
                    node=node,
                    node_name=node_name)
            
            sorted_names = sorted(response)
            describe_resp = call_describe_parameters(
                        node=node, node_name=node_name,
                        parameter_names=sorted_names)
            for descriptor in describe_resp.descriptors:
                parameters.append(TopicInfo(descriptor.name, get_parameter_type_string(descriptor.type)))
            
        env = Environment(
            loader=FileSystemLoader(get_package_share_directory("ros2model") + "/templates"), autoescape=True)
        template = env.get_template("node_model.jinja")
        contents = template.render(node_name=args.node_name,
                                    subscribers=subscribers,
                                    publishers=publishers,
                                    service_clients=service_clients,
                                    service_servers=service_servers,
                                    actions_clients=actions_clients,
                                    actions_servers=actions_servers,
                                    parameters=parameters,
                                    has_subscribers=len(subscribers) > 0,
                                    has_publishers=len(publishers) > 0,
                                    has_service_clients=len(service_clients) > 0,
                                    has_service_servers=len(service_servers) > 0,
                                    has_actions_clients=len(actions_clients) > 0,
                                    has_actions_servers=len(actions_servers) > 0,
                                    has_parameters=len(parameters) > 0)
        print(contents)
        output_file = Path(args.output)
        print("Writing model to {}".format(output_file.absolute()))
        output_file.touch()
        output_file.write_text(contents)
            

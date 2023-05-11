
from pathlib import Path

from ament_index_python import get_package_share_directory
from jinja2 import Environment, FileSystemLoader
from ros2cli.node.strategy import add_arguments

from ros2model.api import process_action_dir, process_msg_dir, process_srv_dir
from ros2model.verb import VerbExtension


class InterfacePackageVerb(VerbExtension):
    """Output information about a node."""

    def add_arguments(self, parser, cli_name):
        add_arguments(parser)
        parser.add_argument(
            'interface_package_name',
            help='Name of the package containing the interface')

        parser.add_argument(
            "-o",
            "--output",
            default=".",
            required=True,
            help="The output file for the generated model.")

    def main(self, *, args):
        package_share_path = get_package_share_directory(
            args.interface_package_name)
        msg_path = Path(package_share_path) / "msg"
        srv_path = Path(package_share_path) / "srv"
        actions_path = Path(package_share_path) / "action"
        msgs = process_msg_dir(msg_path)
        srvs = process_srv_dir(srv_path)
        actions = process_action_dir(actions_path)
        print("Found {} messages, {} services and {} actions.".format(
            len(msgs), len(srvs), len(actions)))
        env = Environment(
            loader=FileSystemLoader(get_package_share_directory("ros2model") + "/templates"), autoescape=False)
        template = env.get_template("model.jinja")
        contents = template.render(
            package_name=args.interface_package_name, msgs=msgs, srvs=srvs, actions=actions)
        output_file = Path(args.output)
        print("Writing model to {}".format(output_file.absolute()))
        output_file.touch()
        output_file.write_bytes(contents.encode("utf-8"))
